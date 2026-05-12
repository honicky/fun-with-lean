# logs/

Put a real Axplorer trajectory log here as **`square_N15_run.jsonl`** and
`src/trajectory.py` will pick it up automatically (otherwise the V1
hand-curated trajectory is used). See the "V2" section of the top-level
`README.md` for the exact command, and `vendor/PATCH_NOTES.md` for the JSONL
schema.

Quick check after producing one:

```bash
uv run python -m src.trajectory_loader logs/square_N15_run.jsonl
```

The log is small (a handful of capped entries per epoch) — it's fine to commit
it once you have a converged run (`best_score_so_far` reaching `ex(15, C_4) = 30`).
