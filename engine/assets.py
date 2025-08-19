"""Asset registry for Ludorium."""

from __future__ import annotations

import csv
from typing import Dict, Tuple

import pyxel

SpriteUV = Tuple[int, int, int, int, int]
TilemapInfo = Tuple[int, int]


class AssetRegistry:
    """Resolve asset names to sprite and tilemap information."""

    def __init__(self) -> None:
        self._sprites: Dict[str, SpriteUV] = {}
        self._tilemaps: Dict[str, TilemapInfo] = {}

    def load_pyxres(self, path: str) -> None:
        """Load a Pyxel resource file.

        要件: Import sprite banks and tilemaps from disk.
        前提: ``path`` points to a valid `.pyxres` file.
        戻り値/副作用: Populates Pyxel's internal image and tilemap banks.
        """

        pyxel.load(path)

    def register_sprite(self, name: str, bank: int, u: int, v: int, w: int, h: int) -> None:
        """Register a sprite entry.

        要件: Associate a name with a sprite region.
        前提: Coordinates reference already loaded Pyxel image banks.
        戻り値/副作用: Stores sprite mapping for later lookup.
        """

        self._sprites[name] = (bank, u, v, w, h)

    def sprite_uv(self, name: str) -> SpriteUV:
        """Return sprite UV information.

        要件: Retrieve coordinates for a registered sprite.
        前提: ``name`` exists in the registry.
        戻り値/副作用: Returns tuple ``(bank, u, v, w, h)``.
        """

        return self._sprites[name]

    def register_tilemap(self, name: str, tm_index: int, bank: int = 0) -> None:
        """Register a tilemap entry.

        要件: Associate a name with a Pyxel tilemap index.
        前提: Tilemap is already loaded via ``load_pyxres``.
        戻り値/副作用: Stores tilemap mapping for later lookup.
        """

        self._tilemaps[name] = (bank, tm_index)

    def tilemap_info(self, name: str) -> TilemapInfo:
        """Return tilemap bank and index.

        要件: Retrieve mapping for a registered tilemap.
        前提: ``name`` exists in the registry.
        戻り値/副作用: Returns tuple ``(bank, tm_index)``.
        """

        return self._tilemaps[name]

    def load_atlas(self, path: str) -> None:
        """Load sprite definitions from a CSV atlas.

        要件: Bulk-register sprites defined in a CSV file.
        前提: File uses format ``name,bank,u,v,w,h`` without header.
        戻り値/副作用: Populates the sprite registry.
        """

        with open(path, "r", newline="") as fh:
            reader = csv.reader(fh)
            for row in reader:
                name, bank, u, v, w, h = row
                self.register_sprite(name, int(bank), int(u), int(v), int(w), int(h))
