import importlib.util
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("main", Path(__file__).resolve().parents[1] / "main.py")
main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main)


def test_run_game_invokes_script():
    with patch("subprocess.run") as run:
        main.run_game()
        run.assert_called_once_with(["python", "scripts/run.py"], check=False)


def test_build_game_invokes_build_script():
    with patch("subprocess.run") as run:
        main.build_game()
        run.assert_called_once_with(["python", "scripts/build.py"], check=False)


def test_export_web_invokes_export_script():
    with patch("subprocess.run") as run:
        main.export_web()
        run.assert_called_once_with(["python", "scripts/export_web.py"], check=False)


def test_edit_assets_invokes_editor():
    with patch("subprocess.run") as run:
        main.edit_assets()
        run.assert_called_once_with(["pyxel", "edit", "assets/assets.pyxres"], check=False)


def test_main_without_display(monkeypatch, capsys):
    monkeypatch.delenv("DISPLAY", raising=False)
    main.main()
    assert "GUI is unavailable" in capsys.readouterr().out
