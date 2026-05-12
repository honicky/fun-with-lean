"""Consistency tests for the hand-curated V1 trajectory.

These are not "is the animation pretty" tests -- they pin down the invariants the
scenes rely on: every curated graph is genuinely C_4-free, edge counts match
their advertised scores, and the Act 1 step list really walks SEED ->
NAIVE_PLATEAU with each "reject" closing a real 4-cycle.
"""

import os
import sys

import networkx as nx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import trajectory as T  # noqa: E402
from graph_utils import count_edges, has_4_cycle  # noqa: E402


def _graph(edges):
    g = nx.empty_graph(T.N_VERTICES)
    g.add_edges_from(edges)
    return g


def test_named_states_are_c4_free():
    for name, edges in T.NAMED_STATES.items():
        assert not has_4_cycle(_graph(edges)), name


def test_headline_edge_counts():
    assert count_edges(_graph(T.SEED)) == 0
    assert count_edges(_graph(T.NAIVE_PLATEAU)) == T.NAIVE_SEARCH_CEILING == 24
    assert 26 <= count_edges(_graph(T.TRANSFORMER_SAMPLE_1)) <= 28
    assert 26 <= count_edges(_graph(T.TRANSFORMER_SAMPLE_2)) <= 28
    # ex(15, C_4) = 30 (OEIS A006855).
    assert count_edges(_graph(T.FINAL)) == T.OPTIMUM_EDGES == 30


def test_final_is_4_regular():
    g = _graph(T.FINAL)
    assert all(d == 4 for _, d in g.degree())


def test_transformer_samples_are_mostly_bipartite():
    a = set(T.TRANSFORMER_PARTITION_A)
    b = set(T.TRANSFORMER_PARTITION_B)
    assert a | b == set(range(T.N_VERTICES)) and not (a & b)
    for sample in (T.TRANSFORMER_SAMPLE_1, T.TRANSFORMER_SAMPLE_2):
        within = sum(1 for u, v in sample if (u in a) == (v in a))
        # "near-bipartite": most edges cross the partition.
        assert within <= len(sample) // 4


def test_naive_plateau_is_maximal():
    # No single edge can be added without creating a 4-cycle -- that's the plateau.
    g = _graph(T.NAIVE_PLATEAU)
    for u in range(T.N_VERTICES):
        for v in range(u + 1, T.N_VERTICES):
            if g.has_edge(u, v):
                continue
            g.add_edge(u, v)
            assert has_4_cycle(g), (u, v)
            g.remove_edge(u, v)


def test_act1_operations_walk_seed_to_plateau():
    ops = T.ACT1_OPERATIONS
    assert 35 <= len(ops) <= 45
    adds = [e for op, e in ops if op == "add"]
    rejects = [e for op, e in ops if op == "reject"]
    assert {op for op, _ in ops} <= {"add", "reject"}
    assert len(adds) + len(rejects) == len(ops)
    # The adds are exactly the plateau's edges (as a set).
    norm = lambda es: {tuple(sorted(e)) for e in es}
    assert norm(adds) == norm(T.NAIVE_PLATEAU)
    assert len(adds) == len(set(norm(adds)))  # no duplicate adds

    g = nx.empty_graph(T.N_VERTICES)
    for op, e in ops:
        if op == "add":
            g.add_edge(*e)
            assert not has_4_cycle(g), ("add closed a 4-cycle", e)
        else:  # reject
            g.add_edge(*e)
            assert has_4_cycle(g), ("reject did not close a 4-cycle", e)
            g.remove_edge(*e)
    assert norm(g.edges()) == norm(T.NAIVE_PLATEAU)


def test_act1_ends_stuck():
    # The last few steps must all be rejects -- "stuck at 24".
    tail_ops = [op for op, _ in T.ACT1_OPERATIONS[-3:]]
    assert tail_ops == ["reject", "reject", "reject"]


def test_act2_pool_and_samples_consistent():
    for entry in T.ACT2_TOPK + T.ACT2_SAMPLES:
        g = _graph(entry["graph"])
        assert not has_4_cycle(g), entry["label"]
        assert count_edges(g) == entry["score"], entry["label"]
    # The plateau itself is in the pool.
    norm = lambda es: {tuple(sorted(e)) for e in es}
    assert any(norm(e["graph"]) == norm(T.NAIVE_PLATEAU) for e in T.ACT2_TOPK)
    # Samples are strictly better than the plateau-region pool max... well, at
    # least one is, and both clear the "structured" bar of 26+.
    assert all(e["score"] >= 26 for e in T.ACT2_SAMPLES)


def test_act3_iterations_climb_to_optimum():
    its = T.ACT3_ITERATIONS
    assert [it["iteration"] for it in its] == list(range(len(its)))
    scores = [it["score"] for it in its]
    assert scores[0] == T.NAIVE_SEARCH_CEILING
    assert scores[-1] == T.OPTIMUM_EDGES
    assert scores == sorted(scores)  # non-decreasing
    assert scores[-1] > scores[0]  # actually climbs
    for it in its:
        g = _graph(it["graph"])
        assert not has_4_cycle(g), it["iteration"]
        assert count_edges(g) == it["score"], it["iteration"]
    # Iterations 1.. are nested (the centre graph just keeps filling in).
    norm = lambda es: {tuple(sorted(e)) for e in es}
    for prev, cur in zip(its[1:], its[2:]):
        assert norm(prev["graph"]) <= norm(cur["graph"])
