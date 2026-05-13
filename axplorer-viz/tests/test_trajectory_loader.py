"""Tests for src/trajectory_loader.py.

There's no real Axplorer log in CI, so we build a *synthetic* JSONL that has the
shape the patched Axplorer (vendor/PATCH_NOTES.md) emits -- reusing the V1
hand-curated graphs as "real" content -- and check that the loader turns it back
into the data structures the Manim scenes consume.
"""

import json
import os
import sys

import networkx as nx
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import trajectory as V1  # noqa: E402  (V1 hand-curated, used as synthetic "real" content)
from decode import decode_object, encode_edge  # noqa: E402
from graph_utils import count_edges, has_4_cycle  # noqa: E402
import trajectory_loader as L  # noqa: E402

N = 15


def _enc(edges):
    return [encode_edge(e, N) for e in edges]


def _graph(edges):
    g = nx.empty_graph(N)
    g.add_edges_from(edges)
    return g


def _write_synth_log(path):
    """A 4-epoch synthetic log: epoch 0 = initial random search (plateau-ish),
    epochs 1-2 = model samples appearing, epoch 3 = the optimum found."""
    # epoch-0 top-k: a few sub-plateau graphs (V1's ACT2_TOPK content)
    ep0_top = [(e["score"], e["graph"]) for e in V1.ACT2_TOPK]
    # epoch 3 top-k: includes the real optimum
    ep3_top = [(count_edges(_graph(V1.FINAL)), V1.FINAL),
               (V1.ACT2_TOPK[0]["score"], V1.ACT2_TOPK[0]["graph"])]
    records = [
        {
            "epoch": 0, "n_vertices": N,
            "top_k_objects": [_enc(g) for _, g in ep0_top],
            "top_k_scores": [float(s) for s, _ in ep0_top],
            "model_samples_raw": [],
            "model_samples_after_search": [],
            "best_score_so_far": float(max(s for s, _ in ep0_top)),
            "wall_time_seconds": 12.0,
        },
        {
            "epoch": 1, "n_vertices": N,
            "top_k_objects": [_enc(V1.NAIVE_PLATEAU)],
            "top_k_scores": [float(count_edges(_graph(V1.NAIVE_PLATEAU)))],
            "model_samples_raw": [_enc(V1.TRANSFORMER_SAMPLE_2)],
            "model_samples_after_search": [_enc(V1.TRANSFORMER_SAMPLE_2)],
            "best_score_so_far": 26.0,
            "wall_time_seconds": 120.0,
        },
        {
            "epoch": 2, "n_vertices": N,
            "top_k_objects": [_enc(V1.TRANSFORMER_SAMPLE_1), _enc(V1.NAIVE_PLATEAU)],
            "top_k_scores": [27.0, 24.0],
            "model_samples_raw": [_enc(V1.TRANSFORMER_SAMPLE_1), _enc(V1.TRANSFORMER_SAMPLE_2)],
            "model_samples_after_search": [_enc(V1.TRANSFORMER_SAMPLE_1)],
            "best_score_so_far": 28.0,
            "wall_time_seconds": 600.0,
        },
        {
            "epoch": 3, "n_vertices": N,
            "top_k_objects": [_enc(g) for _, g in ep3_top],
            "top_k_scores": [float(s) for s, _ in ep3_top],
            "model_samples_raw": [_enc(V1.FINAL)],
            "model_samples_after_search": [_enc(V1.FINAL)],
            "best_score_so_far": 30.0,
            "wall_time_seconds": 1800.0,
        },
    ]
    with open(path, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    return records


@pytest.fixture
def synth_log(tmp_path):
    p = tmp_path / "square_N15_synth.jsonl"
    _write_synth_log(str(p))
    return str(p)


def test_loader_returns_v1_compatible_surface(synth_log):
    d = L.load_trajectory(synth_log)
    required = {
        "N_VERTICES", "OPTIMUM_EDGES", "NAIVE_SEARCH_CEILING", "SEED", "NAIVE_PLATEAU",
        "TRANSFORMER_PARTITION_A", "TRANSFORMER_PARTITION_B", "TRANSFORMER_SAMPLE_1",
        "TRANSFORMER_SAMPLE_2", "FINAL", "ACT1_OPERATIONS", "ACT2_TOPK", "ACT2_SAMPLES",
        "ACT3_ITERATIONS", "FLYWHEEL_TAGLINE", "NAMED_STATES",
    }
    assert required <= set(d)
    assert d["N_VERTICES"] == N
    assert d["SEED"] == []


def test_named_states_are_c4_free_and_make_sense(synth_log):
    d = L.load_trajectory(synth_log)
    for name in ("NAIVE_PLATEAU", "TRANSFORMER_SAMPLE_1", "TRANSFORMER_SAMPLE_2", "FINAL"):
        edges = d[name]
        assert edges  # non-empty
        assert not has_4_cycle(_graph(edges)), name
    # epoch-0 best == plateau; final epoch best is the 30-edge optimum
    assert count_edges(_graph(d["FINAL"])) == 30
    assert d["OPTIMUM_EDGES"] == 30
    assert d["NAIVE_SEARCH_CEILING"] == count_edges(_graph(d["NAIVE_PLATEAU"]))
    # samples are distinct from each other and from the plateau
    norm = lambda es: frozenset(tuple(sorted(e)) for e in es)
    assert norm(d["TRANSFORMER_SAMPLE_1"]) != norm(d["TRANSFORMER_SAMPLE_2"])
    assert norm(d["TRANSFORMER_SAMPLE_1"]) != norm(d["NAIVE_PLATEAU"])


def test_partition_is_a_valid_2_coloring(synth_log):
    d = L.load_trajectory(synth_log)
    a, b = set(d["TRANSFORMER_PARTITION_A"]), set(d["TRANSFORMER_PARTITION_B"])
    assert a | b == set(range(N))
    assert not (a & b)
    assert a and b
    # the synthetic SAMPLE_1 (V1's near-bipartite graph) should mostly cut the partition
    assert d["SAMPLE_1_CUT_FRACTION"] >= 0.5


def test_act1_operations_are_a_valid_synthesized_trace(synth_log):
    d = L.load_trajectory(synth_log)
    ops = d["ACT1_OPERATIONS"]
    assert {op for op, _ in ops} <= {"add", "reject"}
    adds = [e for op, e in ops if op == "add"]
    norm = lambda es: {tuple(sorted(e)) for e in es}
    assert norm(adds) == norm(d["NAIVE_PLATEAU"])
    g = nx.empty_graph(N)
    for op, e in ops:
        if op == "add":
            g.add_edge(*e)
            assert not has_4_cycle(g), ("add closed a 4-cycle", e)
        else:
            g.add_edge(*e)
            assert has_4_cycle(g), ("reject did not close a 4-cycle", e)
            g.remove_edge(*e)
    assert norm(g.edges()) == norm(d["NAIVE_PLATEAU"])
    # determinism: same log -> same trace
    assert L.load_trajectory(synth_log)["ACT1_OPERATIONS"] == ops


def test_act2_pool_and_samples(synth_log):
    d = L.load_trajectory(synth_log)
    assert d["ACT2_TOPK"]
    for entry in d["ACT2_TOPK"] + d["ACT2_SAMPLES"]:
        g = _graph(entry["graph"])
        assert not has_4_cycle(g), entry["label"]
        assert entry["score"] == count_edges(g)
    assert all(e["score"] >= 1 for e in d["ACT2_SAMPLES"])


def test_act3_iterations_climb_and_are_nested(synth_log):
    d = L.load_trajectory(synth_log)
    its = d["ACT3_ITERATIONS"]
    assert [it["iteration"] for it in its] == list(range(len(its)))
    scores = [it["score"] for it in its]
    assert scores == sorted(scores)               # non-decreasing
    assert scores[0] == d["NAIVE_SEARCH_CEILING"]
    assert scores[-1] == d["OPTIMUM_EDGES"]
    assert scores[-1] > scores[0]
    for it in its:
        g = _graph(it["graph"])
        assert not has_4_cycle(g), it["iteration"]
        assert count_edges(g) == it["score"], it["iteration"]
    # iterations 1.. are nested subsets of one another
    norm = lambda es: {tuple(sorted(e)) for e in es}
    for prev, cur in zip(its[1:], its[2:]):
        assert norm(prev["graph"]) <= norm(cur["graph"])
    # the last one is the real FINAL graph
    assert norm(its[-1]["graph"]) == norm(d["FINAL"])


def test_n_vertices_inference_without_explicit_field(tmp_path):
    # drop the n_vertices field; the loader should infer N=15 from token range
    recs = _write_synth_log(str(tmp_path / "x.jsonl"))
    p = tmp_path / "no_n.jsonl"
    with open(p, "w") as f:
        for r in recs:
            r2 = {k: v for k, v in r.items() if k != "n_vertices"}
            f.write(json.dumps(r2) + "\n")
    d = L.load_trajectory(str(p))
    assert d["N_VERTICES"] == N
    # explicit override also works
    assert L.load_trajectory(str(p), n_vertices=15)["N_VERTICES"] == 15


def test_summary_cli_renders(synth_log, capsys):
    d = L.load_trajectory(synth_log)
    text = L._summary(d)
    assert "trajectory log:" in text
    assert "Act 3 iterations:" in text


def test_empty_log_raises(tmp_path):
    p = tmp_path / "empty.jsonl"
    p.write_text("")
    with pytest.raises(ValueError):
        L.load_trajectory(str(p))


# --- integration: load the committed real Axplorer log (a short N=15 run) -----

_EXAMPLE_LOG = os.path.join(os.path.dirname(__file__), "..", "logs", "example_N15_run.jsonl")


@pytest.mark.skipif(not os.path.isfile(_EXAMPLE_LOG), reason="no committed example Axplorer log")
def test_loads_committed_example_log():
    d = L.load_trajectory(_EXAMPLE_LOG)
    assert d["N_VERTICES"] == 15
    for name in ("NAIVE_PLATEAU", "TRANSFORMER_SAMPLE_1", "TRANSFORMER_SAMPLE_2", "FINAL"):
        edges = d[name]
        assert edges and not has_4_cycle(_graph_n(edges, 15)), name
    # this is a *short* run on a *small* instance, so it's not expected to be
    # below the optimum -- N=15 is solved by the initial random search.
    assert d["OPTIMUM_EDGES"] <= 30
    its = d["ACT3_ITERATIONS"]
    assert [it["iteration"] for it in its] == list(range(len(its)))
    assert [it["score"] for it in its] == sorted(it["score"] for it in its)
    for it in its:
        assert not has_4_cycle(_graph_n(it["graph"], 15)), it["iteration"]
        assert count_edges(_graph_n(it["graph"], 15)) == it["score"]
    # the synthesized Act 1 trace still replays to NAIVE_PLATEAU
    g = nx.empty_graph(15)
    for op, e in d["ACT1_OPERATIONS"]:
        if op == "add":
            g.add_edge(*e)
            assert not has_4_cycle(g)
        else:
            g.add_edge(*e)
            assert has_4_cycle(g)
            g.remove_edge(*e)
    norm = lambda es: {tuple(sorted(x)) for x in es}
    assert norm(g.edges()) == norm(d["NAIVE_PLATEAU"])


def _graph_n(edges, n):
    g = nx.empty_graph(n)
    g.add_edges_from(edges)
    return g


# --- log discovery (which file trajectory.py picks up) ------------------------

import trajectory as TRAJ  # noqa: E402


def test_find_trajectory_log_picks_largest_n(tmp_path):
    (tmp_path / "square_N15_run.jsonl").write_text("{}\n")
    (tmp_path / "square_N30_run.jsonl").write_text("{}\n")
    (tmp_path / "square_N21_run.jsonl").write_text("{}\n")
    (tmp_path / "example_N40_run.jsonl").write_text("{}\n")   # not "square_..." -> ignored
    (tmp_path / "notes.txt").write_text("hi")
    assert TRAJ._find_trajectory_log(str(tmp_path)).endswith("square_N30_run.jsonl")


def test_find_trajectory_log_none_when_empty(tmp_path):
    assert TRAJ._find_trajectory_log(str(tmp_path)) is None
    # only an example log -> still None (examples don't auto-activate)
    (tmp_path / "example_N15_run.jsonl").write_text("{}\n")
    assert TRAJ._find_trajectory_log(str(tmp_path)) is None


def test_default_is_v1_when_no_square_log_committed():
    # the repo ships logs/example_N15_run.jsonl but NOT a square_N*_run.jsonl,
    # so the headline trajectory is the V1 hand-curated one.
    assert TRAJ.TRAJECTORY_SOURCE == "v1-hand-curated"
