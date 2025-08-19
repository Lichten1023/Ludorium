"""Placeholder game scene."""

from __future__ import annotations

import pyxel

from engine.input import Input
from engine.scene import Scene


class GameScene(Scene):
    """Simple placeholder scene displayed after the title."""

    def __init__(self, input_device: Input) -> None:
        self._input = input_device

    def update(self, dt: float) -> None:
        """Return to title when START is pressed."""

        if self._input.triggered("START"):
            from scenes.title_scene import TitleScene
            self.change_scene(TitleScene(self._input))

    def draw(self) -> None:
        """Render placeholder text."""

        pyxel.cls(0)
        pyxel.text(50, 60, "Game", 11)
