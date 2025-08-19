"""Unit tests for basic engine components."""

from __future__ import annotations

import pathlib
import sys
from typing import Dict, List

import pyxel

# Ensure project root is on sys.path
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from engine.input import Input  # type: ignore  # noqa: E402
from engine.scene import Scene  # type: ignore  # noqa: E402
from engine.scene_manager import SceneManager  # type: ignore  # noqa: E402


class DummyScene(Scene):
    def __init__(self) -> None:
        super().__init__()
        self.entered = False
        self.exited = False

    def on_enter(self, data=None):  # type: ignore[override]
        self.entered = True

    def on_exit(self):  # type: ignore[override]
        self.exited = True

    def update(self, dt: float) -> None:  # type: ignore[override]
        pass

    def draw(self) -> None:  # type: ignore[override]
        pass


def test_scene_manager_transitions() -> None:
    manager = SceneManager()
    s1 = DummyScene()
    s2 = DummyScene()
    manager.start(s1)
    assert s1.entered
    manager.change(s2)
    assert s1.exited
    assert s2.entered


def test_input_trigger(monkeypatch) -> None:
    pressed: Dict[int, bool] = {}

    def btn(code: int) -> bool:
        return pressed.get(code, False)

    monkeypatch.setattr(pyxel, "btn", btn)
    keymap: Dict[str, List[int]] = {"START": [1]}
    input_dev = Input(keymap)

    input_dev.update()
    pressed[1] = True
    input_dev.update()
    assert input_dev.triggered("START")
    assert input_dev.pressed("START")
    input_dev.update()
    assert not input_dev.triggered("START")
    pressed[1] = False
    input_dev.update()
    assert input_dev.released("START")
