Ludorium provides a minimal GUI to assist Pyxel game development.

## Setup

```bash
pip install pyxel
```

## Usage

Run the assistant:

```bash
python main.py
```

A window with buttons appears when a display is available. Use it to:

- **Edit Assets** – open `assets/assets.pyxres` in the Pyxel editor.
- **Run** – execute the current project through `scripts/run.py`.
- **Build** – produce a `.pyxapp` package using `scripts/build.py`.
- **Export Web** – generate web files via `scripts/export_web.py`.

If no GUI is available, the script prints a notice and the CLI helpers can be
invoked directly:

```bash
python scripts/run.py
python scripts/build.py
python scripts/export_web.py
```
