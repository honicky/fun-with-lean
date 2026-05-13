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
> uses it **if a `logs/square_N<n>_run.jsonl` exists** (largest N wins — e.g.
> `square_N30_run.jsonl`), otherwise it falls back to the V1 data. Check
> `trajectory.TRAJECTORY_SOURCE` to see which is active. The intended V2 run is
> N = 30 (see "V2: producing a real Axplorer trajectory log" below).
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
> - The **V2 plumbing is complete and tested**: `src/trajectory.py` switches to
>   a real log automatically if a `logs/square_N<n>_run.jsonl` is present (largest
>   N wins), and every scene reads its magic numbers (ceiling, optimum, scores,
>   N) from `trajectory`, so they render unchanged on real data. Do a converged
>   **N = 30** run (the intended target — see below), drop the log in `logs/`,
>   and `uv run manim -qh src/scenes/full_video.py FullVideo` renders it. (Point
>   it at the trivial N = 15 log and you'll get a trivial-but-honest video: a
>   flat curve at 30.)
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
│   └── (square_N30_run.jsonl) # do an overnight N=30 run and drop it here -> V2 video
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

The vendored Axplorer runs in its **own** environment (`env_axplorer`) — keep it
separate from the `uv` viz env above; do not merge them. With
[`micromamba`](https://mamba.readthedocs.io/en/latest/user_guide/micromamba.html)
(or `conda`/`mamba`):

```bash
# 1. create the Axplorer env from the vendored environment.yml (name: env_axplorer)
micromamba create -y -f vendor/axplorer/environment.yml
micromamba run -n env_axplorer python -c "import torch; print(torch.__version__)"
micromamba run -n env_axplorer python vendor/axplorer/train.py --help   # sanity check
```

### The intended run: N = 30 (overnight, on a GPU/Mac)

`--N 30` is what makes the flywheel story *real* — greedy search alone plateaus
~5–10 edges below the optimum (`ex(30, C_4)`), so the transformer has structure
to learn. This is the upstream README's instance; budget **~a few hours** on a
GPU or an Apple-Silicon Mac (MPS), longer on plain CPU.

```bash
mkdir -p logs
cd vendor/axplorer
micromamba run -n env_axplorer python train.py \
    --env_name square --exp_name viz_run_N30 --N 30 \
    --encoding_tokens single_integer --max_len 100 \
    --temperature 0.6 --inc_temp 0.1 \
    --log_trajectory ../../logs/square_N30_run.jsonl
cd ../..
```

(On a Mac, leave `--cpu` unset so it uses MPS. The upstream defaults — `--gensize
100000`, `--max_steps 50000`, `--num_samples_from_model 500000`, `--max_epochs
2000` — are fine for a full GPU run; to compress it to ~1–2 h, shrink
`--num_samples_from_model` to ~20–50k, `--gensize` to ~10–20k, and cap
`--max_epochs` to ~15–30 — PatternBoost closes most of the gap in the first few
flywheel iterations.)

Then:

```bash
uv run python -m src.trajectory_loader logs/square_N30_run.jsonl   # sanity-check the log
uv run manim -qh src/scenes/full_video.py FullVideo                # renders the V2 video
```

`src/trajectory.py` automatically uses any `logs/square_N<n>_run.jsonl` (largest
N wins) and every scene reads its magic numbers — the ceiling, the optimum, the
scores, N — from `trajectory`, so the scenes render unchanged on real data. (At
N ≈ 30 the per-graph circular layout gets dense — ~85+ edges — but still renders.)

### A small reproducible run (sanity / N = 15)

```bash
cd vendor/axplorer
micromamba run -n env_axplorer python train.py \
    --env_name square --exp_name viz_run --N 15 \
    --encoding_tokens single_integer --max_len 50 \
    --temperature 0.6 --inc_temp 0.1 \
    --cpu true --process_pool false --seed 1234 \
    --gensize 4000 --pop_size 4000 --max_epochs 6 --max_steps 400 \
    --num_samples_from_model 2000 --gen_batch_size 500 --n_layer 3 --n_embd 192 --n_head 6 \
    --log_trajectory ../../logs/square_N15_run.jsonl
cd ../..
```

`--process_pool false --seed N` makes a run reproducible end to end (with the
process pool, worker RNG state isn't seeded — see `vendor/PATCH_NOTES.md`). This
is the run committed as `logs/example_N15_run.jsonl` — and it's the one that
shows the flywheel is *unnecessary* at N = 15 (see the "Finding" note above).

If `src/envs/` in the vendored copy is unclear, `vendor/axplorer/new_envs.ipynb`
walks through how the `square` environment encodes graphs.

## Tuning the look

Everything visual lives in `src/styles.py` — palette, font, vertex/edge sizes,
the 4-cycle flash color and duration, plot colors, the dark background. Per-act
layout constants (graph centers, radii) sit at the top of each scene file.
