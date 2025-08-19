"""Title scene for Ludorium."""

from __future__ import annotations

from typing import Any, Dict, Optional

import pyxel

from engine.input import Input
from engine.scene import Scene
from scenes.game_scene import GameScene


class TitleScene(Scene):
    """Display the title screen and wait for start input."""

    def __init__(self, input_device: Input) -> None:
        self._input = input_device

    def update(self, dt: float) -> None:
        """Check for start input and change scene."""

        if self._input.triggered("START"):
            self.change_scene(GameScene(self._input))

    def draw(self) -> None:
        """Render title text."""

        pyxel.cls(0)
        pyxel.text(40, 50, "Ludorium", 7)
        pyxel.text(20, 80, "Press SPACE to start", 7)
