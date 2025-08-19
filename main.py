"""GUI front-end for Pyxel development tasks."""

from __future__ import annotations

import os
import subprocess
import tkinter as tk


def _run(cmd: list[str]) -> None:
    """Execute a subprocess command without raising errors."""
    try:
        subprocess.run(cmd, check=False)
    except FileNotFoundError as exc:  # pragma: no cover - depends on environment
        print(f"Command not found: {exc}")


def run_game() -> None:
    """Run the current Pyxel project via ``scripts/run.py``."""
    _run(["python", "scripts/run.py"])


def build_game() -> None:
    """Build the project into a ``.pyxapp`` package."""
    _run(["python", "scripts/build.py"])


def export_web() -> None:
    """Export the project for web deployment."""
    _run(["python", "scripts/export_web.py"])


def edit_assets() -> None:
    """Launch the Pyxel asset editor."""
    _run(["pyxel", "edit", "assets/assets.pyxres"])


def main() -> None:
    """Start a simple GUI to access common development tasks."""
    if os.environ.get("DISPLAY") is None and os.name != "nt":
        print("GUI is unavailable in this environment. Use CLI scripts instead.")
        return

    root = tk.Tk()
    root.title("Ludorium Assistant")

    tk.Button(root, text="Edit Assets", command=edit_assets).pack(fill=tk.X)
    tk.Button(root, text="Run", command=run_game).pack(fill=tk.X)
    tk.Button(root, text="Build", command=build_game).pack(fill=tk.X)
    tk.Button(root, text="Export Web", command=export_web).pack(fill=tk.X)

    root.mainloop()


if __name__ == "__main__":
    main()
