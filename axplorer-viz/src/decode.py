"""Decode Axplorer ``single_integer`` edge tokens back to vertex pairs.

The ``square`` environment in Axplorer (AxiomMath/axplorer) represents a graph
on ``N`` vertices as the set of present edges, and -- with
``--encoding_tokens single_integer`` -- encodes each edge ``{i, j}`` (``i < j``)
as a single integer token: its **lexicographic index among**
``itertools.combinations(range(N), 2)``.  So for ``N`` vertices:

    token 0           -> (0, 1)
    token 1           -> (0, 2)
    ...
    token N-2         -> (0, N-1)
    token N-1         -> (1, 2)
    ...
    token C(N,2) - 1  -> (N-2, N-1)

(Their README describes this loosely as "Ni + j"; the real encoding is the
``combinations`` index implemented here -- see
``vendor/axplorer/src/envs/tokenizers.py::SparseTokenizerSingleInteger``.)

Tokens ``>= C(N, 2)`` are the special symbols ``SEP / EOS / PAD / BOS`` -- not
edges; :func:`decode_object` skips them, :func:`decode_token` rejects them.

This module is intentionally dependency-free (pure Python) so it can run inside
the visualization's ``uv`` environment without importing Axplorer.
"""

from __future__ import annotations

import math
from itertools import combinations


def num_edge_tokens(n_vertices: int) -> int:
    """How many token ids correspond to edges, ``C(n, 2)``."""
    return math.comb(n_vertices, 2)


def decode_token(token: int, n_vertices: int) -> tuple[int, int]:
    """Return the edge ``(i, j)`` (``i < j``) for ``token`` on ``n_vertices``.

    Inverse of the ``single_integer`` encoding (lex index in
    ``combinations(range(n_vertices), 2)``).  Raises ``ValueError`` if ``token``
    is out of the edge range (i.e. is a special symbol).
    """
    n = n_vertices
    limit = num_edge_tokens(n)
    if not (0 <= token < limit):
        raise ValueError(
            f"token {token} is not an edge token for N={n} (edge tokens are 0..{limit - 1})"
        )
    # Pairs starting with vertex i: there are (n - 1 - i) of them.
    i = 0
    offset = 0
    while offset + (n - 1 - i) <= token:
        offset += n - 1 - i
        i += 1
    j = i + 1 + (token - offset)
    return (i, j)


def encode_edge(edge: tuple[int, int], n_vertices: int) -> int:
    """Inverse of :func:`decode_token` -- the token id for edge ``{i, j}``.

    Provided mainly so tests can round-trip; the visualization only ever
    decodes.
    """
    i, j = (edge[0], edge[1]) if edge[0] <= edge[1] else (edge[1], edge[0])
    n = n_vertices
    if not (0 <= i < j < n):
        raise ValueError(f"edge {edge} is not valid for N={n}")
    # sum_{k=0}^{i-1} (n - 1 - k)  +  (j - i - 1)
    offset = i * (n - 1) - (i * (i - 1)) // 2
    return offset + (j - i - 1)


def decode_object(token_list, n_vertices: int) -> list[tuple[int, int]]:
    """Decode a logged object (list of edge tokens) to a sorted edge list.

    Any non-edge tokens (special symbols, should not normally appear in the
    logged objects -- the logging patch strips them) are skipped.  Duplicate
    edges are collapsed.
    """
    limit = num_edge_tokens(n_vertices)
    edges = set()
    for t in token_list:
        t = int(t)
        if 0 <= t < limit:
            edges.add(decode_token(t, n_vertices))
    return sorted(edges)


def all_edge_tokens(n_vertices: int):
    """Yield ``(token, (i, j))`` for every edge -- handy for sanity checks."""
    for token, edge in enumerate(combinations(range(n_vertices), 2)):
        yield token, edge
