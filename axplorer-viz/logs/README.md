# logs/

`src/trajectory.py` uses any **`square_N<n>_run.jsonl`** found here to drive the
Manim scenes (largest N wins); otherwise it uses the V1 hand-curated trajectory.
Every scene reads its magic numbers — ceiling, optimum, scores, N — from
`trajectory`, so the scenes render unchanged on real data.

- **`example_N15_run.jsonl`** — a real, short, reproducible Axplorer run at
  N = 15 (`--seed 1234 --process_pool false`), committed as evidence the pipeline
  works end to end. It does **not** auto-activate (only `square_N<n>_run.jsonl`
  does). Note: this run shows the flywheel does *nothing* at N = 15 — the initial
  random-construction phase already finds the optimum (30). See the "Finding"
  note in the top-level `README.md`. Inspect it:

  ```bash
  uv run python -m src.trajectory_loader logs/example_N15_run.jsonl
  ```

- **`square_N30_run.jsonl`** (not committed; you produce it) — the intended V2
  run. `--N 30` is where greedy search demonstrably plateaus and the flywheel has
  to learn structure. See "V2: producing a real Axplorer trajectory log" in the
  top-level `README.md` for the command (budget ~a few hours on a GPU / MPS Mac).
  Once it's here:

  ```bash
  uv run python -m src.trajectory_loader logs/square_N30_run.jsonl
  uv run manim -qh src/scenes/full_video.py FullVideo
  ```

JSONL schema: `vendor/PATCH_NOTES.md`.
