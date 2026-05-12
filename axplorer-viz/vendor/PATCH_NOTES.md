# axplorer-viz patch to vendored Axplorer

Goal: get **trajectory data out of a real Axplorer run** to feed the Manim
visualization, while changing as little of upstream as possible. Every change
below is marked in the source with a `# [axplorer-viz patch]` comment. The
git diff for this directory (`git log -p axplorer-viz/vendor/axplorer/`) is the
authoritative record.

## Files touched

### `train.py`
- `--log_trajectory <path>` flag: when set, one JSONL line is appended **per
  epoch, after the Selection phase** (`update_datasets`).
- After `args.seed` is finalized, also seed Python's `random` and `numpy`'s
  global RNGs (upstream only seeds `torch` there).
- Helpers `_edge_tokens`, `_n_edge_tokens`, `_append_trajectory_log`, and
  `_TRAJECTORY_LOG_CAP = 32` (caps how many objects/samples go in each line).
- The `sample_and_score(...)` call now passes `raw_token_out=` so a handful of
  pre-local-search samples can be logged.

Each JSONL line:

```json
{
  "epoch": 0,
  "n_vertices": 15,                                   // makes the log self-describing
  "top_k_objects": [[edge_token, ...], ...],          // <= 32, sorted by score desc
  "top_k_scores": [float, ...],                       // edge counts; aligned with top_k_objects
  "model_samples_raw": [[edge_token, ...], ...],      // <= 32, model output BEFORE local search
  "model_samples_after_search": [[edge_token, ...], ...],  // <= 32, AFTER local search, sorted by score desc
  "best_score_so_far": 30.0,
  "wall_time_seconds": 1234.5
}
```

`edge_token` is the `single_integer` encoding: the lexicographic index of edge
`{i, j}` (`i < j`) among `itertools.combinations(range(N), 2)`. See
`axplorer-viz/src/decode.py`.

### `src/evaluator.py`
- `sample_and_score(..., raw_token_out=None, raw_token_cap=32)`: if `raw_token_out`
  is a list, the first `raw_token_cap` raw model-sampled token sequences (before
  local search) are appended to it. Default `None` => identical behaviour to
  upstream.

### `src/envs/cycle.py`
- Removed `np.random.seed(None)` at the top of `SquareDataPoint._add_edges_greedily`.
  Upstream reseeded numpy's global RNG to a *random* state on every call, which
  defeats `--seed`. We rely on `train.py` having seeded numpy instead.

## Reproducibility

`--seed N` plus `--process_pool false` makes a run deterministic end to end.
With the process pool (`--process_pool true`, the default), the worker
processes that do data generation / scoring don't inherit the seeded RNG state,
so a pooled run is only approximately reproducible. For the visualization log we
recommend `--process_pool false` (slower, but at N=15 it's fine).

## What we did NOT change

No refactors, no behaviour changes when `--log_trajectory` is empty (the
default), no new dependencies. `--log_trajectory` off => upstream behaviour
except for the `random`/`numpy` seeding and the removed `np.random.seed(None)`.
