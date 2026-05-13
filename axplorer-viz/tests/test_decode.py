"""Tests for src/decode.py -- the Axplorer ``single_integer`` token decoder."""

import math
import os
import sys
from itertools import combinations

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from decode import (  # noqa: E402
    all_edge_tokens,
    decode_object,
    decode_token,
    encode_edge,
    num_edge_tokens,
)


@pytest.mark.parametrize("n", [2, 3, 4, 5, 8, 15, 30])
def test_decode_matches_combinations_enumeration(n):
    expected = list(combinations(range(n), 2))
    assert num_edge_tokens(n) == math.comb(n, 2) == len(expected)
    for token, edge in enumerate(expected):
        assert decode_token(token, n) == edge


@pytest.mark.parametrize("n", [2, 3, 4, 5, 8, 15, 30])
def test_encode_decode_roundtrip(n):
    for token, edge in all_edge_tokens(n):
        assert encode_edge(edge, n) == token
        assert decode_token(encode_edge(edge, n), n) == edge
    # encode is order-insensitive on the pair
    for i, j in combinations(range(n), 2):
        assert encode_edge((j, i), n) == encode_edge((i, j), n)


def test_known_small_cases_n15():
    # First few and last token for N=15 (C(15,2) = 105 edge tokens, ids 0..104).
    assert num_edge_tokens(15) == 105
    assert decode_token(0, 15) == (0, 1)
    assert decode_token(1, 15) == (0, 2)
    assert decode_token(13, 15) == (0, 14)
    assert decode_token(14, 15) == (1, 2)
    assert decode_token(104, 15) == (13, 14)


def test_decode_token_rejects_non_edge_tokens():
    for bad in (-1, 105, 106, 200):
        with pytest.raises(ValueError):
            decode_token(bad, 15)
    with pytest.raises(ValueError):
        encode_edge((0, 15), 15)
    with pytest.raises(ValueError):
        encode_edge((3, 3), 15)


def test_decode_object_strips_specials_and_dedups():
    n = 15
    bos, eos = num_edge_tokens(n) + 3, num_edge_tokens(n) + 1
    seq = [bos, 0, 14, 14, 104, eos]  # BOS, (0,1), (1,2), (1,2) dup, (13,14), EOS
    assert decode_object(seq, n) == [(0, 1), (1, 2), (13, 14)]
    assert decode_object([], n) == []
    # a realistic encoded sequence: round-trip a small graph through encode/decode
    edges = [(0, 1), (0, 5), (3, 9), (10, 14)]
    tokens = [bos] + [encode_edge(e, n) for e in edges] + [eos]
    assert decode_object(tokens, n) == sorted(edges)
