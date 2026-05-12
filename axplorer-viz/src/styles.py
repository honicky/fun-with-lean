"""Single source of truth for the visualization's look.

Everything tweakable about the aesthetic lives here: the dark Axplorer-blog
palette, fonts, the circular graph layout, plot colours for Act 3, and small
helpers the scenes use to draw graphs consistently.  Scenes import from this
module (plus ``trajectory`` and ``graph_utils``) and nothing else.
"""

from __future__ import annotations

import numpy as np
from manim import Dot, FadeOut, Line, Polygon, Text, ValueTracker, VGroup, VMobject

# ---------------------------------------------------------------------------
# Palette -- dark, like the Axplorer blog.
# ---------------------------------------------------------------------------

BACKGROUND_COLOR = "#0E1116"          # near-black with a cool tint

VERTEX_COLOR = "#5EE6C9"              # teal -- the graph's "ink"
VERTEX_RADIUS = 0.085

EDGE_COLOR = "#8693A8"               # muted slate; edges read but don't shout
EDGE_NEW_COLOR = "#E8EDF4"           # a freshly added edge flashes bright, then settles
EDGE_STROKE_WIDTH = 2.6
EDGE_THUMBNAIL_STROKE_WIDTH = 1.6

FLASH_COLOR = "#FF4D5E"              # 4-cycle violation -- red
FLASH_FILL_OPACITY = 0.28
FLASH_DURATION = 0.4                  # seconds the offending C_4 polygon stays up

GOOD_COLOR = "#52E08A"               # "this worked / optimum reached" -- vivid green
WARN_COLOR = "#FF4D5E"

# Act 2 bipartition highlight.
PARTITION_A_COLOR = "#FF9E6D"        # warm
PARTITION_B_COLOR = "#5BB8F5"        # cool

# Act 3 plot.
AXIS_COLOR = "#5A6472"
PLOT_CURVE_COLOR = "#5EE6C9"         # the score climbing
PLOT_POINT_COLOR = "#E8EDF4"
CEILING_COLOR = "#E5737E"            # the dashed "naive search ceiling" at 24

# Transformer block (Act 2).
BOX_FILL_COLOR = "#161E2B"
BOX_STROKE_COLOR = "#5BB8F5"
ATTENTION_ARROW_COLOR = "#3C5168"

# ---------------------------------------------------------------------------
# Type / text
# ---------------------------------------------------------------------------

FONT = "sans-serif"                   # Pango resolves this to whatever sans is installed

TITLE_COLOR = "#E8EDF4"
TITLE_SIZE = 40

LABEL_COLOR = "#C3CCDA"
LABEL_SIZE = 28

SUBLABEL_COLOR = "#8693A8"
SUBLABEL_SIZE = 22

SCORE_COLOR = "#F2C94C"              # amber -- the number everyone is watching
SCORE_SIZE = 34
SCORE_CAPTION_COLOR = "#8693A8"
SCORE_CAPTION_SIZE = 20

CONSTRAINT_COLOR = "#8693A8"
CONSTRAINT_SIZE = 24

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

GRAPH_RADIUS = 2.55                   # radius of the 15-vertex circle in the main view
THUMBNAIL_RADIUS = 0.62               # radius for the small "top-k" graphs in Act 2

# Default placement of the main graph (Act 1 / Act 3 keep it roughly centre-left
# / centre so the score panel and plot have room).
MAIN_GRAPH_CENTER = np.array([-2.2, 0.4, 0.0])

# Generic fade time for act-to-act transitions.
ACT_FADE_TIME = 0.8


def circle_positions(n: int, radius: float = GRAPH_RADIUS, center=(0.0, 0.0, 0.0)) -> dict[int, np.ndarray]:
    """Vertex i -> 3D point, equally spaced on a circle, vertex 0 at the top,
    going clockwise (matches the convention documented in ``trajectory``)."""
    cx, cy, cz = center
    out: dict[int, np.ndarray] = {}
    for i in range(n):
        theta = np.pi / 2 - 2 * np.pi * i / n
        out[i] = np.array([cx + radius * np.cos(theta), cy + radius * np.sin(theta), cz])
    return out


def _norm_edge(e: tuple[int, int]) -> tuple[int, int]:
    a, b = e
    return (a, b) if a <= b else (b, a)


def graph_group(
    edges,
    positions: dict[int, np.ndarray],
    *,
    vertex_color: str = VERTEX_COLOR,
    vertex_radius: float = VERTEX_RADIUS,
    edge_color: str = EDGE_COLOR,
    edge_width: float = EDGE_STROKE_WIDTH,
    n_vertices: int | None = None,
) -> VGroup:
    """Build a VGroup for a graph drawn at ``positions``.

    The returned group carries three extra attributes for the scenes to grab:

    * ``vertex_dots`` -- dict ``vertex_id -> Dot``
    * ``edge_lines``  -- dict ``(u, v) -> Line`` with ``u <= v``
    * ``positions``   -- the positions dict it was built with

    Edges are added *under* the vertices so dots sit on top of line ends.
    """
    if n_vertices is None:
        n_vertices = len(positions)

    edge_lines: dict[tuple[int, int], Line] = {}
    for e in edges:
        u, v = _norm_edge(tuple(e))
        edge_lines[(u, v)] = Line(
            positions[u], positions[v], color=edge_color, stroke_width=edge_width
        )

    vertex_dots: dict[int, Dot] = {}
    for i in range(n_vertices):
        vertex_dots[i] = Dot(point=positions[i], radius=vertex_radius, color=vertex_color)

    group = VGroup(*edge_lines.values(), *vertex_dots.values())
    group.vertex_dots = vertex_dots
    group.edge_lines = edge_lines
    group.positions = positions
    return group


def cycle_polygon(cycle, positions, *, color: str = FLASH_COLOR, fill_opacity: float = FLASH_FILL_OPACITY) -> Polygon:
    """The red quad drawn over an offending 4-cycle (a, b, c, d)."""
    pts = [positions[v] for v in cycle]
    return Polygon(*pts, color=color, fill_color=color, fill_opacity=fill_opacity, stroke_width=3.0)


def int_counter(tracker, anchor, *, font=FONT, font_size=SCORE_SIZE, color=SCORE_COLOR) -> Text:
    """A ``Text`` digit display driven by a ``ValueTracker`` -- no LaTeX.

    The Text is rebuilt (via ``become``) only when the rounded value changes,
    so it is cheap even though it lives on screen for the whole video.  It stays
    centred on ``anchor`` regardless of how many digits it has.
    """
    anchor = np.array(anchor, dtype=float)

    def _make(v: int) -> Text:
        return Text(str(v), font=font, font_size=font_size, color=color).move_to(anchor)

    label = _make(int(round(tracker.get_value())))

    def _update(mob):
        v = int(round(tracker.get_value()))
        if mob.text != str(v):
            mob.become(_make(v))

    label.add_updater(_update)
    return label


def clear_scene(scene, *, run_time: float = ACT_FADE_TIME):
    """Fade out everything currently on screen (skipping ValueTrackers, which
    have no opacity), then remove leftovers.  Used between acts."""
    for m in list(scene.mobjects):
        if hasattr(m, "clear_updaters"):
            m.clear_updaters()
    visible = [m for m in scene.mobjects if isinstance(m, VMobject)]
    if visible:
        scene.play(*[FadeOut(m) for m in visible], run_time=run_time)
    for m in list(scene.mobjects):
        if not isinstance(m, ValueTracker):
            scene.remove(m)
