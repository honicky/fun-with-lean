"""Trajectory for the Axplorer / Turan C_4 visualization (V1 fallback + V2 real data).

WHERE THE DATA COMES FROM
-------------------------
By default this module exposes the **V1 hand-curated** trajectory defined below
-- declarative data only (ints/lists/tuples/dicts), no Manim.

If a real Axplorer log exists at ``axplorer-viz/logs/square_N15_run.jsonl``
(produced by the patched, vendored Axplorer -- see ``vendor/PATCH_NOTES.md``),
the module-level names the scenes import (``SEED``, ``NAIVE_PLATEAU``,
``TRANSFORMER_SAMPLE_1`` ... ``ACT3_ITERATIONS``, etc.) are **overridden** at
import time by :func:`trajectory_loader.load_trajectory`, so the same Manim
scenes render from the real run with zero code changes in ``scenes/``.  Check
``trajectory.TRAJECTORY_SOURCE`` to see which one is active.  (If the log is
present but unreadable, we warn and keep the V1 data.)

The V1 part below stays purely declarative; the V2 wiring lives in one small
block at the bottom of the file.

PROBLEM
-------
ex(15, C_4): the maximum number of edges in a simple graph on 15 vertices that
contains no 4-cycle.  The known value is 30.

  Source: OEIS A006855, "Maximal number of edges in an n-node graph with no
  4-cycle (C_4)" -- the term for n=15 is 30.  https://oeis.org/A006855
  (This is the n=15 case of the Zarankiewicz/Kovari-Sos-Turan problem; see also
  Clapham, Flockhart & Sheehan, "Graphs without four-cycles", J. Graph Theory
  13 (1989), which tabulates the small extremal numbers and graphs.)

All graph states below were checked with src/graph_utils.has_4_cycle and are
C_4-free.  The 15 vertices are intended to be drawn equally spaced around a
circle, vertex i at angle 90 deg - i * 360/15 deg (vertex 0 at the top, going
clockwise) -- the scenes own that layout; this file only fixes the labels.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Problem constants
# ---------------------------------------------------------------------------

N_VERTICES: int = 15

#: Known optimum ex(15, C_4) -- the score the flywheel must reach. See module docstring.
OPTIMUM_EDGES: int = 30

#: Where plain single-edge-addition local search gets stuck (Act 1 plateau /
#: Act 3 "naive search ceiling" dashed line).
NAIVE_SEARCH_CEILING: int = 24


# ---------------------------------------------------------------------------
# Named graph states (edge lists; vertices 0..14)
# ---------------------------------------------------------------------------

#: Act 1 starting point: 15 isolated vertices, no edges.
SEED: list[tuple[int, int]] = []

#: Where greedy/local search plateaus: 24 edges, *maximal* C_4-free (no single
#: edge can be added without creating a 4-cycle), but visibly lumpy and
#: asymmetric -- one vertex of degree 6, several of degree 2.  Clearly far from
#: the regular extremal structure.
NAIVE_PLATEAU: list[tuple[int, int]] = [
    (0, 6), (0, 9), (0, 10), (0, 11), (0, 14),
    (1, 6), (1, 7), (1, 13),
    (2, 6), (2, 12),
    (3, 4), (3, 5), (3, 6),
    (4, 9),
    (5, 8), (5, 11), (5, 12),
    (6, 7), (6, 14),
    (7, 8),
    (8, 10),
    (9, 10), (9, 12),
    (10, 13),
]

# The transformer's "aha" samples: both are near-bipartite C_4-free graphs with
# the vertices split into the two arcs A = {0..6} and B = {7..14}; the vast
# majority of edges cross between the arcs (only ~5 lie inside an arc).  Far more
# regular and structured than NAIVE_PLATEAU -- this is the point.
TRANSFORMER_PARTITION_A: list[int] = [0, 1, 2, 3, 4, 5, 6]
TRANSFORMER_PARTITION_B: list[int] = [7, 8, 9, 10, 11, 12, 13, 14]

#: 27 edges; the graph highlighted with a 2-colouring in Act 2.
TRANSFORMER_SAMPLE_1: list[tuple[int, int]] = [
    (0, 5), (0, 8), (0, 11), (0, 14),
    (1, 9), (1, 10), (1, 12), (1, 14),
    (2, 8), (2, 9), (2, 13),
    (3, 7), (3, 10), (3, 11),
    (4, 7), (4, 13), (4, 14),
    (5, 7), (5, 8), (5, 12),
    (6, 11), (6, 12), (6, 13),
    (7, 10),
    (8, 9),
    (9, 10),
    (11, 14),
]

#: 26 edges; a second, structurally distinct sample from the model.
TRANSFORMER_SAMPLE_2: list[tuple[int, int]] = [
    (0, 3), (0, 11), (0, 13), (0, 14),
    (1, 2), (1, 7), (1, 8), (1, 14),
    (2, 6), (2, 8), (2, 12), (2, 13),
    (3, 7), (3, 9), (3, 11), (3, 12),
    (4, 5), (4, 9), (4, 10), (4, 14),
    (5, 7), (5, 10), (5, 13),
    (6, 10), (6, 12),
    (10, 11),
]

#: The N=15 optimum: 30 edges, 4-regular, C_4-free.  Built so the 15 perimeter
#: edges (i, i+1 mod 15) are all present, plus 15 chords -- it reads as a
#: deliberately engineered structure in the circular layout, in contrast to the
#: yarn-ball plateau.
FINAL: list[tuple[int, int]] = [
    # perimeter (the 15-cycle 0-1-2-...-14-0)
    (0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8),
    (8, 9), (9, 10), (10, 11), (11, 12), (12, 13), (13, 14), (0, 14),
    # chords
    (0, 2), (0, 10),
    (1, 7), (1, 8),
    (2, 12),
    (3, 9), (3, 12),
    (4, 6), (4, 9),
    (5, 13), (5, 14),
    (6, 11),
    (7, 11),
    (8, 13),
    (10, 14),
]


# ---------------------------------------------------------------------------
# Act 1: SEED -> NAIVE_PLATEAU, with realistic stumbles.
# ---------------------------------------------------------------------------
#
# A sequence of (operation, (u, v)) steps.  Operations:
#   "add"    -- the candidate edge was C_4-free, so it is kept.
#   "reject" -- adding the candidate edge would have closed a 4-cycle, so local
#               search flashes the offending C_4 and discards the edge.
#
# 40 steps: 24 "add" (exactly the edges of NAIVE_PLATEAU) and 16 "reject".
# Replaying the "add" steps in this order is C_4-free at every prefix, and every
# "reject" step genuinely closes a 4-cycle against the graph built so far -- so
# Act 1 can verify each step live with src/graph_utils rather than trusting
# this list.  The last few steps are all rejects: the graph is maximal, search
# is stuck -> "Stuck at 24".

ACT1_OPERATIONS: list[tuple[str, tuple[int, int]]] = [
    ("add", (1, 6)),
    ("add", (6, 14)),
    ("add", (9, 12)),
    ("add", (5, 11)),
    ("add", (1, 13)),
    ("reject", (13, 14)),
    ("add", (5, 8)),
    ("add", (10, 13)),
    ("reject", (6, 10)),
    ("add", (9, 10)),
    ("add", (1, 7)),
    ("reject", (1, 9)),
    ("add", (7, 8)),
    ("add", (4, 9)),
    ("add", (5, 12)),
    ("reject", (4, 5)),
    ("add", (2, 6)),
    ("reject", (8, 13)),
    ("add", (0, 6)),
    ("reject", (7, 14)),
    ("add", (2, 12)),
    ("reject", (1, 12)),
    ("add", (3, 5)),
    ("add", (0, 11)),
    ("reject", (0, 7)),
    ("add", (6, 7)),
    ("reject", (0, 8)),
    ("add", (0, 10)),
    ("reject", (8, 9)),
    ("add", (0, 9)),
    ("add", (8, 10)),
    ("reject", (11, 14)),
    ("add", (3, 6)),
    ("add", (0, 14)),
    ("add", (3, 4)),
    ("reject", (2, 14)),
    ("reject", (4, 6)),
    ("reject", (4, 7)),
    ("reject", (8, 12)),
    ("reject", (2, 5)),
]


# ---------------------------------------------------------------------------
# Act 2: the "top-k" pool fed into the transformer.
# ---------------------------------------------------------------------------
# Four small graphs the local-search phase found near the plateau; their scores
# are deliberately a bit below the plateau, except the plateau itself.  These
# are the thumbnails that flow into the transformer block.

ACT2_TOPK: list[dict] = [
    {"label": "search #1", "score": 24, "graph": NAIVE_PLATEAU},
    {"label": "search #2", "score": 22, "graph": [
        (0, 6), (0, 9), (0, 10), (0, 11), (1, 6), (1, 7), (1, 13),
        (2, 6), (2, 12), (3, 4), (3, 5), (3, 6), (4, 9), (5, 8),
        (5, 11), (6, 7), (7, 8), (8, 10), (9, 10), (9, 12), (10, 13), (0, 14),
    ]},
    {"label": "search #3", "score": 21, "graph": [
        (0, 6), (0, 9), (0, 11), (0, 14), (1, 6), (1, 7), (2, 6),
        (2, 12), (3, 4), (3, 5), (3, 6), (4, 9), (5, 8), (5, 11),
        (6, 14), (7, 8), (8, 10), (9, 10), (9, 12), (10, 13), (1, 13),
    ]},
    {"label": "search #4", "score": 23, "graph": [
        (0, 6), (0, 9), (0, 10), (0, 11), (0, 14), (1, 6), (1, 7),
        (1, 13), (2, 6), (2, 12), (3, 4), (3, 5), (3, 6), (4, 9), (5, 8),
        (5, 11), (5, 12), (6, 7), (7, 8), (8, 10), (9, 10), (9, 12), (10, 13),
    ]},
]

#: The samples the transformer emits in Act 2, shown one after another.
ACT2_SAMPLES: list[dict] = [
    {"label": "sample 1", "score": 27, "graph": TRANSFORMER_SAMPLE_1},
    {"label": "sample 2", "score": 26, "graph": TRANSFORMER_SAMPLE_2},
]


# ---------------------------------------------------------------------------
# Act 3: the flywheel loop. Each entry = one compressed iteration.
# ---------------------------------------------------------------------------
# iteration 0 is the naive-search plateau (carried over, sits on the dashed
# ceiling line).  Iteration 1 is the first structured sample from the trained
# model -- a *restructuring* of the plateau (not a superset of it).  Iterations
# 2, 3, 4 are local-search refinements, each adding one edge, climbing
# 27 -> 28 -> 29 -> 30 = the optimum.  The iteration-1..4 graphs are nested
# (G27 subset G28 subset G29 subset FINAL), so the centre graph just keeps
# filling in toward the regular extremal structure.

_ACT3_LEFT_OUT: list[tuple[int, int]] = [(3, 9), (5, 13), (7, 11)]
_ACT3_G27: list[tuple[int, int]] = [e for e in FINAL if e not in _ACT3_LEFT_OUT]
_ACT3_G28: list[tuple[int, int]] = _ACT3_G27 + [(3, 9)]
_ACT3_G29: list[tuple[int, int]] = _ACT3_G28 + [(5, 13)]

ACT3_ITERATIONS: list[dict] = [
    {"iteration": 0, "score": 24, "phase": "naive search",       "graph": NAIVE_PLATEAU},
    {"iteration": 1, "score": 27, "phase": "sample (trained)",   "graph": _ACT3_G27},
    {"iteration": 2, "score": 28, "phase": "local search",       "graph": _ACT3_G28},
    {"iteration": 3, "score": 29, "phase": "local search",       "graph": _ACT3_G29},
    {"iteration": 4, "score": 30, "phase": "optimum",            "graph": FINAL},
]

#: Title card at the end of Act 3.
FLYWHEEL_TAGLINE: str = "Axplorer: 2.5 hours, $3, one GPU."


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------

#: All five canonical states keyed by name, for tests / sanity checks.
NAMED_STATES: dict[str, list[tuple[int, int]]] = {
    "SEED": SEED,
    "NAIVE_PLATEAU": NAIVE_PLATEAU,
    "TRANSFORMER_SAMPLE_1": TRANSFORMER_SAMPLE_1,
    "TRANSFORMER_SAMPLE_2": TRANSFORMER_SAMPLE_2,
    "FINAL": FINAL,
}


# ===========================================================================
# V2 wiring: if a real Axplorer log is present, override the names above with
# data parsed from it.  See module docstring and vendor/PATCH_NOTES.md.
# (This is the only non-declarative part of the module.)
# ===========================================================================

import os as _os  # noqa: E402

#: Which dataset is active: "v1-hand-curated" or "axplorer-log:<relpath>".
TRAJECTORY_SOURCE: str = "v1-hand-curated"

#: Where a real Axplorer trajectory log is expected (axplorer-viz/logs/...).
TRAJECTORY_LOG_PATH: str = _os.path.normpath(
    _os.path.join(_os.path.dirname(__file__), "..", "logs", "square_N15_run.jsonl")
)

_OVERRIDABLE = (
    "N_VERTICES", "OPTIMUM_EDGES", "NAIVE_SEARCH_CEILING",
    "SEED", "NAIVE_PLATEAU", "TRANSFORMER_PARTITION_A", "TRANSFORMER_PARTITION_B",
    "TRANSFORMER_SAMPLE_1", "TRANSFORMER_SAMPLE_2", "FINAL",
    "ACT1_OPERATIONS", "ACT2_TOPK", "ACT2_SAMPLES", "ACT3_ITERATIONS",
    "FLYWHEEL_TAGLINE", "NAMED_STATES",
)

if _os.path.isfile(TRAJECTORY_LOG_PATH):
    try:
        import sys as _sys

        _sys.path.insert(0, _os.path.dirname(__file__))
        from trajectory_loader import load_trajectory as _load_trajectory

        LOADED_TRAJECTORY = _load_trajectory(
            TRAJECTORY_LOG_PATH, n_vertices=N_VERTICES, optimum_edges=OPTIMUM_EDGES
        )
        for _name in _OVERRIDABLE:
            if _name in LOADED_TRAJECTORY:
                globals()[_name] = LOADED_TRAJECTORY[_name]
        TRAJECTORY_SOURCE = "axplorer-log:" + _os.path.relpath(TRAJECTORY_LOG_PATH, _os.path.dirname(__file__))
    except Exception as _exc:  # pragma: no cover - corrupt/incompatible log
        import warnings as _warnings

        _warnings.warn(
            f"axplorer-viz: found a trajectory log at {TRAJECTORY_LOG_PATH} but failed to load it "
            f"({_exc!r}); falling back to the V1 hand-curated trajectory.",
            stacklevel=2,
        )
