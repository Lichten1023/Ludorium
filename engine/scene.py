"""Scene base classes for Ludorium.

要件: Provide lifecycle hooks and helpers for game states.
前提: Managed by ``SceneManager`` which injects itself before use.
戻り値/副作用: Subclasses implement update/draw to modify global Pyxel state.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class Scene(ABC):
    """Abstract base for all scenes.

    要件: Define the interface required by the scene manager.
    前提: ``set_manager`` is called before lifecycle methods.
    戻り値/副作用: ``update`` and ``draw`` are invoked each frame.
    """

    def __init__(self) -> None:
        self._manager: Optional["SceneManager"] = None

    def set_manager(self, manager: "SceneManager") -> None:
        """Inject the managing ``SceneManager``.

        要件: Associate the scene with its manager.
        前提: Called exactly once during scene registration.
        戻り値/副作用: Stores reference for ``change_scene`` helper.
        """

        self._manager = manager

    def change_scene(self, scene: "Scene", data: Optional[Dict[str, Any]] = None) -> None:
        """Request a scene transition through the manager.

        要件: Allow scenes to initiate transitions.
        前提: ``set_manager`` has been invoked.
        戻り値/副作用: Triggers ``SceneManager.change``.
        """

        if self._manager is not None:
            self._manager.change(scene, data)

    def on_enter(self, data: Optional[Dict[str, Any]] = None) -> None:
        """Hook called when the scene becomes active.

        要件: Subclasses may initialize state here.
        前提: Manager ensures this is called exactly once per activation.
        戻り値/副作用: May mutate scene or global state.
        """

    def on_exit(self) -> None:
        """Hook called when the scene is deactivated.

        要件: Subclasses may release resources here.
        前提: Called exactly once before the scene is replaced.
        戻り値/副作用: May mutate scene or global state.
        """

    @abstractmethod
    def update(self, dt: float) -> None:
        """Advance the scene's state.

        要件: Update game logic for the frame.
        前提: ``dt`` is the frame delta time in seconds.
        戻り値/副作用: Mutates internal state.
        """

    @abstractmethod
    def draw(self) -> None:
        """Render the scene.

        要件: Draw current state to Pyxel display.
        前提: Called once per frame after ``update``.
        戻り値/副作用: Uses Pyxel drawing APIs to affect display.
        """
