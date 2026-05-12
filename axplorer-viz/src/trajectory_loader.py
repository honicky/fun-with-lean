"""Turn a real Axplorer trajectory log into the same data ``trajectory.py`` exposes.

``trajectory.py`` (V1) is hand-curated.  This module reads a JSONL log produced
by the patched Axplorer (``--log_trajectory``; see
``vendor/PATCH_NOTES.md``) and produces a dict with the *same* module-level
names the Manim scenes import -- so the scenes don't change.

What the log gives us directly:
  * per-epoch top-k pool (objects + scores) and ``model_samples_*``
  * the ``best_score_so_far`` series and ``wall_time_seconds``
  * (epoch 0 = initial random search only)

What the log can't give us (and we therefore synthesize, exactly as V1 did):
  * Act 1's step-by-step add/reject trace -- the log is per-epoch, not per-move.
    We re-derive a plausible trace that ends at the *real* epoch-0 best graph,
    using ``graph_utils`` so every reject genuinely closes a 4-cycle.
  * Act 3's centre graph per iteration -- the *scores* are real (the
    ``best_score_so_far`` series), but the scene needs the per-iteration graphs
    to be nested, so we show nested subsets of the *real* final graph filling in.
  * Act 2's vertex partition -- a greedy 2-colouring of the chosen sample
    (which is honest: if the real samples aren't near-bipartite, the colouring
    won't look bipartite, and that's a finding, not a bug).

Run ``python -m src.trajectory_loader logs/square_N15_run.jsonl`` for a summary.
"""

from __future__ import annotations

import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import networkx as nx  # noqa: E402

from decode import decode_object, num_edge_tokens  # noqa: E402
from graph_utils import count_edges, has_4_cycle  # noqa: E402

# These match V1's trajectory.py constants; the loader keeps the same surface.
N_VERTICES_DEFAULT = 15
FLYWHEEL_TAGLINE = "Axplorer: a few hours, one GPU, real run."


# ---------------------------------------------------------------------------
# small graph helpers (operate on edge lists)
# ---------------------------------------------------------------------------

def _norm(e):
    a, b = e
    return (a, b) if a <= b else (b, a)


def _graph(edges, n):
    g = nx.empty_graph(n)
    g.add_edges_from(edges)
    return g


def _score(edges, n):
    """Edge count if the graph is C_4-free, else -1 (matches Axplorer's scoring)."""
    g = _graph(edges, n)
    return -1 if has_4_cycle(g) else count_edges(g)


def _is_within(u, v, a_set):
    return (u in a_set) == (v in a_set)


# ---------------------------------------------------------------------------
# log parsing
# ---------------------------------------------------------------------------

def _read_jsonl(path):
    records = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    records.sort(key=lambda r: r.get("epoch", 0))
    return records


def _infer_n_vertices(records):
    """Number of vertices N.  Prefer the explicit ``n_vertices`` field the
    patched Axplorer writes; otherwise fall back to inferring it from the
    largest edge token seen (largest token == C(N,2)-1, which assumes the log
    actually uses high-numbered vertices -- true for non-trivial graphs)."""
    for rec in records:
        if rec.get("n_vertices"):
            return int(rec["n_vertices"])
    max_tok = -1
    for rec in records:
        for field in ("top_k_objects", "model_samples_raw", "model_samples_after_search"):
            for obj in rec.get(field, []):
                for t in obj:
                    max_tok = max(max_tok, int(t))
    if max_tok < 0:
        return N_VERTICES_DEFAULT
    # smallest n with C(n,2) > max_tok
    n = 2
    while num_edge_tokens(n) <= max_tok:
        n += 1
    return n


def _decode_objs(objs, n):
    return [decode_object(o, n) for o in objs]


# ---------------------------------------------------------------------------
# representative-graph selection
# ---------------------------------------------------------------------------

def _best_object(rec, n, *, prefer_field="top_k_objects"):
    """Highest-scoring valid object in a record, decoded to an edge list."""
    cands = []
    objs = rec.get(prefer_field) or rec.get("top_k_objects") or []
    scores = rec.get("top_k_scores")
    decoded = _decode_objs(objs, n)
    for i, edges in enumerate(decoded):
        s = scores[i] if (scores is not None and i < len(scores)) else _score(edges, n)
        cands.append((s, edges))
    if not cands:
        return []
    return max(cands, key=lambda t: (t[0], len(t[1])))[1]


def _graph_distance(a, b):
    """Symmetric-difference size of two edge sets -- "how different do these look"."""
    sa, sb = {_norm(e) for e in a}, {_norm(e) for e in b}
    return len(sa ^ sb)


def _pick_distinct_samples(records, n, reference_edges, k=2):
    """Pick ``k`` model samples (epoch >= 1, valid, decent score) that look most
    different from ``reference_edges`` (the naive plateau).  Prefer
    ``model_samples_raw``; fall back to ``model_samples_after_search``."""
    pool = []  # (score, distance, edges)
    for rec in records:
        if rec.get("epoch", 0) < 1:
            continue
        for field in ("model_samples_raw", "model_samples_after_search"):
            for edges in _decode_objs(rec.get(field, []), n):
                s = _score(edges, n)
                if s < 0 or not edges:
                    continue
                pool.append((s, _graph_distance(edges, reference_edges), edges))
        if len(pool) >= 200:
            break
    if not pool:
        return []
    # de-dup by edge set
    seen = set()
    uniq = []
    for s, d, edges in pool:
        key = frozenset(_norm(e) for e in edges)
        if key not in seen:
            seen.add(key)
            uniq.append((s, d, edges))
    # rank by (score desc, then distance-from-plateau desc)
    uniq.sort(key=lambda t: (t[0], t[1]), reverse=True)
    chosen = []
    for s, d, edges in uniq:
        if all(_graph_distance(edges, c) >= 4 for c in chosen):
            chosen.append(edges)
        if len(chosen) == k:
            break
    while len(chosen) < k and uniq:
        chosen.append(uniq[len(chosen) % len(uniq)][2])
    return chosen[:k]


def _greedy_2coloring(edges, n):
    """A greedy max-cut-ish 2-colouring: returns (part_a, part_b) vertex lists.
    Vertices are placed to put as many edges as possible across the partition --
    so a near-bipartite graph ends up cleanly split."""
    g = _graph(edges, n)
    color = {}
    # process vertices in descending degree; greedily choose the side that
    # disagrees with more already-coloured neighbours
    for v in sorted(g.nodes(), key=lambda x: -g.degree(x)):
        same0 = sum(1 for u in g.neighbors(v) if color.get(u) == 0)
        same1 = sum(1 for u in g.neighbors(v) if color.get(u) == 1)
        color[v] = 0 if same0 <= same1 else 1
    part_a = sorted(v for v in range(n) if color.get(v, 0) == 0)
    part_b = sorted(v for v in range(n) if color.get(v, 0) == 1)
    return part_a, part_b


def _cut_fraction(edges, a_set):
    if not edges:
        return 1.0
    return sum(1 for u, v in edges if not _is_within(u, v, a_set)) / len(edges)


# ---------------------------------------------------------------------------
# Act 1 synthesis (the log has no per-move trace)
# ---------------------------------------------------------------------------

def synthesize_act1_operations(plateau_edges, n, *, seed=0, n_rejects=16, n_trailing=4):
    """Build a plausible (add, reject) trace SEED -> plateau, using graph_utils
    so every "reject" genuinely closes a 4-cycle against the graph so far.

    Mirrors the V1 generator: ``plateau_edges`` get added in a shuffled order
    (always C_4-free since the final graph is), interleaved with rejects of
    edges that *would* close a 4-cycle, plus a tail of rejects ("stuck")."""
    rng = random.Random(seed)
    plateau = [_norm(e) for e in plateau_edges]
    plateau_set = set(plateau)
    all_pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]

    def makes_c4(present, e):
        g = _graph(list(present) + [e], n)
        return has_4_cycle(g)

    order = plateau[:]
    rng.shuffle(order)
    present = []
    ops = []
    used = set()
    for e in order:
        if len(present) >= 4 and len(used) < n_rejects and rng.random() < 0.65:
            cands = [p for p in all_pairs if p not in plateau_set and p not in used]
            rng.shuffle(cands)
            for c in cands:
                if makes_c4(present, c):
                    ops.append(("reject", c))
                    used.add(c)
                    break
        ops.append(("add", e))
        present.append(e)
    # tail: a few more failed attempts -> stuck
    cands = [p for p in all_pairs if p not in plateau_set and p not in used]
    rng.shuffle(cands)
    tail = 0
    for c in cands:
        if tail >= n_trailing:
            break
        if makes_c4(plateau, c):
            ops.append(("reject", c))
            used.add(c)
            tail += 1
    return ops


# ---------------------------------------------------------------------------
# Act 3 nested-subset filler (real scores, graphs build up toward the real FINAL)
# ---------------------------------------------------------------------------

def _nested_chain_to_final(final_edges, target_sizes, n):
    """Return one edge-list per target size, each a subset of the next, ending at
    ``final_edges``.  We drop edges from ``final_edges`` (preferring to keep a
    spanning structure) to hit the smaller sizes -- so the centre graph in Act 3
    visibly fills in toward the real final graph."""
    final = [_norm(e) for e in final_edges]
    # order edges so the ones we keep longest form a connected backbone:
    # BFS/DFS spanning-tree edges first, then the rest.
    g = _graph(final, n)
    backbone = set()
    for comp in nx.connected_components(g):
        sub = g.subgraph(comp)
        for u, v in nx.bfs_edges(sub, next(iter(comp))):
            backbone.add(_norm((u, v)))
    rest = [e for e in final if e not in backbone]
    ordered = list(backbone) + rest  # keep backbone, drop from `rest` first
    chain = []
    for size in target_sizes:
        size = max(0, min(size, len(final)))
        # keep the first `size` of `ordered` (backbone preferred)
        keep = ordered[:size]
        chain.append(sorted(keep))
    # ensure nesting (target_sizes should be non-decreasing; clamp if not)
    for i in range(1, len(chain)):
        if not set(map(tuple, chain[i - 1])) <= set(map(tuple, chain[i])):
            chain[i] = sorted(set(map(tuple, chain[i])) | set(map(tuple, chain[i - 1])))
    return chain


# ---------------------------------------------------------------------------
# top-level loader
# ---------------------------------------------------------------------------

def load_trajectory(jsonl_path, *, n_vertices=None, optimum_edges=None):
    """Read ``jsonl_path`` and return a dict with the same names ``trajectory.py``
    exposes.  ``n_vertices`` overrides the inferred N; ``optimum_edges``
    overrides the known ex(N, C_4) value (default: the best score actually
    reached in the log)."""
    records = _read_jsonl(jsonl_path)
    if not records:
        raise ValueError(f"empty / unreadable trajectory log: {jsonl_path}")
    n = int(n_vertices) if n_vertices is not None else _infer_n_vertices(records)

    # --- named graph states -------------------------------------------------
    SEED = []
    NAIVE_PLATEAU = _best_object(records[0], n)  # epoch 0 == initial random search
    FINAL = _best_object(records[-1], n)
    samples = _pick_distinct_samples(records, n, NAIVE_PLATEAU, k=2)
    if len(samples) < 2:
        # fall back to top-k of a mid epoch
        mid = records[len(records) // 2]
        decoded = _decode_objs(mid.get("top_k_objects", []), n)
        samples = (samples + [e for e in decoded if e and _score(e, n) >= 0])[:2]
    while len(samples) < 2:
        samples.append(FINAL or NAIVE_PLATEAU or [])
    SAMPLE_1, SAMPLE_2 = samples[0], samples[1]

    final_score = _score(FINAL, n) if FINAL else max(
        (r.get("best_score_so_far", -1) for r in records), default=-1
    )
    OPTIMUM_EDGES = int(optimum_edges) if optimum_edges is not None else int(round(final_score))
    plateau_score = _score(NAIVE_PLATEAU, n) if NAIVE_PLATEAU else int(round(records[0].get("best_score_so_far", 0)))
    NAIVE_SEARCH_CEILING = int(plateau_score)

    # --- Act 2 partition (greedy 2-colouring of sample 1) -------------------
    PART_A, PART_B = _greedy_2coloring(SAMPLE_1, n)
    if not PART_A or not PART_B:  # degenerate; fall back to a contiguous split
        half = n // 2
        PART_A, PART_B = list(range(half)), list(range(half, n))

    # --- Act 1 operations (synthesized) ------------------------------------
    ACT1_OPERATIONS = synthesize_act1_operations(NAIVE_PLATEAU, n, seed=records[0].get("epoch", 0))

    # --- Act 2 top-k pool + samples ----------------------------------------
    # use the *last* epoch with a populated top-k for the pool (most "trained"),
    # or epoch 0 if that's all there is
    pool_rec = next((r for r in reversed(records) if r.get("top_k_objects")), records[0])
    pool_objs = _decode_objs(pool_rec.get("top_k_objects", []), n)
    pool_scores = pool_rec.get("top_k_scores") or [_score(e, n) for e in pool_objs]
    paired = sorted(
        ((s, e) for s, e in zip(pool_scores, pool_objs) if e and s >= 0),
        key=lambda t: t[0], reverse=True,
    )[:4]
    ACT2_TOPK = [{"label": f"search #{i + 1}", "score": int(round(s)), "graph": e} for i, (s, e) in enumerate(paired)]
    if not ACT2_TOPK:  # ensure non-empty
        ACT2_TOPK = [{"label": "search #1", "score": NAIVE_SEARCH_CEILING, "graph": NAIVE_PLATEAU}]
    ACT2_SAMPLES = [
        {"label": "sample 1", "score": int(round(_score(SAMPLE_1, n))), "graph": SAMPLE_1},
        {"label": "sample 2", "score": int(round(_score(SAMPLE_2, n))), "graph": SAMPLE_2},
    ]

    # --- Act 3 iterations (real best-score series, nested graphs to FINAL) --
    series = []
    seen_scores = set()
    for rec in records:
        s = rec.get("best_score_so_far")
        if s is None:
            continue
        s = int(round(s))
        if s in seen_scores:
            continue
        seen_scores.add(s)
        series.append((rec.get("epoch", len(series)), s))
    if not series:
        series = [(0, NAIVE_SEARCH_CEILING), (1, OPTIMUM_EDGES)]
    # the first point sits on the naive ceiling; subsequent points climb
    series = sorted(series, key=lambda t: t[1])
    if series[0][1] != NAIVE_SEARCH_CEILING:
        series = [(0, NAIVE_SEARCH_CEILING)] + series
    if series[-1][1] != OPTIMUM_EDGES:
        series.append((series[-1][0] + 1, OPTIMUM_EDGES))
    target_sizes = [s for _, s in series[1:]]  # graphs for iterations 1..K
    chain = _nested_chain_to_final(FINAL, target_sizes, n) if FINAL else [[] for _ in target_sizes]
    ACT3_ITERATIONS = [{"iteration": 0, "score": series[0][1], "phase": "naive search", "graph": NAIVE_PLATEAU}]
    for i, ((_, s), graph) in enumerate(zip(series[1:], chain), start=1):
        phase = "sample (trained)" if i == 1 else ("optimum" if i == len(series) - 1 else "local search")
        ACT3_ITERATIONS.append({"iteration": i, "score": s, "phase": phase, "graph": graph})

    return {
        "SOURCE": "axplorer-log",
        "LOG_PATH": os.path.abspath(jsonl_path),
        "N_VERTICES": n,
        "OPTIMUM_EDGES": OPTIMUM_EDGES,
        "NAIVE_SEARCH_CEILING": NAIVE_SEARCH_CEILING,
        "SEED": SEED,
        "NAIVE_PLATEAU": NAIVE_PLATEAU,
        "TRANSFORMER_PARTITION_A": PART_A,
        "TRANSFORMER_PARTITION_B": PART_B,
        "TRANSFORMER_SAMPLE_1": SAMPLE_1,
        "TRANSFORMER_SAMPLE_2": SAMPLE_2,
        "FINAL": FINAL,
        "ACT1_OPERATIONS": ACT1_OPERATIONS,
        "ACT2_TOPK": ACT2_TOPK,
        "ACT2_SAMPLES": ACT2_SAMPLES,
        "ACT3_ITERATIONS": ACT3_ITERATIONS,
        "FLYWHEEL_TAGLINE": FLYWHEEL_TAGLINE,
        "NAMED_STATES": {
            "SEED": SEED, "NAIVE_PLATEAU": NAIVE_PLATEAU,
            "TRANSFORMER_SAMPLE_1": SAMPLE_1, "TRANSFORMER_SAMPLE_2": SAMPLE_2, "FINAL": FINAL,
        },
        # extra V2-only diagnostics (scenes ignore these)
        "EPOCHS": len(records),
        "BEST_SCORE_SERIES": [(r.get("epoch"), r.get("best_score_so_far")) for r in records],
        "WALL_TIME_SECONDS": records[-1].get("wall_time_seconds"),
        "SAMPLE_1_CUT_FRACTION": _cut_fraction(SAMPLE_1, set(PART_A)),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _summary(d):
    lines = [
        f"trajectory log:        {d['LOG_PATH']}",
        f"epochs:                {d['EPOCHS']}",
        f"N (vertices):          {d['N_VERTICES']}",
        f"naive plateau (ep 0):  {d['NAIVE_SEARCH_CEILING']} edges",
        f"final / optimum:       {d['OPTIMUM_EDGES']} edges  ({len(d['FINAL'])} edges in selected FINAL graph)",
        f"best-score series:     {[s for _, s in d['BEST_SCORE_SERIES'] if s is not None]}",
        f"wall time (s):         {d['WALL_TIME_SECONDS']}",
        f"transformer sample 1:  {len(d['TRANSFORMER_SAMPLE_1'])} edges, "
        f"cut fraction vs greedy 2-colouring = {d['SAMPLE_1_CUT_FRACTION']:.2f}",
        f"transformer sample 2:  {len(d['TRANSFORMER_SAMPLE_2'])} edges",
        f"Act 1 operations:      {len(d['ACT1_OPERATIONS'])} "
        f"({sum(1 for o,_ in d['ACT1_OPERATIONS'] if o=='add')} add / "
        f"{sum(1 for o,_ in d['ACT1_OPERATIONS'] if o=='reject')} reject)",
        f"Act 2 top-k pool:      {[ (e['label'], e['score']) for e in d['ACT2_TOPK'] ]}",
        f"Act 3 iterations:      {[ (it['iteration'], it['score']) for it in d['ACT3_ITERATIONS'] ]}",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python -m src.trajectory_loader <path-to-trajectory.jsonl>", file=sys.stderr)
        raise SystemExit(2)
    print(_summary(load_trajectory(sys.argv[1])))
