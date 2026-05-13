"""Graph scoring + 4-cycle detection for the Turan C_4 problem.

The objective in Act 1-3 is ex(15, C_4): maximize the number of edges in a
simple graph on 15 vertices that contains no 4-cycle.  These helpers are the
ground-truth scoring used by both the curated trajectory and the Manim scenes.
"""

from __future__ import annotations

import itertools


def count_edges(G) -> int:
    """Number of edges in ``G`` -- the quantity Axplorer is maximizing."""
    return G.number_of_edges()


def find_4_cycles(G) -> list[tuple[int, int, int, int]]:
    """All distinct 4-cycles (C_4 subgraphs) in ``G``.

    Each cycle is returned once, in a canonical orientation: the tuple
    ``(a, b, c, d)`` lists the four vertices in cyclic order, starts at the
    smallest vertex ``a``, and proceeds toward the smaller of ``a``'s two
    neighbours, so ``b < d``.  The list is sorted.

    A 4-cycle ``a-b-c-d-a`` has two "diagonals": the opposite pairs ``{a, c}``
    and ``{b, d}``.  Two vertices that share two (or more) common neighbours are
    a diagonal of one 4-cycle per pair of those common neighbours, so we
    enumerate every vertex pair, look at its common neighbourhood, and emit one
    canonical tuple per pair of common neighbours.  The set dedups the two ways
    each cycle is discovered (once from each diagonal).
    """
    cycles: set[tuple[int, int, int, int]] = set()
    for u, w in itertools.combinations(G.nodes(), 2):
        common = (set(G[u]) & set(G[w])) - {u, w}
        if len(common) < 2:
            continue
        for x, y in itertools.combinations(sorted(common), 2):
            # 4-cycle u-x-w-y-u; diagonals {u, w} and {x, y}.
            start = min(u, w, x, y)
            if start in (u, w):
                opposite = w if start == u else u
                left, right = (x, y) if x < y else (y, x)
            else:
                opposite = y if start == x else x
                left, right = (u, w) if u < w else (w, u)
            cycles.add((start, left, opposite, right))
    return sorted(cycles)


def has_4_cycle(G) -> bool:
    """True iff ``G`` contains at least one 4-cycle.

    Cheaper than :func:`find_4_cycles`: stop as soon as some vertex pair has two
    common neighbours.
    """
    for u, w in itertools.combinations(G.nodes(), 2):
        common = (set(G[u]) & set(G[w])) - {u, w}
        if len(common) >= 2:
            return True
    return False
