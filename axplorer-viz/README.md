# axplorer-viz

A short Manim explainer for how **Axplorer** — Axiom Math's open-source,
PatternBoost-style extremal-combinatorics search tool
([AxiomMath/axplorer](https://github.com/AxiomMath/axplorer)) — attacks the
**Turán 4-cycle problem at N = 15**: maximize the number of edges in a 15-vertex
simple graph that contains no 4-cycle (`C_4`). The known optimum is
`ex(15, C_4) = 30` (OEIS [A006855](https://oeis.org/A006855)).

The video is three acts (~90 s total):

1. **The plateau** — plain single-edge local search greedily adds edges, keeps
   bumping into 4-cycles, and gets stuck at 24 edges.
2. **Learn the structure** — a transformer trained on the top-k graphs found so
   far emits new, visibly more *regular* (near-bipartite) candidates.
3. **The flywheel** — sample → local search → retrain, repeated; the best score
   climbs past the naive ceiling all the way to the proven optimum, 30.

> ### ⚠️ V1 is a hand-curated trajectory
>
> **None of the graphs or search steps in this repo come from a real Axplorer
> run.** `src/trajectory.py` is hand-authored data, built so the visualization
> *design* can be locked in: the plateau graph, the "aha" transformer samples,
> the per-step stumbles in Act 1, the climb in Act 3 — all curated. Every graph
> *is* genuinely `C_4`-free (checked by `src/graph_utils.py` and the test
> suite), and `FINAL` *is* the real extremal graph for N = 15 — but the
> *trajectory through them* is staged.
>
> **V2** will replace `src/trajectory.py` with a parser for actual Axplorer logs
> (search moves, top-k snapshots, sampled graphs, scores) so the same scenes
> animate a real run. The scenes only touch `trajectory.py` through a small set
> of constants/lists, so swapping the data source is the whole V2 job.

## Layout

```
axplorer-viz/
├── pyproject.toml          # uv-managed; manim 0.18.x, networkx, numpy
├── src/
│   ├── trajectory.py       # hand-curated graph sequence (the V1 "data")
│   ├── graph_utils.py      # count_edges / find_4_cycles / has_4_cycle
│   ├── styles.py           # colors, fonts, layout, small drawing helpers
│   └── scenes/
│       ├── act1_naive_search.py    # Scene: Act1NaiveSearch
│       ├── act2_transformer.py     # Scene: Act2Transformer
│       ├── act3_flywheel.py        # Scene: Act3Flywheel
│       └── full_video.py           # Scene: FullVideo  (the deliverable)
└── tests/
    ├── test_graph_utils.py
    └── test_trajectory.py
```

## Setup

[`uv`](https://docs.astral.sh/uv/) manages the environment. From the repo root:

```bash
uv sync                 # create .venv and install manim 0.18.x, networkx, numpy
uv run pytest           # sanity check: graph utils + trajectory invariants
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

Preview a single act while iterating:

```bash
uv run manim -ql src/scenes/act1_naive_search.py Act1NaiveSearch
uv run manim -ql src/scenes/act2_transformer.py  Act2Transformer
uv run manim -ql src/scenes/act3_flywheel.py     Act3Flywheel
```

The full video — **1080p draft first, then the 1440p final**:

```bash
# 1080p draft
uv run manim -qh src/scenes/full_video.py FullVideo

# 1440p final
uv run manim -qp src/scenes/full_video.py FullVideo
```

Output lands in `media/videos/full_video/<resolution>/FullVideo.mp4`.
A clean full render takes a couple of minutes on an M-series Mac (well under
five). Add `--disable_caching` if you've edited shared modules and want to be
sure nothing stale is reused.

## Tuning the look

Everything visual lives in `src/styles.py` — palette, font, vertex/edge sizes,
the 4-cycle flash color and duration, plot colors, the dark background. Per-act
layout constants (graph centers, radii) sit at the top of each scene file.
