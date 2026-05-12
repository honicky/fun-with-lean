"""The whole thing: opening card -> Act 1 -> Act 2 -> Act 3, with fade
transitions and a brief intertitle before each act.

Render this for the final deliverable (see README).  The individual acts also
have their own Scene subclasses if you want to iterate on one in isolation.
"""

from __future__ import annotations

import sys
from pathlib import Path

from manim import DOWN, FadeIn, FadeOut, Scene, Text, UP, VGroup

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import styles as S  # noqa: E402
from act1_naive_search import play_act1  # noqa: E402
from act2_transformer import play_act2  # noqa: E402
from act3_flywheel import play_act3  # noqa: E402


def _card(scene, big, small, *, hold=1.4, big_size=44):
    title = Text(big, font=S.FONT, color=S.TITLE_COLOR, font_size=big_size)
    sub = Text(small, font=S.FONT, color=S.SUBLABEL_COLOR, font_size=24)
    group = VGroup(title, sub).arrange(DOWN, buff=0.35)
    scene.play(FadeIn(group, shift=0.25 * UP), run_time=0.7)
    scene.wait(hold)
    scene.play(FadeOut(group, shift=0.25 * DOWN), run_time=0.6)


class FullVideo(Scene):
    def construct(self):
        self.camera.background_color = S.BACKGROUND_COLOR

        _card(self,
              "Axplorer  ×  Turán's 4-cycle problem",
              "PatternBoost-style search:  on 15 vertices, max edges with no 4-cycle",
              hold=1.3)

        _card(self, "1   ·   the plateau", "plain local search", hold=0.6, big_size=38)
        play_act1(self)
        S.clear_scene(self)

        _card(self, "2   ·   learn the structure", "a transformer trained on the top-k", hold=0.6, big_size=38)
        play_act2(self)
        S.clear_scene(self)

        _card(self, "3   ·   the flywheel", "search  →  train  →  sample  →  search", hold=0.6, big_size=38)
        play_act3(self)
        S.clear_scene(self)
