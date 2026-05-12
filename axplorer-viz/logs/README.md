# logs/

- **`example_N15_run.jsonl`** — a real (short, reproducible) Axplorer run at
  N = 15, committed as evidence the V2 pipeline works end to end. Inspect it:

  ```bash
  uv run python -m src.trajectory_loader logs/example_N15_run.jsonl
  ```

  Heads-up: this run shows the flywheel does *nothing* at N = 15 — the initial
  random-construction phase already finds the optimum (30 edges). See the
  "Finding" note in the top-level `README.md`. It is **not** wired to the video
  (only `square_N15_run.jsonl` is).

- **`square_N15_run.jsonl`** (not committed) — if you put a file here,
  `src/trajectory.py` uses it instead of the V1 hand-curated trajectory and the
  scenes render from it (every magic number — ceiling, optimum, scores, N — is
  read from `trajectory`). Use a *meaningful* run (e.g. converged larger-N) for
  an interesting video; the trivial N = 15 log just gives a flat curve at 30.
  See the "V2" section of the top-level `README.md` for the command, and
  `vendor/PATCH_NOTES.md` for the JSONL schema.
