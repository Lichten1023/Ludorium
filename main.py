"""Entry point for the Ludorium project."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import pyxel

from engine.assets import AssetRegistry
from engine.input import Input
from engine.scene_manager import SceneManager
from scenes.title_scene import TitleScene


def load_config(path: str) -> Dict[str, int | str]:
    """Read game configuration.

    要件: Obtain window size and title from JSON file.
    前提: ``path`` points to a valid configuration file.
    戻り値/副作用: Returns dictionary with ``title``, ``width``, ``height``, ``fps``.
    """

    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_keymap(path: str) -> Dict[str, List[int]]:
    """Read key mappings and resolve Pyxel constants.

    要件: Map logical button names to Pyxel key codes.
    前提: JSON values contain constant names defined in ``pyxel`` module.
    戻り値/副作用: Returns mapping for ``Input`` initialization.
    """

    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)

    mapping: Dict[str, List[int]] = {}
    for name, codes in raw.items():
        resolved: List[int] = []
        for code in codes:
            value = getattr(pyxel, code, None)
            if isinstance(value, int):
                resolved.append(value)
        mapping[name] = resolved
    return mapping


def main() -> None:
    """Launch the game and run the Pyxel loop.

    要件: Initialize subsystems and start the title scene.
    前提: Configuration and keymap files exist under ``config/``.
    戻り値/副作用: Opens Pyxel window and enters main loop.
    """

    config = load_config("config/game.json")
    keymap = load_keymap("config/keymap.json")
    input_device = Input(keymap)
    assets = AssetRegistry()
    atlas_path = Path("assets/atlas.csv")
    if atlas_path.exists():
        assets.load_atlas(str(atlas_path))

    pyxel.init(
        config["width"],
        config["height"],
        title=config["title"],
        fps=config["fps"],
    )

    manager = SceneManager()
    manager.start(TitleScene(input_device))

    def update() -> None:
        input_device.update()
        manager.update(1.0 / config["fps"])

    def draw() -> None:
        manager.draw()

    pyxel.run(update, draw)


if __name__ == "__main__":
    main()
