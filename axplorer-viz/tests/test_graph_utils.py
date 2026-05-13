"""Tests for src/graph_utils.py.

Coverage required by the build spec: C_4 itself, K_4, the Petersen graph, and
a 15-vertex tree.
"""

import os
import sys

import networkx as nx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from graph_utils import count_edges, find_4_cycles, has_4_cycle  # noqa: E402


def test_count_edges_matches_networkx():
    G = nx.cycle_graph(4)
    assert count_edges(G) == 4
    assert count_edges(nx.complete_graph(4)) == 6
    assert count_edges(nx.empty_graph(15)) == 0


def test_c4_has_exactly_one_4_cycle():
    G = nx.cycle_graph(4)  # edges 0-1, 1-2, 2-3, 3-0
    assert has_4_cycle(G) is True
    cycles = find_4_cycles(G)
    assert cycles == [(0, 1, 2, 3)]


def test_k4_has_exactly_three_4_cycles():
    G = nx.complete_graph(4)
    assert has_4_cycle(G) is True
    cycles = find_4_cycles(G)
    assert len(cycles) == 3
    # Every reported cycle is genuinely a C_4 in K_4: consecutive vertices adjacent.
    for a, b, c, d in cycles:
        for x, y in ((a, b), (b, c), (c, d), (d, a)):
            assert G.has_edge(x, y)
    # Canonical orientation: starts at smallest vertex, b < d.
    for a, b, c, d in cycles:
        assert a == min(a, b, c, d)
        assert b < d
    assert len(set(cycles)) == len(cycles)


def test_petersen_graph_has_no_4_cycle():
    G = nx.petersen_graph()  # girth 5
    assert has_4_cycle(G) is False
    assert find_4_cycles(G) == []


def test_15_vertex_tree_has_no_4_cycle():
    # A tree is acyclic, hence certainly C_4-free.
    path = nx.path_graph(15)
    star = nx.star_graph(14)  # 15 vertices (center + 14 leaves)
    for tree in (path, star):
        assert tree.number_of_nodes() == 15
        assert nx.is_tree(tree)
        assert has_4_cycle(tree) is False
        assert find_4_cycles(tree) == []


def test_friendship_graph_has_no_4_cycle():
    # Two triangles sharing a single vertex (the friendship graph F_2):
    # no two vertices share more than one common neighbour, so no C_4.
    G = nx.Graph([(0, 1), (0, 2), (1, 2), (0, 3), (0, 4), (3, 4)])
    assert has_4_cycle(G) is False
    assert find_4_cycles(G) == []


def test_diamond_does_have_a_4_cycle():
    # K_4 minus one edge ("diamond"): 2-0-3-1-2 is a C_4 (and the only one).
    G = nx.Graph([(0, 1), (1, 2), (2, 0), (1, 3), (3, 0)])
    assert has_4_cycle(G) is True
    assert find_4_cycles(G) == [(0, 2, 1, 3)]


def test_book_graph_two_4cycles_sharing_an_edge():
    # 0-1 shared; cycles 0-2-1-3-0 and 0-3-1-4-0 ... build explicitly:
    # vertices a,b are the "spine"; pages p create 4-cycles a-p-b-q-a.
    G = nx.Graph()
    a, b = 0, 1
    for p in (2, 3, 4):
        G.add_edge(a, p)
        G.add_edge(b, p)
    # common neighbours of a and b are {2,3,4} -> C(3,2) = 3 distinct 4-cycles.
    cycles = find_4_cycles(G)
    assert len(cycles) == 3
    assert has_4_cycle(G) is True


def test_adding_an_edge_can_create_a_4_cycle():
    # Path 0-1-2-3; adding 0-3 closes a C_4.
    G = nx.path_graph(4)
    assert has_4_cycle(G) is False
    G.add_edge(0, 3)
    assert has_4_cycle(G) is True
    assert find_4_cycles(G) == [(0, 1, 2, 3)]
