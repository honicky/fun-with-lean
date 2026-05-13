"""Act 2 (~30s): a transformer trained on the top-k produces structured samples.

Left: the "top-k pool" -- four small graphs the local search found near the
plateau, the 24-edge plateau among them.  Centre: a stylised "Transformer" box
(rounded rectangle + a little attention glyph; no architecture internals).  The
pool flows into the box; out the other side comes ``TRANSFORMER_SAMPLE_1`` --
visibly more regular -- which we then 2-colour to expose its near-bipartite
structure.  A second sample follows.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from manim import (
    Arrow,
    CurvedArrow,
    DOWN,
    Dot,
    FadeIn,
    FadeOut,
    LEFT,
    RIGHT,
    RoundedRectangle,
    Scene,
    Text,
    UP,
    VGroup,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import styles as S  # noqa: E402
import trajectory as T  # noqa: E402

POOL_X = -5.25
POOL_Y = [2.05, 0.6, -0.85, -2.3]
THUMB_R = 0.5

BOX_CENTER = np.array([-0.4, 0.05, 0.0])
BOX_W, BOX_H = 2.9, 3.7

OUT_CENTER = np.array([3.7, 0.05, 0.0])
OUT_R = 1.42


def _thumb(edges):
    pos = S.circle_positions(T.N_VERTICES, radius=THUMB_R, center=(0, 0, 0))
    return S.graph_group(edges, pos, vertex_radius=0.028, edge_color=S.EDGE_COLOR,
                         edge_width=S.EDGE_THUMBNAIL_STROKE_WIDTH)


def _is_within_a(u, v, a_set):
    return (u in a_set) == (v in a_set)


def _transformer_box():
    box = RoundedRectangle(width=BOX_W, height=BOX_H, corner_radius=0.22,
                           stroke_color=S.BOX_STROKE_COLOR, stroke_width=2.4,
                           fill_color=S.BOX_FILL_COLOR, fill_opacity=1.0).move_to(BOX_CENTER)
    title = Text("Transformer", font=S.FONT, color=S.TITLE_COLOR, font_size=26).move_to(BOX_CENTER)
    sub = Text("learns from top-k", font=S.FONT, color=S.SUBLABEL_COLOR, font_size=17)
    sub.next_to(title, DOWN, buff=0.16)

    # tiny "attention" glyph near the top: two rows of dots with a few crossing arcs
    top_y = BOX_CENTER[1] + BOX_H / 2 - 0.55
    bot_y = top_y - 0.7
    xs = np.linspace(BOX_CENTER[0] - 0.8, BOX_CENTER[0] + 0.8, 4)
    top_dots = [Dot([x, top_y, 0], radius=0.035, color=S.ATTENTION_ARROW_COLOR) for x in xs]
    bot_dots = [Dot([x, bot_y, 0], radius=0.035, color=S.ATTENTION_ARROW_COLOR) for x in xs]
    arcs = []
    for (i, j) in [(0, 3), (1, 2), (3, 1), (2, 0)]:
        arcs.append(CurvedArrow(top_dots[i].get_center(), bot_dots[j].get_center(),
                                angle=0.5, tip_length=0.08,
                                color=S.ATTENTION_ARROW_COLOR, stroke_width=1.6))
    glyph = VGroup(*top_dots, *bot_dots, *arcs)

    group = VGroup(box, glyph, title, sub)
    group.box = box
    return group


def play_act2(scene: Scene) -> None:
    header = Text("train on the top-k    →    generate new graphs",
                  font=S.FONT, color=S.LABEL_COLOR, font_size=24).to_edge(UP, buff=0.32)

    # --- the top-k pool -------------------------------------------------
    thumbs = []
    thumb_labels = []
    for entry, y in zip(T.ACT2_TOPK, POOL_Y):
        g = _thumb(entry["graph"]).move_to([POOL_X, y, 0])
        lbl = Text(f"{entry['score']}", font=S.FONT, color=S.SCORE_COLOR, font_size=20)
        lbl.next_to(g, RIGHT, buff=0.18)
        thumbs.append(g)
        thumb_labels.append(lbl)
    pool_caption = Text("top-k pool", font=S.FONT, color=S.SUBLABEL_COLOR, font_size=18)
    pool_caption.move_to([POOL_X, POOL_Y[0] + THUMB_R + 0.45, 0])

    box_group = _transformer_box()

    arrow_in = Arrow(start=[POOL_X + 0.95, 0.05, 0], end=[BOX_CENTER[0] - BOX_W / 2 - 0.12, 0.05, 0],
                     buff=0.05, color=S.SUBLABEL_COLOR, stroke_width=3.0,
                     max_tip_length_to_length_ratio=0.18)
    arrow_in_lbl = Text("+ resample", font=S.FONT, color=S.SUBLABEL_COLOR, font_size=16)
    arrow_in_lbl.next_to(arrow_in, UP, buff=0.08)

    arrow_out = Arrow(start=[BOX_CENTER[0] + BOX_W / 2 + 0.12, OUT_CENTER[1], 0],
                      end=[OUT_CENTER[0] - OUT_R - 0.3, OUT_CENTER[1], 0],
                      buff=0.05, color=S.BOX_STROKE_COLOR, stroke_width=3.0,
                      max_tip_length_to_length_ratio=0.18)
    arrow_out_lbl = Text("sample", font=S.FONT, color=S.SUBLABEL_COLOR, font_size=16)
    arrow_out_lbl.next_to(arrow_out, UP, buff=0.08)

    caption = Text("the model has only seen graphs the local search found",
                   font=S.FONT, color=S.SUBLABEL_COLOR, font_size=S.SUBLABEL_SIZE).to_edge(DOWN, buff=0.34)

    scene.play(FadeIn(header), run_time=0.5)
    scene.play(FadeIn(pool_caption),
               *[FadeIn(g, shift=0.2 * RIGHT) for g in thumbs],
               *[FadeIn(l) for l in thumb_labels], run_time=1.1)
    scene.play(FadeIn(box_group, shift=0.2 * LEFT), FadeIn(arrow_in), FadeIn(arrow_in_lbl),
               FadeIn(caption), run_time=1.1)
    scene.wait(0.6)

    # --- "training": copies of the pool fly into the box ----------------
    flyers = [g.copy() for g in thumbs]
    scene.add(*flyers)
    scene.play(
        *[f.animate.scale(0.12).move_to(BOX_CENTER).set_opacity(0.0) for f in flyers],
        lag_ratio=0.18, run_time=3.0,
    )
    scene.remove(*flyers)
    scene.play(box_group.box.animate.set_stroke(width=4.5), run_time=0.35)
    scene.play(box_group.box.animate.set_stroke(width=2.4), run_time=0.35)
    scene.wait(0.4)

    # --- sample 1 emerges ----------------------------------------------
    a_set = set(T.TRANSFORMER_PARTITION_A)
    s1 = T.ACT2_SAMPLES[0]
    out_pos = S.circle_positions(T.N_VERTICES, radius=OUT_R, center=tuple(OUT_CENTER))
    sample1 = S.graph_group(s1["graph"], out_pos, vertex_radius=0.062,
                            edge_color=S.EDGE_COLOR, edge_width=2.0)
    sample1.save_state()
    sample1.scale(0.14).move_to(BOX_CENTER).set_opacity(0.0)
    scene.add(sample1)
    scene.play(FadeIn(arrow_out), FadeIn(arrow_out_lbl), run_time=0.4)
    scene.play(sample1.animate.restore(), run_time=1.5)

    s1_label = Text(f"sample 1   ·   {s1['score']} edges", font=S.FONT, color=S.SCORE_COLOR, font_size=24)
    s1_label.next_to(VGroup(*sample1.vertex_dots.values()), DOWN, buff=0.28).set_x(OUT_CENTER[0])
    scene.play(FadeIn(s1_label, shift=0.15 * UP), run_time=0.5)
    new_caption = Text("but it gives back something far more regular than search ever found",
                       font=S.FONT, color=S.LABEL_COLOR, font_size=S.SUBLABEL_SIZE).to_edge(DOWN, buff=0.34)
    scene.play(caption.animate.become(new_caption), run_time=0.5)
    scene.wait(1.3)

    # --- highlight the near-bipartite structure -------------------------
    recolors = [
        dot.animate.set_color(S.PARTITION_A_COLOR if v in a_set else S.PARTITION_B_COLOR).scale(1.3)
        for v, dot in sample1.vertex_dots.items()
    ]
    scene.play(*recolors, run_time=1.2)
    # dim the few edges that fall inside an arc; keep the crossing skeleton bright
    edge_emph = []
    for (u, v), line in sample1.edge_lines.items():
        if _is_within_a(u, v, a_set):
            edge_emph.append(line.animate.set_stroke(opacity=0.12))
        else:
            edge_emph.append(line.animate.set_stroke(color=S.EDGE_NEW_COLOR, opacity=0.95))
    struct_label = Text("near-bipartite structure", font=S.FONT, color=S.TITLE_COLOR, font_size=24)
    struct_label.move_to(s1_label).set_x(OUT_CENTER[0])
    scene.play(*edge_emph, s1_label.animate.become(struct_label), run_time=1.0)
    scene.wait(1.5)

    # --- sample 2 emerges -----------------------------------------------
    s2 = T.ACT2_SAMPLES[1]
    sample2 = S.graph_group(s2["graph"], out_pos, vertex_radius=0.062,
                            edge_color=S.EDGE_COLOR, edge_width=2.0)
    for (u, v), line in sample2.edge_lines.items():
        if not _is_within_a(u, v, a_set):
            line.set_stroke(color=S.EDGE_NEW_COLOR, opacity=0.9)
    for v, dot in sample2.vertex_dots.items():
        dot.set_color(S.PARTITION_A_COLOR if v in a_set else S.PARTITION_B_COLOR)
    sample2.save_state()
    sample2.scale(0.14).move_to(BOX_CENTER).set_opacity(0.0)
    s2_label = Text(f"sample 2   ·   {s2['score']} edges", font=S.FONT, color=S.SCORE_COLOR, font_size=24)
    s2_label.move_to(s1_label).set_x(OUT_CENTER[0])

    # `s1_label` is the on-screen text mobject (it became `struct_label`'s look
    # via .become; `struct_label` itself was never added to the scene).
    scene.play(FadeOut(sample1), FadeOut(s1_label), run_time=0.7)
    scene.add(sample2)
    scene.play(sample2.animate.restore(), run_time=1.4)
    scene.play(FadeIn(s2_label, shift=0.15 * UP), run_time=0.5)
    scene.wait(1.0)

    final_caption = Text("structured candidates — now feed them back into the search loop",
                         font=S.FONT, color=S.LABEL_COLOR, font_size=S.SUBLABEL_SIZE).to_edge(DOWN, buff=0.34)
    scene.play(caption.animate.become(final_caption), run_time=0.5)
    scene.wait(1.4)


class Act2Transformer(Scene):
    def construct(self):
        self.camera.background_color = S.BACKGROUND_COLOR
        play_act2(self)
        S.clear_scene(self)
