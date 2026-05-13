"""Act 1 (~20s): naive local search hits a plateau around 24 edges.

15 vertices in a circle on the left, a live edge counter top-right, the
constraint pinned along the bottom.  We replay ``trajectory.ACT1_OPERATIONS``:
greedy edge additions, and -- when an attempted edge would close a 4-cycle --
a red quad flashes over the offending C_4 and the edge is discarded.  The act
ends parked on a maximal 24-edge graph: "Stuck at 24."
"""

from __future__ import annotations

import sys
from pathlib import Path

import networkx as nx
import numpy as np
from manim import (
    Create,
    DOWN,
    Dot,
    FadeIn,
    FadeOut,
    Line,
    Scene,
    Text,
    UP,
    ValueTracker,
    VGroup,
    Write,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import styles as S  # noqa: E402
import trajectory as T  # noqa: E402
from graph_utils import find_4_cycles  # noqa: E402

MAIN_CENTER = np.array([-2.5, 0.35, 0.0])
GRAPH_RADIUS = 2.5


def _offending_cycle(running: nx.Graph, u: int, v: int):
    """Return a 4-cycle of ``running + (u, v)`` that uses the edge (u, v)."""
    running.add_edge(u, v)
    cycles = find_4_cycles(running)
    running.remove_edge(u, v)
    target = frozenset((u, v))
    for a, b, c, d in cycles:
        sides = (frozenset((a, b)), frozenset((b, c)), frozenset((c, d)), frozenset((d, a)))
        if target in sides:
            return (a, b, c, d)
    return cycles[0]  # the curated trajectory guarantees a cycle through (u, v)


def play_act1(scene: Scene) -> None:
    positions = S.circle_positions(T.N_VERTICES, radius=GRAPH_RADIUS, center=MAIN_CENTER)

    # --- static frame ---------------------------------------------------
    context = Text(
        "Turán's problem  ·  15 vertices  ·  no 4-cycles",
        font=S.FONT, color=S.SUBLABEL_COLOR, font_size=S.SUBLABEL_SIZE,
    ).to_edge(UP, buff=0.3)

    constraint = Text(
        "maximize edges    ·    avoid 4-cycles",
        font=S.FONT, color=S.CONSTRAINT_COLOR, font_size=S.CONSTRAINT_SIZE,
    ).to_edge(DOWN, buff=0.35)

    col_x = 4.2
    score_caption = Text("EDGES", font=S.FONT, color=S.SCORE_CAPTION_COLOR, font_size=S.SCORE_CAPTION_SIZE)
    score_caption.move_to(np.array([col_x, 2.95, 0.0]))
    score_tracker = ValueTracker(0)
    score_value = S.int_counter(score_tracker, anchor=np.array([col_x, 2.25, 0.0]),
                                font_size=S.SCORE_SIZE * 1.7)

    phase_label = Text("greedy search", font=S.FONT, color=S.LABEL_COLOR, font_size=24)
    phase_label.move_to(np.array([col_x, 1.15, 0.0]))

    vertex_dots = {
        i: Dot(point=positions[i], radius=S.VERTEX_RADIUS, color=S.VERTEX_COLOR)
        for i in range(T.N_VERTICES)
    }
    vertices_group = VGroup(*vertex_dots.values())

    scene.play(FadeIn(context), FadeIn(constraint), run_time=0.7)
    scene.play(Write(score_caption), FadeIn(score_value), FadeIn(phase_label), run_time=0.5)
    scene.play(FadeIn(vertices_group, lag_ratio=0.08), run_time=1.0)

    # --- replay the search ---------------------------------------------
    running = nx.empty_graph(T.N_VERTICES)
    edge_lines: dict[tuple[int, int], Line] = {}
    added_count = 0

    for op, (u, v) in T.ACT1_OPERATIONS:
        if op == "add":
            added_count += 1
            running.add_edge(u, v)
            line = Line(positions[u], positions[v], color=S.EDGE_NEW_COLOR, stroke_width=S.EDGE_STROKE_WIDTH)
            line.set_z_index(-1)
            edge_lines[(min(u, v), max(u, v))] = line
            scene.play(Create(line), score_tracker.animate.set_value(added_count), run_time=0.16)
            line.set_color(S.EDGE_COLOR)  # settle to resting colour
        else:  # reject
            a, b, c, d = _offending_cycle(running, u, v)
            tentative = Line(positions[u], positions[v], color=S.WARN_COLOR, stroke_width=S.EDGE_STROKE_WIDTH)
            poly = S.cycle_polygon((a, b, c, d), positions)
            scene.play(Create(tentative), run_time=0.14)
            scene.play(FadeIn(poly), run_time=0.10)
            scene.wait(max(0.02, S.FLASH_DURATION - 0.24))
            scene.play(FadeOut(poly), FadeOut(tentative), run_time=0.14)

    # --- stuck ----------------------------------------------------------
    new_phase = Text("— stuck —", font=S.FONT, color=S.WARN_COLOR, font_size=24)
    new_phase.move_to(phase_label)
    scene.play(phase_label.animate.become(new_phase), run_time=0.4)

    stuck = Text(f"Stuck at {added_count}", font=S.FONT, color=S.WARN_COLOR, font_size=S.TITLE_SIZE)
    stuck.next_to(vertices_group, DOWN, buff=0.34).set_x(MAIN_CENTER[0])
    scene.play(FadeIn(stuck, shift=0.2 * UP), run_time=0.5)
    scene.wait(1.3)


class Act1NaiveSearch(Scene):
    def construct(self):
        self.camera.background_color = S.BACKGROUND_COLOR
        play_act1(self)
        S.clear_scene(self)
