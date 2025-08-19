"""Input abstraction layer for Ludorium.

要件: Allow querying logical input names instead of raw pyxel codes.
前提: ``keymap`` provides mapping from logical names to key codes.
戻り値/副作用: Reads Pyxel key states each frame; no direct side effects.
"""

from __future__ import annotations

from typing import Dict, List

import pyxel


class Input:
    """Manage input states with edge detection."""

    def __init__(self, keymap: Dict[str, List[int]]) -> None:
        self._keymap = keymap
        codes = {code for codes in keymap.values() for code in codes}
        self._current: Dict[int, bool] = {code: False for code in codes}
        self._previous: Dict[int, bool] = {code: False for code in codes}

    def update(self) -> None:
        """Refresh key states.

        要件: Capture the current frame's key states.
        前提: Called once per frame before querying input.
        戻り値/副作用: Updates internal state buffers.
        """

        for code in self._current:
            self._previous[code] = self._current[code]
            self._current[code] = pyxel.btn(code)

    def pressed(self, name: str) -> bool:
        """Check if logical button is held.

        要件: Determine sustained press state.
        前提: ``update`` has been called in the current frame.
        戻り値/副作用: Returns True if any mapped key is down.
        """

        return any(self._current.get(code, False) for code in self._keymap.get(name, []))

    def triggered(self, name: str) -> bool:
        """Check if logical button was pressed this frame.

        要件: Detect rising edge transitions.
        前提: ``update`` has been called in the current frame.
        戻り値/副作用: Returns True only on the frame the key is pressed.
        """

        return any(
            self._current.get(code, False) and not self._previous.get(code, False)
            for code in self._keymap.get(name, [])
        )

    def released(self, name: str) -> bool:
        """Check if logical button was released this frame.

        要件: Detect falling edge transitions.
        前提: ``update`` has been called in the current frame.
        戻り値/副作用: Returns True on the frame the key is released.
        """

        return any(
            not self._current.get(code, False) and self._previous.get(code, False)
            for code in self._keymap.get(name, [])
        )
