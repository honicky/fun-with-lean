# axplorer-viz

A short Manim explainer for how **Axplorer** — Axiom Math's open-source,
PatternBoost-style extremal-combinatorics search tool
([AxiomMath/axplorer](https://github.com/AxiomMath/axplorer)) — attacks the
**Turán 4-cycle problem at N = 15**: maximize the number of edges in a 15-vertex
simple graph that contains no 4-cycle (`C_4`). The known optimum is
`ex(15, C_4) = 30` (OEIS [A006855](https://oeis.org/A006855)).

The video is three acts (~80 s total):

1. **The plateau** — plain single-edge local search greedily adds edges, keeps
   bumping into 4-cycles, and gets stuck around 24 edges.
2. **Learn the structure** — a transformer trained on the top-k graphs found so
   far emits new, more *regular* (near-bipartite) candidates.
3. **The flywheel** — sample → local search → retrain, repeated; the best score
   climbs past the naive ceiling to the proven optimum, 30.

> ## V1 vs V2 — where the data comes from
>
> The Manim scenes (`src/scenes/`) never change between V1 and V2; only the
> *data source* behind `src/trajectory.py` does.
>
> **V1 — hand-curated.** `src/trajectory.py` ships hand-authored data so the
> visual *design* could be locked in: the plateau graph, the "aha" transformer
> samples, the per-step stumbles in Act 1, the climb in Act 3. Every graph *is*
> genuinely `C_4`-free (checked by `src/graph_utils.py` + tests) and `FINAL`
> *is* a real extremal graph for N = 15 — but the *trajectory through them* is
> staged. The pre-rendered V1 video lives at `preview/axplorer_turan_v1_1080p.mp4`.
>
> **V2 — real Axplorer run.** A vendored fork of Axplorer (`vendor/axplorer/`,
> with a minimal logging patch — see `vendor/PATCH_NOTES.md`) writes a per-epoch
> JSONL trajectory log. `src/trajectory_loader.py` reads it and produces the
> *same* module-level names the scenes import; `src/trajectory.py` automatically
> uses it **if `logs/square_N15_run.jsonl` exists**, otherwise it falls back to
> the V1 data. Check `trajectory.TRAJECTORY_SOURCE` to see which is active.
>
> Some V2 details are still synthesized because the log is per-*epoch*, not
> per-*move*: Act 1's add/reject trace is re-derived to end at the real epoch-0
> graph; Act 3's centre graph fills in toward the real final graph along the
> real best-score series; Act 2's two-colour highlight is a greedy 2-colouring
> of the real sample (so if the real samples *aren't* near-bipartite, it won't
> look bipartite — that's an honest finding, not a bug). The headline numbers
> (plateau score, per-epoch best scores, final = optimum, the actual graphs) are
> straight from the run.
>
> ### Finding: at N = 15, the flywheel has nothing to do
>
> We ran real Axplorer at N = 15 (`logs/example_N15_run.jsonl`, a short
> reproducible run — `--seed 1234 --process_pool false`). The result: **N = 15
> is solved by the initial random-construction phase.** Axplorer's `square`
> environment generates each candidate by greedily adding edges until no more can
> be added without a 4-cycle, and on 15 vertices those maximal graphs land at
> 26–30 edges, with the *optimum (30)* appearing within the first few hundred
> restarts. So `best_score_so_far` is already 30 at epoch 0 and stays flat — the
> transformer + flywheel never get a chance to improve anything.
>
> That's a finding about the **problem size**, not about Axplorer or
> PatternBoost: the loop matters at scales where naive search *doesn't* trivially
> succeed (the upstream README uses N = 30). So:
>
> - The **headline video stays the V1 hand-curated trajectory** — it's a faithful
>   *idealization* of what the search → train → sample loop does where it's
>   needed (a plateau, a learned restructuring, a climb), just compressed onto a
>   visually digestible 15-vertex instance.
> - The **V2 plumbing is complete and tested**: `src/trajectory.py` will switch
>   to a real log automatically if one is present at `logs/square_N15_run.jsonl`,
>   and every scene reads its magic numbers (ceiling, optimum, scores, N) from
>   `trajectory`, so they render unchanged on real data. Drop a *meaningful*
>   trajectory there (e.g. a converged larger-N run) and `uv run manim -qh
>   src/scenes/full_video.py FullVideo` renders it. (Point it at the trivial
>   N = 15 log and you'll get a trivial-but-honest video: a flat curve at 30.)
>
> This repo is a **learning-in-public reproduction** and is **not affiliated
> with Axiom Math**. Axplorer is Apache-2.0; attribution is preserved in
> `vendor/axplorer/LICENSE` and `vendor/README.md`. PatternBoost is from Charton,
> Ellenberg, Wagner & Williamson, *"PatternBoost: Constructions in Mathematics
> with a Little Help from AI"* (2024).

## Layout

```
axplorer-viz/
├── pyproject.toml             # uv-managed (manim 0.18.x, networkx, numpy) — the viz env
├── src/
│   ├── trajectory.py          # V1 hand-curated data; auto-overridden by a real log if present
│   ├── trajectory_loader.py   # reads logs/*.jsonl -> same structures trajectory.py exposes
│   ├── decode.py              # decode Axplorer single_integer edge tokens -> (i, j)
│   ├── graph_utils.py         # count_edges / find_4_cycles / has_4_cycle
│   ├── styles.py              # colors, fonts, layout, small drawing helpers
│   └── scenes/
│       ├── act1_naive_search.py    # Scene: Act1NaiveSearch
│       ├── act2_transformer.py     # Scene: Act2Transformer
│       ├── act3_flywheel.py        # Scene: Act3Flywheel
│       └── full_video.py           # Scene: FullVideo  (the deliverable)
├── tests/                     # graph_utils, trajectory (V1), decode, trajectory_loader
├── vendor/
│   ├── README.md              # provenance + Apache-2.0 note
│   ├── PATCH_NOTES.md         # exactly what our logging patch changes
│   └── axplorer/              # vendored AxiomMath/axplorer + the logging patch
├── logs/
│   ├── example_N15_run.jsonl  # a real (short) Axplorer run — evidence the pipeline works
│   └── (square_N15_run.jsonl) # drop a meaningful run here to switch the video to V2
└── preview/axplorer_turan_v1_1080p.mp4   # pre-rendered V1 video
```

## Setup (the visualization env)

[`uv`](https://docs.astral.sh/uv/) manages the Manim/Python env. From `axplorer-viz/`:

```bash
uv sync                 # create .venv and install manim 0.18.x, networkx, numpy
uv run pytest           # graph utils + trajectory (V1) + decode + loader tests
```

Manim needs system **ffmpeg** plus the **cairo/pango** stack. On macOS:

```bash
brew install ffmpeg pango cairo pkg-config
```

(Debian/Ubuntu: `apt install ffmpeg libpango1.0-dev libcairo2-dev pkg-config`.)
No LaTeX is required — every label is rendered with Pango (`Text`), not `Tex`.

## Rendering

Manim quality flags: `-ql` = 480p15 (fast preview), `-qm` = 720p30,
`-qh` = 1080p60, `-qp` = 1440p60.

```bash
# preview a single act
uv run manim -ql src/scenes/act1_naive_search.py Act1NaiveSearch
uv run manim -ql src/scenes/act2_transformer.py  Act2Transformer
uv run manim -ql src/scenes/act3_flywheel.py     Act3Flywheel

# the full video — 1080p draft first, then the 1440p final
uv run manim -qh src/scenes/full_video.py FullVideo     # 1080p draft
uv run manim -qp src/scenes/full_video.py FullVideo     # 1440p final
```

Output lands in `media/videos/full_video/<resolution>/FullVideo.mp4`
(`media/` is git-ignored). A clean full render takes a couple of minutes on an
M-series Mac (well under five). Add `--disable_caching` if you've edited shared
modules and want to be sure nothing stale is reused. Whichever data source is
active (`trajectory.TRAJECTORY_SOURCE`) is what gets rendered.

## V2: producing a real Axplorer trajectory log

The vendored Axplorer is run in its **own** environment (`env_axplorer`) — keep
it separate from the `uv` viz env above; do not merge them. Using
[`micromamba`](https://mamba.readthedocs.io/en/latest/user_guide/micromamba.html)
(or `conda`/`mamba`):

```bash
# 1. create the Axplorer env from the vendored environment.yml
micromamba create -y -f vendor/axplorer/environment.yml      # name: env_axplorer
micromamba run -n env_axplorer python -c "import torch; print(torch.__version__)"
micromamba run -n env_axplorer python vendor/axplorer/train.py --help   # sanity check

# 2. run the loop on N=15, writing a per-epoch trajectory log
mkdir -p logs
cd vendor/axplorer
micromamba run -n env_axplorer python train.py \
    --env_name square --exp_name viz_run --N 15 \
    --encoding_tokens single_integer --max_len 50 \
    --temperature 0.6 --inc_temp 0.1 \
    --cpu true --process_pool false --seed 1234 \
    --log_trajectory ../../logs/square_N15_run.jsonl
cd ../..
```

Notes:
- Run it until `best_score_so_far` plateaus. At N = 15 the known optimum is
  `ex(15, C_4) = 30` — if the final best isn't 30, the run hasn't converged (let
  it run longer / more epochs) or the config is off.
- The upstream defaults (`--gensize 100000`, `--max_steps 50000`,
  `--num_samples_from_model 500000`, GPU/MPS) are tuned for big GPU runs. On a
  laptop CPU, scale them down (e.g. `--gensize 5000 --max_steps 800
  --num_samples_from_model 5000 --pop_size 4000 --max_epochs 8`) — fewer/cheaper
  epochs, still enough trajectory for the video. With a GPU you can use the
  README defaults from upstream.
- `--process_pool false --seed N` makes a run reproducible end to end (with the
  process pool, worker RNG state isn't seeded — see `vendor/PATCH_NOTES.md`).
- Once `logs/square_N15_run.jsonl` exists, `src/trajectory.py` picks it up
  automatically. Inspect it first:

  ```bash
  uv run python -m src.trajectory_loader logs/square_N15_run.jsonl
  ```

  then re-render: `uv run manim -qh src/scenes/full_video.py FullVideo`.

If `src/envs/` in the vendored copy is unclear, `vendor/axplorer/new_envs.ipynb`
walks through how the `square` environment encodes graphs.

## Tuning the look

Everything visual lives in `src/styles.py` — palette, font, vertex/edge sizes,
the 4-cycle flash color and duration, plot colors, the dark background. Per-act
layout constants (graph centers, radii) sit at the top of each scene file.
