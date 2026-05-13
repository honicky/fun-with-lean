"""Act 3 (~40s): the full flywheel climbs past the baseline to the optimum.

Centre: the working graph.  Left: a live "best so far" edge counter.  Right: a
small loop diagram (sample -> local search -> retrain -> ...) with the active
phase lit.  Bottom: a score-vs-iteration plot with a dashed "naive search
ceiling" at ``trajectory.NAIVE_SEARCH_CEILING``.

We replay ``trajectory.ACT3_ITERATIONS``: iteration 0 is the plateau (sitting
on the ceiling); iteration 1 is the trained model's first structured sample (a
restructuring of the plateau); the rest are local-search refinements that add
edges, climbing toward ``trajectory.OPTIMUM_EDGES``.  The remaining x-axis is
filled flat at the optimum to make the convergence obvious.  Then the graph
drifts to centre, rotates slowly, and the tagline lands.

All the magic numbers come from ``trajectory`` (the ceiling, the optimum, the
iteration scores, N), so this scene renders unchanged whether ``trajectory`` is
the V1 hand-curated data or a real Axplorer log.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from manim import (
    Axes,
    Create,
    CurvedArrow,
    DOWN,
    DashedLine,
    Dot,
    FadeIn,
    FadeOut,
    LEFT,
    Line,
    ORIGIN,
    RIGHT,
    Rotate,
    RoundedRectangle,
    Scene,
    TAU,
    Text,
    UP,
    ValueTracker,
    VGroup,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import styles as S  # noqa: E402
import trajectory as T  # noqa: E402

GRAPH_CENTER = np.array([0.0, 1.3, 0.0])
GRAPH_R = 1.7
COUNTER_POS = np.array([-4.8, 1.55, 0.0])
LOOP_CENTER = np.array([4.7, 1.35, 0.0])
LOOP_R = 1.18

PHASES = ["sample", "search", "retrain"]
PHASE_ANGLE = {"sample": 90, "search": -32, "retrain": 212}  # degrees on the loop


def _norm(e):
    a, b = e
    return (a, b) if a <= b else (b, a)


def _build_loop():
    nodes = {}
    for name in PHASES:
        ang = np.deg2rad(PHASE_ANGLE[name])
        center = LOOP_CENTER + LOOP_R * np.array([np.cos(ang), np.sin(ang), 0.0])
        box = RoundedRectangle(width=1.4, height=0.5, corner_radius=0.12,
                               stroke_color=S.SUBLABEL_COLOR, stroke_width=1.6,
                               fill_color=S.BOX_FILL_COLOR, fill_opacity=1.0)
        txt = Text(name, font=S.FONT, color=S.SUBLABEL_COLOR, font_size=16)
        node = VGroup(box, txt).move_to(center)
        node.box, node.txt = box, txt
        nodes[name] = node
    arcs = []
    order = ["retrain", "sample", "search", "retrain"]
    for a, b in zip(order, order[1:]):
        arcs.append(CurvedArrow(nodes[a].get_center(), nodes[b].get_center(),
                                angle=-0.7, tip_length=0.13,
                                color=S.ATTENTION_ARROW_COLOR, stroke_width=2.0))
    caption = Text("the flywheel", font=S.FONT, color=S.SUBLABEL_COLOR, font_size=15)
    caption.move_to(LOOP_CENTER + np.array([0, -0.02, 0]))
    group = VGroup(*arcs, *nodes.values(), caption)
    group.nodes = nodes
    return group


def _phase_anims(loop, active):
    out = []
    for name, node in loop.nodes.items():
        if name == active:
            out.append(node.box.animate.set_stroke(color=S.GOOD_COLOR, width=3.0))
            out.append(node.txt.animate.set_color(S.TITLE_COLOR))
        else:
            out.append(node.box.animate.set_stroke(color=S.SUBLABEL_COLOR, width=1.6))
            out.append(node.txt.animate.set_color(S.SUBLABEL_COLOR))
    return out


def play_act3(scene: Scene) -> None:
    positions = S.circle_positions(T.N_VERTICES, radius=GRAPH_R, center=tuple(GRAPH_CENTER))

    title = Text("the flywheel:   sample  →  local search  →  retrain  →  …",
                 font=S.FONT, color=S.LABEL_COLOR, font_size=22).to_edge(UP, buff=0.28)

    # --- edge counter ---------------------------------------------------
    counter_caption = Text("EDGES", font=S.FONT, color=S.SCORE_CAPTION_COLOR, font_size=S.SCORE_CAPTION_SIZE)
    counter_caption.move_to(COUNTER_POS + np.array([0, 0.72, 0]))
    score_tracker = ValueTracker(T.ACT3_ITERATIONS[0]["score"])
    counter = S.int_counter(score_tracker, anchor=COUNTER_POS, font_size=S.SCORE_SIZE * 1.7)
    best_caption = Text("best so far", font=S.FONT, color=S.SUBLABEL_COLOR, font_size=16)
    best_caption.move_to(COUNTER_POS + np.array([0, -0.66, 0]))

    # --- working graph --------------------------------------------------
    vertex_dots = {i: Dot(positions[i], radius=S.VERTEX_RADIUS, color=S.VERTEX_COLOR) for i in range(T.N_VERTICES)}
    edge_mobs: dict[tuple[int, int], Line] = {}

    def make_edges(edge_list):
        new = []
        for e in edge_list:
            k = _norm(e)
            if k not in edge_mobs:
                ln = Line(positions[k[0]], positions[k[1]], color=S.EDGE_COLOR, stroke_width=S.EDGE_STROKE_WIDTH)
                ln.set_z_index(-1)
                edge_mobs[k] = ln
                new.append(ln)
        return new

    def drop_edges(edge_list):
        rem = []
        for e in edge_list:
            k = _norm(e)
            if k in edge_mobs:
                rem.append(edge_mobs.pop(k))
        return rem

    PHASE_REF = GRAPH_CENTER + np.array([0, -GRAPH_R - 0.55, 0])

    def phase_text(text, color):
        return Text(text, font=S.FONT, color=color, font_size=22).move_to(PHASE_REF)

    iters = T.ACT3_ITERATIONS
    ceiling_y = T.NAIVE_SEARCH_CEILING          # where the dashed "naive search ceiling" sits
    optimum_y = T.OPTIMUM_EDGES
    start_score = iters[0]["score"]             # the first plotted point (== the plateau, on the ceiling)

    phase_label = phase_text(
        ("naive search — already optimal" if ceiling_y >= optimum_y else f"naive search — stuck at {start_score}"),
        S.WARN_COLOR,
    )

    # --- plot -----------------------------------------------------------
    y_lo, y_hi = ceiling_y - 2, optimum_y + 1
    x_hi = 6                                     # the plot's x-axis spans iterations 0..x_hi
    axes = Axes(
        x_range=[0, x_hi, 1], y_range=[y_lo, y_hi, 2],
        x_length=10.6, y_length=2.0,
        axis_config={"include_numbers": False, "include_tip": False,
                     "stroke_color": S.AXIS_COLOR, "stroke_width": 2.0},
    ).move_to(np.array([-0.7, -2.6, 0.0]))
    x_label = Text("iteration →", font=S.FONT, color=S.SUBLABEL_COLOR, font_size=18).next_to(axes.x_axis, RIGHT, buff=0.1)
    y_label = Text("edges", font=S.FONT, color=S.SUBLABEL_COLOR, font_size=18).next_to(axes.y_axis, UP, buff=0.08)
    tick_opt = Text(str(optimum_y), font=S.FONT, color=S.GOOD_COLOR, font_size=16).next_to(axes.c2p(0, optimum_y), LEFT, buff=0.1)
    tick_ceil = Text(str(ceiling_y), font=S.FONT, color=S.CEILING_COLOR, font_size=16).next_to(axes.c2p(0, ceiling_y), LEFT, buff=0.1)
    ceiling = DashedLine(axes.c2p(0, ceiling_y), axes.c2p(x_hi, ceiling_y), color=S.CEILING_COLOR, stroke_width=2.0, dash_length=0.12)
    ceiling_label = Text("naive search ceiling", font=S.FONT, color=S.CEILING_COLOR, font_size=16)
    ceiling_label.next_to(axes.c2p(2.1, ceiling_y), DOWN, buff=0.1)

    loop = _build_loop()

    # static dashboard pieces -- everything that gets cleared in the finale
    dashboard = [title, counter_caption, counter, best_caption, phase_label,
                 axes, x_label, y_label, tick_ceil, tick_opt, ceiling, ceiling_label, loop]
    plot_marks = []  # plot dots + connector lines

    # --- intro ----------------------------------------------------------
    scene.play(FadeIn(title), run_time=0.5)
    scene.play(*[FadeIn(d) for d in vertex_dots.values()],
               FadeIn(counter_caption), FadeIn(counter), FadeIn(best_caption), FadeIn(loop),
               run_time=1.0)
    plateau_edges = make_edges(iters[0]["graph"])
    scene.play(*[FadeIn(m) for m in plateau_edges], FadeIn(phase_label), run_time=1.0)
    scene.play(Create(axes), FadeIn(x_label), FadeIn(y_label), FadeIn(tick_ceil), FadeIn(tick_opt),
               Create(ceiling), FadeIn(ceiling_label), run_time=1.2)
    p0 = Dot(axes.c2p(0, start_score), radius=0.06, color=S.PLOT_POINT_COLOR)
    plot_marks.append(p0)
    scene.play(FadeIn(p0, scale=2.0), run_time=0.4)
    scene.wait(1.2)

    # --- iterations -----------------------------------------------------
    prev_edges = set(_norm(e) for e in iters[0]["graph"])
    last_pt = p0

    for idx in range(1, len(iters)):
        cur = iters[idx]
        cur_set = set(_norm(e) for e in cur["graph"])
        to_add = [e for e in cur["graph"] if _norm(e) not in prev_edges]
        to_remove = [e for e in iters[idx - 1]["graph"] if _norm(e) not in cur_set]

        if idx == 1:
            scene.play(*_phase_anims(loop, "sample"),
                       phase_label.animate.become(phase_text("sample from the trained model", S.GOOD_COLOR)),
                       run_time=0.7)
            rem = drop_edges(to_remove)
            add = make_edges(to_add)
            scene.play(*[FadeOut(m) for m in rem], run_time=0.6)
            scene.play(*_phase_anims(loop, "search"),
                       phase_label.animate.become(phase_text("local search refines it", S.LABEL_COLOR)),
                       run_time=0.5)
            scene.play(*[Create(m) for m in add], score_tracker.animate.set_value(cur["score"]), run_time=1.4)
        else:
            scene.play(*_phase_anims(loop, "sample"), run_time=0.4)
            add = make_edges(to_add)
            n = len(to_add)
            scene.play(*_phase_anims(loop, "search"),
                       phase_label.animate.become(phase_text(f"local search:  +{n} edge" + ("s" if n != 1 else ""), S.LABEL_COLOR)),
                       run_time=0.5)
            scene.play(*[Create(m) for m in add], score_tracker.animate.set_value(cur["score"]), run_time=0.8)

        new_pt = Dot(axes.c2p(cur["iteration"], cur["score"]), radius=0.06, color=S.PLOT_POINT_COLOR)
        connector = Line(last_pt.get_center(), new_pt.get_center(), color=S.PLOT_CURVE_COLOR, stroke_width=3.0)
        plot_marks += [connector, new_pt]
        scene.play(Create(connector), run_time=0.5)
        scene.play(FadeIn(new_pt, scale=2.0), run_time=0.3)
        last_pt = new_pt

        scene.play(*_phase_anims(loop, "retrain"),
                   phase_label.animate.become(phase_text("retrain on the new top-k", S.SUBLABEL_COLOR)),
                   run_time=0.5)
        scene.wait(0.35)
        prev_edges = cur_set

    # --- convergence: fill the rest of the x-axis flat at the optimum ---
    scene.play(phase_label.animate.become(phase_text("it cannot do better — this is the optimum", S.GOOD_COLOR)),
               run_time=0.6)
    for it in range(len(iters), x_hi + 1):
        new_pt = Dot(axes.c2p(it, optimum_y), radius=0.06, color=S.PLOT_POINT_COLOR)
        connector = Line(last_pt.get_center(), new_pt.get_center(), color=S.PLOT_CURVE_COLOR, stroke_width=3.0)
        plot_marks += [connector, new_pt]
        scene.play(Create(connector), FadeIn(new_pt, scale=1.6), run_time=0.3)
        last_pt = new_pt
    optimum_tag = Text(f"ex({T.N_VERTICES}, no 4-cycle) = {optimum_y}", font=S.FONT, color=S.GOOD_COLOR, font_size=18)
    optimum_tag.next_to(last_pt, UP, buff=0.16)
    plot_marks.append(optimum_tag)
    scene.play(FadeIn(optimum_tag), run_time=0.5)

    scene.play(*[d.animate.set_color(S.GOOD_COLOR) for d in vertex_dots.values()],
               *[m.animate.set_stroke(color=S.GOOD_COLOR, opacity=0.85) for m in edge_mobs.values()],
               run_time=1.0)
    scene.wait(1.2)

    # --- finale ---------------------------------------------------------
    counter.clear_updaters()
    scene.play(*[FadeOut(m) for m in dashboard + plot_marks], run_time=0.8)

    scene.remove(*vertex_dots.values(), *edge_mobs.values())
    graph = VGroup(*edge_mobs.values(), *vertex_dots.values())
    scene.add(graph)
    scene.play(graph.animate.move_to(ORIGIN).scale(1.4), run_time=1.2)
    scene.play(Rotate(graph, angle=TAU / 7, about_point=ORIGIN), run_time=1.8)

    tagline = Text(T.FLYWHEEL_TAGLINE, font=S.FONT, color=S.TITLE_COLOR, font_size=S.TITLE_SIZE)
    tagline.to_edge(DOWN, buff=0.7)
    scene.play(FadeIn(tagline, shift=0.25 * UP), Rotate(graph, angle=TAU / 10, about_point=ORIGIN), run_time=1.4)
    scene.play(Rotate(graph, angle=TAU / 8, about_point=ORIGIN), run_time=1.8)
    scene.wait(1.4)


class Act3Flywheel(Scene):
    def construct(self):
        self.camera.background_color = S.BACKGROUND_COLOR
        play_act3(self)
        S.clear_scene(self)
