"""Scene manager controlling active scene lifecycle.

要件: Manage a single active scene and route game loop calls.
前提: Scenes comply with ``Scene`` interface and are not reused concurrently.
戻り値/副作用: Handles scene transitions and forwards update/draw.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .scene import Scene


class SceneManager:
    """Maintain and update the active scene."""

    def __init__(self) -> None:
        self._current: Optional[Scene] = None

    def start(self, initial: Scene, data: Optional[Dict[str, Any]] = None) -> None:
        """Activate the initial scene.

        要件: Set up the first scene of the game.
        前提: ``initial`` is a freshly created scene instance.
        戻り値/副作用: Calls ``on_enter`` on the scene.
        """

        self._current = initial
        self._current.set_manager(self)
        self._current.on_enter(data)

    def change(self, next_scene: Scene, data: Optional[Dict[str, Any]] = None) -> None:
        """Transition to a new scene.

        要件: Deactivate current scene and switch to ``next_scene``.
        前提: ``start`` has been called once.
        戻り値/副作用: Calls ``on_exit`` and ``on_enter`` appropriately.
        """

        if self._current is not None:
            self._current.on_exit()
        self._current = next_scene
        self._current.set_manager(self)
        self._current.on_enter(data)

    def update(self, dt: float) -> None:
        """Update the active scene.

        要件: Forward the game loop update call.
        前提: A scene has been activated via ``start``.
        戻り値/副作用: Mutates scene state.
        """

        if self._current is not None:
            self._current.update(dt)

    def draw(self) -> None:
        """Draw the active scene.

        要件: Forward draw call for rendering.
        前提: A scene has been activated via ``start``.
        戻り値/副作用: Draws via scene implementation.
        """

        if self._current is not None:
            self._current.draw()
