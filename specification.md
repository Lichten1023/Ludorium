# Pyxel 統合開発環境（Ludorium）詳細設計書（実装手順つき）

## 0. ゴール/非ゴール

* **ゴール**

  * Pyxel上で**とっつきやすく**ゲームを作るための薄い統合フレームワーク（以後 Ludorium）。
  * 即時描画のダルさを解消：**保持型スプライト管理・Z/レイヤ順制御・シーン管理・入力抽象化・アセット名解決・TTL/スケジューラ・簡易アニメ**を提供。
  * **1ファイルから始められ**、規模拡大で素直に分割できる。
  * **Pyxel準拠ビルド**（`.pyxapp`）と**Webエクスポート**（Pyxel Web）をワンコマンド化。
* **非ゴール**

  * ノーコード完結（Scratch級の完全GUI）は対象外。コードベースを基盤に**設計支援**を厚くする。
  * ECS/物理/ネットワーク等の重量級は範囲外。必要十分に留める。

---

## 1. 環境・規約

* Python >= 3.10 / Pyxel 最新安定（1.8+想定）
* 依存：原則 Pyxel のみ（任意ツールは `tools/` 下に同梱）。
* 画面：**仮想解像度**をプロジェクト作成時に固定（例：160×144, 256×144 など）。整数拡大前提。
* コーディング規約：

  * クラス名：**PascalCase**（あなたの嗜好に合わせる）
  * 関数/変数：snake\_case
  * 型ヒント必須、docstringは**要件→前提→戻り値/副作用**の順
* ディレクトリ（初期）：

  ```
  my_game/
  ├─ main.py
  ├─ engine/
  │   ├─ scene_manager.py
  │   ├─ scene.py
  │   ├─ input.py
  │   ├─ assets.py
  │   ├─ sprite.py
  │   ├─ animation.py
  │   ├─ scheduler.py
  │   ├─ camera.py
  │   └─ layers.py
  ├─ scenes/
  │   ├─ title_scene.py
  │   └─ game_scene.py
  ├─ assets/
  │   ├─ assets.pyxres
  │   └─ atlas.csv        # 任意：名前→UV対応
  ├─ config/
  │   ├─ game.json        # 画面/タイトル/FPSなど
  │   └─ keymap.json      # 入力マップ
  ├─ scripts/
  │   ├─ run.py           # 実行
  │   ├─ build.py         # .pyxapp
  │   └─ export_web.py    # web出力
  └─ README.md
  ```

---

## 2. 機能ブロック設計（API仕様）

### 2.1 Scene / SceneManager

* 目的：**状態遷移と画面ごとの責務分離**。
* `class Scene`（抽象基底）

  * `app: App | None`（実行時に注入）
  * ライフサイクル：`on_enter(data: dict|None) -> None`, `on_exit() -> None`
  * ゲームループ：`update(dt: float) -> None`, `draw() -> None`
  * 便宜：`change_scene(scene: Scene, data: dict|None=None) -> None`（Manager経由）
* `class SceneManager`

  * `start(initial: Scene) -> None`
  * `change(next_scene: Scene, data: dict|None=None) -> None`
  * `update(dt: float) -> None`, `draw() -> None`
  * **単一アクティブ**（スタックは持たない；必要なら将来拡張）

**完了条件**：タイトル→ゲームへ遷移可能。
**検証**：SPACE押下でシーン切替・`on_enter`が一度だけ呼ばれる。

---

### 2.2 Input（入力抽象）

* 目的：キー/パッド/マウスを**論理名**で扱う。Pyxel依存を隠蔽。
* `class Input`

  * 初期化時に `keymap: dict[str, list[int]]` を受け取る（key code 配列）
  * `pressed(name: str) -> bool`（長押し）
  * `triggered(name: str) -> bool`（**立ち上がり**）
  * `released(name: str) -> bool`（立ち下がり）
  * `update() -> None`（前フレーム状態保持）
* 既定マップ（config/keymap.json）例：

  ```json
  {
    "UP": ["KEY_UP","GAMEPAD1_UP"],
    "DOWN": ["KEY_DOWN","GAMEPAD1_DOWN"],
    "LEFT": ["KEY_LEFT","GAMEPAD1_LEFT"],
    "RIGHT": ["KEY_RIGHT","GAMEPAD1_RIGHT"],
    "START": ["KEY_SPACE","GAMEPAD1_START"],
    "A": ["KEY_Z","GAMEPAD1_A"],
    "B": ["KEY_X","GAMEPAD1_B"]
  }
  ```

**完了条件**：論理名で押下/トリガ判定が動く。
**検証**：`Input.triggered("START")`で1回だけTrue。

---

### 2.3 Assets（アセット名解決）

* 目的：**名前で**スプライト・タイル・音を引ける。
* `class AssetRegistry`

  * `load_pyxres(path: str) -> None`（`pyxel.load` もここで呼ぶ）
  * `register_sprite(name: str, bank: int, u: int, v: int, w: int, h: int) -> None`
  * `sprite_uv(name: str) -> tuple[int,int,int,int,int]`
  * `register_tilemap(name: str, tm_index: int, bank: int=0) -> None`
  * `tilemap_info(name: str) -> tuple[int,int]`  # (bank, tm\_index)
  * **CSV読込**：`load_atlas_csv(path: str) -> None`（`name,bank,u,v,w,h`）
* 音は最小：`play_sfx(name)`, `play_bgm(name, loop=True)` の**薄いラッパ**で十分（内部は番号対応でも良い）。

**完了条件**：`"player"`等の名前で `pyxel.blt` に必要なUV/バンクが取れる。
**検証**：`assets.register_sprite("logo",0,0,0,32,16)`→描画OK。

---

### 2.4 Layers / Camera / Zソート

* `class LayerDef(name: str, zbase: int, parallax: float=1.0, camera_affine: bool=True)`
* `class Layers`

  * 既定：`bg(zbase=0, parallax=0.5)`, `main(100,1.0)`, `ui(1000, camera_affine=False)`
  * `get(name) -> LayerDef`
* `class Camera`

  * `x: int=0; y: int=0`
* **ソートキー**：`(layer.zbase, sprite.z, sprite.order)` 安定ソート。

**完了条件**：背景→本体→UIの順で正しく重なる。
**検証**：UIはカメラ非追従で固定表示。

---

### 2.5 SpriteManager（保持・消去・重なり）

* 目的：**spawn/move/kill/ttl** を提供し、**毎フレ生存物のみ描画**。
* `@dataclass class Sprite`

  * `alive: bool, name: str, x: int, y: int, z: int, layer: str="main"`
  * `visible: bool=True, ttl: float=-1.0, order: int, colkey: int|None=0`
* `class SpriteManager`

  * `spawn(name,x,y,*,z=0,layer="main",ttl=-1.0,visible=True,colkey=0) -> int`
  * `move(id, x=None, y=None, dx=0, dy=0) -> None`
  * `set(id, *, z=None, layer=None, visible=None, name=None) -> None`
  * `kill(id) -> None`
  * `update(dt) -> None`（TTL減算→自動kill）
  * `flush_and_draw(camera: Camera, layers: Layers, assets: AssetRegistry) -> None`
* **カリング**：初版は省略（必要時に矩形視口カリングを追加）。

**完了条件**：**kill/visible/ttl**が効く。Z/Layer順で安定。
**検証**：火花エフェクトを`ttl=0.2`で自動消滅。

---

### 2.6 Animation（フレーム切替）

* `class Animation`

  * `def __init__(self, frames: list[str], fps: float, loop=True, pingpong=False)`
  * `advance(dt) -> None`（内部time累積）
  * `current() -> str`（現在フレームの**スプライト名**）
* 使い方：`name = anim.current(); sm.set(id, name=name)`

**完了条件**：一定fpsで名前が切替る。
**検証**：歩行2枚の交互表示。

---

### 2.7 Scheduler（遅延実行/反復）

* `class Scheduler`

  * `after(delay: float, fn: Callable, *args, **kwargs) -> Handle`
  * `every(interval: float, fn: Callable, *, repeat: int|None=None) -> Handle`
  * `cancel(handle: Handle) -> None`
  * `update(dt) -> None`
* **Booker相当**の最低限（多段タイマを排除）。

**完了条件**：N秒後発火/毎秒発火/キャンセル動作。
**検証**：3回だけ実行→停止。

---

### 2.8 Map（最小）

* 方針：**Pyxel Editorのタイルマップ**を使う。
* `draw_tilemap(name: str, mx: int, my: int, sx: int, sy: int, w: int, h: int, *, layer="bg", z=0)`

  * 内部は `pyxel.bltm`。**視口だけ**を切り出す（将来最適化枠）。

**完了条件**：マップ一枚をBGに表示、カメラ連動。
**検証**：カメラ x/y 変更でスクロール。

---

### 2.9 App（ゲームエントリ）

* `class App`

  * `__init__(config_path: str)`

    * `pyxel.init(w,h,title,fps)`
    * `assets.load_pyxres("assets/assets.pyxres")`
    * `assets.load_atlas_csv("assets/atlas.csv")`（任意）
    * `input = Input(keymap)`
    * `scene_manager.start(TitleScene())`
    * `pyxel.run(self._update, self._draw)`
  * `_update()`：`dt=1/fps`で `input.update()`, `scheduler.update(dt)`, `scene_manager.update(dt)`
  * `_draw()`：`pyxel.cls(0)`, `scene_manager.draw()`

**完了条件**：起動→タイトルシーン実行。
**検証**：クラッシュ/ちらつき無し。

---

## 3. 参照コード骨格（Codexにそのまま生成させる）

> **注意**：ここでは**最小スケルトン**のみ。Codexには各ファイルの内容として吐かせること。

### 3.1 `engine/scene.py`

```python
from __future__ import annotations
from typing import Optional

class Scene:
    def __init__(self) -> None:
        self.app: Optional["App"] = None
        self.manager: Optional["SceneManager"] = None

    def on_enter(self, data: dict | None = None) -> None: ...
    def on_exit(self) -> None: ...
    def update(self, dt: float) -> None: ...
    def draw(self) -> None: ...

    def change_scene(self, scene: "Scene", data: dict | None = None) -> None:
        assert self.manager is not None
        self.manager.change(scene, data)
```

### 3.2 `engine/scene_manager.py`

```python
from __future__ import annotations
from typing import Optional
from .scene import Scene

class SceneManager:
    def __init__(self) -> None:
        self._current: Optional[Scene] = None
        self._pending: Optional[tuple[Scene, dict | None]] = None

    def start(self, scene: Scene, app: "App") -> None:
        self._current = scene
        self._current.app = app
        self._current.manager = self
        self._current.on_enter()

    def change(self, next_scene: Scene, data: dict | None = None) -> None:
        self._pending = (next_scene, data)

    def _commit_change(self, app: "App") -> None:
        if not self._pending: return
        assert self._current is not None
        self._current.on_exit()
        next_scene, data = self._pending
        self._current = next_scene
        self._current.app = app
        self._current.manager = self
        self._pending = None
        self._current.on_enter(data)

    def update(self, app: "App", dt: float) -> None:
        assert self._current is not None
        self._current.update(dt)
        self._commit_change(app)

    def draw(self) -> None:
        assert self._current is not None
        self._current.draw()
```

### 3.3 `engine/input.py`

```python
from __future__ import annotations
import pyxel
from typing import Dict, List, Set

def _keycode(name: str) -> int:
    # 例: "KEY_SPACE" -> pyxel.KEY_SPACE
    return getattr(pyxel, name)

class Input:
    def __init__(self, keymap: Dict[str, List[str]]) -> None:
        self.map: Dict[str, List[int]] = {k: [_keycode(n) for n in v] for k, v in keymap.items()}
        self._pressed_prev: Set[int] = set()

    def update(self) -> None:
        now: Set[int] = set()
        for codes in self.map.values():
            for c in codes:
                if pyxel.btn(c):
                    now.add(c)
        self._pressed_prev, self._pressed_now = self._pressed_now if hasattr(self,"_pressed_now") else set(), now

    def _any(self, name: str, fn) -> bool:
        return any(fn(c) for c in self.map.get(name, []))

    def pressed(self, name: str) -> bool:
        return self._any(name, pyxel.btn)

    def triggered(self, name: str) -> bool:
        return self._any(name, pyxel.btnp)

    def released(self, name: str) -> bool:
        return self._any(name, pyxel.btnr)
```

### 3.4 `engine/layers.py`・`engine/camera.py`

```python
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class LayerDef:
    name: str
    zbase: int
    parallax: float = 1.0
    camera_affine: bool = True

class Layers:
    def __init__(self) -> None:
        self.defs = {
            "bg": LayerDef("bg", 0, 0.5, True),
            "main": LayerDef("main", 100, 1.0, True),
            "ui": LayerDef("ui", 1000, 0.0, False),
        }
    def get(self, name: str) -> LayerDef:
        return self.defs[name]
```

```python
class Camera:
    def __init__(self) -> None:
        self.x = 0
        self.y = 0
```

### 3.5 `engine/assets.py`

```python
from __future__ import annotations
import csv, pyxel
from typing import Dict, Tuple

SpriteUV = Tuple[int,int,int,int,int]  # u,v,w,h,bank

class AssetRegistry:
    def __init__(self) -> None:
        self._sprites: Dict[str, SpriteUV] = {}
        self._tilemaps: Dict[str, Tuple[int,int]] = {}  # name -> (bank, tm_index)

    def load_pyxres(self, path: str) -> None:
        pyxel.load(path)

    def load_atlas_csv(self, path: str) -> None:
        with open(path, newline="", encoding="utf-8") as f:
            for name, bank, u, v, w, h in csv.reader(f):
                self.register_sprite(name, int(bank), int(u), int(v), int(w), int(h))

    def register_sprite(self, name: str, bank: int, u: int, v: int, w: int, h: int) -> None:
        self._sprites[name] = (u,v,w,h,bank)

    def sprite_uv(self, name: str) -> SpriteUV:
        return self._sprites[name]

    def register_tilemap(self, name: str, tm_index: int, bank: int = 0) -> None:
        self._tilemaps[name] = (bank, tm_index)

    def tilemap_info(self, name: str) -> Tuple[int,int]:
        return self._tilemaps[name]
```

### 3.6 `engine/sprite.py`

```python
from __future__ import annotations
import pyxel
from dataclasses import dataclass
from typing import List
from .layers import Layers
from .camera import Camera
from .assets import AssetRegistry

@dataclass
class Sprite:
    alive: bool = False
    name: str = ""
    x: int = 0
    y: int = 0
    z: int = 0
    layer: str = "main"
    visible: bool = True
    ttl: float = -1.0
    order: int = 0
    colkey: int | None = 0

class SpriteManager:
    def __init__(self) -> None:
        self._items: List[Sprite] = []
        self._free: List[int] = []
        self._order_counter = 0

    def spawn(self, name: str, x: int, y: int, *, z: int = 0, layer: str = "main",
              ttl: float = -1.0, visible: bool = True, colkey: int | None = 0) -> int:
        if self._free:
            i = self._free.pop()
            s = self._items[i]
        else:
            i = len(self._items)
            self._items.append(Sprite())
            s = self._items[i]
        s.alive = True
        s.name, s.x, s.y, s.z, s.layer = name, int(x), int(y), int(z), layer
        s.ttl, s.visible, s.colkey = float(ttl), bool(visible), colkey
        s.order = self._order_counter; self._order_counter += 1
        return i

    def move(self, sid: int, x: int | None = None, y: int | None = None, dx: int = 0, dy: int = 0) -> None:
        s = self._items[sid]
        if x is not None: s.x = int(x)
        if y is not None: s.y = int(y)
        if dx or dy: s.x += int(dx); s.y += int(dy)

    def set(self, sid: int, *, z: int | None = None, layer: str | None = None,
            visible: bool | None = None, name: str | None = None) -> None:
        s = self._items[sid]
        if z is not None: s.z = int(z)
        if layer is not None: s.layer = layer
        if visible is not None: s.visible = bool(visible)
        if name is not None: s.name = name

    def kill(self, sid: int) -> None:
        s = self._items[sid]
        if s.alive:
            s.alive = False
            self._free.append(sid)

    def update(self, dt: float) -> None:
        if dt <= 0: return
        for i, s in enumerate(self._items):
            if not s.alive: continue
            if s.ttl >= 0:
                s.ttl -= dt
                if s.ttl <= 0:
                    self.kill(i)

    def flush_and_draw(self, camera: Camera, layers: Layers, assets: AssetRegistry) -> None:
        buf = []
        for s in self._items:
            if not (s.alive and s.visible): continue
            ly = layers.get(s.layer)
            x, y = s.x, s.y
            if ly.camera_affine:
                x -= int(camera.x * ly.parallax)
                y -= int(camera.y * ly.parallax)
            zkey = (ly.zbase, s.z, s.order)
            buf.append((zkey, s, x, y))
        buf.sort(key=lambda t: t[0])
        for _, s, x, y in buf:
            u,v,w,h,bank = assets.sprite_uv(s.name)
            pyxel.blt(x, y, bank, u, v, w, h, s.colkey if s.colkey is not None else 0)
```

### 3.7 `engine/animation.py`

```python
class Animation:
    def __init__(self, frames: list[str], fps: float, loop: bool = True, pingpong: bool = False) -> None:
        self.frames = frames
        self.fps = fps
        self.loop = loop
        self.pingpong = pingpong
        self.time = 0.0
        self._dir = 1

    def advance(self, dt: float) -> None:
        self.time += dt
        # 単純: time→frame index
        tot = len(self.frames)
        if tot <= 1: return
        framef = self.time * self.fps
        if self.pingpong:
            span = (tot - 1) * 2
            idx = int(framef) % span
            if idx >= tot:
                idx = span - idx
            self._idx = idx
        else:
            idx = int(framef)
            if self.loop:
                self._idx = idx % tot
            else:
                self._idx = min(idx, tot - 1)

    def current(self) -> str:
        return self.frames[getattr(self, "_idx", 0)]
```

### 3.8 `engine/scheduler.py`

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Optional, List

@dataclass
class _Task:
    t: float
    interval: float
    fn: Callable
    repeat: Optional[int]
    cancelled: bool = False

class Scheduler:
    def __init__(self) -> None:
        self._now = 0.0
        self._tasks: List[_Task] = []

    def after(self, delay: float, fn: Callable, *args, **kwargs) -> _Task:
        def _wrap():
            fn(*args, **kwargs)
        task = _Task(self._now + delay, 0.0, _wrap, repeat=1)
        self._tasks.append(task)
        return task

    def every(self, interval: float, fn: Callable, *, repeat: int | None = None, *args, **kwargs) -> _Task:
        def _wrap():
            fn(*args, **kwargs)
        task = _Task(self._now + interval, interval, _wrap, repeat=repeat)
        self._tasks.append(task)
        return task

    def cancel(self, task: _Task) -> None:
        task.cancelled = True

    def update(self, dt: float) -> None:
        self._now += dt
        for task in list(self._tasks):
            if task.cancelled: 
                self._tasks.remove(task); continue
            if self._now >= task.t:
                task.fn()
                if task.repeat is None or task.repeat > 1:
                    task.t += (task.interval or 0.0)
                    if task.repeat is not None: task.repeat -= 1
                else:
                    self._tasks.remove(task)
```

### 3.9 `scenes/title_scene.py`（最小例）

```python
from __future__ import annotations
import pyxel
from engine.scene import Scene

class TitleScene(Scene):
    def on_enter(self, data=None) -> None:
        self.t = 0

    def update(self, dt: float) -> None:
        self.t += 1
        if pyxel.btnp(pyxel.KEY_SPACE):
            from .game_scene import GameScene
            self.change_scene(GameScene())

    def draw(self) -> None:
        pyxel.text(50, 40, "MY GAME", 7 if (self.t//15)%2==0 else 6)
        pyxel.text(38, 80, "- PRESS SPACE TO START -", 11)
```

### 3.10 `scenes/game_scene.py`（SpriteManager連携）

```python
from __future__ import annotations
import pyxel
from engine.scene import Scene
from engine.camera import Camera
from engine.layers import Layers
from engine.sprite import SpriteManager

class GameScene(Scene):
    def on_enter(self, data=None) -> None:
        self.cam = Camera()
        self.layers = Layers()
        self.sm = SpriteManager()
        self.player = self.sm.spawn("player", 80, 64, z=10)
        self.vx = self.vy = 0

    def update(self, dt: float) -> None:
        dx = (pyxel.btn(pyxel.KEY_RIGHT) - pyxel.btn(pyxel.KEY_LEFT))
        dy = (pyxel.btn(pyxel.KEY_DOWN) - pyxel.btn(pyxel.KEY_UP))
        self.sm.move(self.player, dx=dx, dy=dy)
        px = self.sm._items[self.player].x
        py = self.sm._items[self.player].y
        self.cam.x = px - 80; self.cam.y = py - 72
        if pyxel.btnp(pyxel.KEY_SPACE):
            self.sm.spawn("spark", px+8, py-4, z=20, ttl=0.2)
        self.sm.update(dt)

    def draw(self) -> None:
        pyxel.cls(0)
        self.sm.flush_and_draw(self.cam, self.layers, self.app.assets)  # type: ignore
        pyxel.text(4,4,"ARROWS TO MOVE / SPACE SPARK",7)
```

### 3.11 `main.py`

```python
from __future__ import annotations
import json, pyxel
from engine.scene_manager import SceneManager
from engine.assets import AssetRegistry
from scenes.title_scene import TitleScene

class App:
    def __init__(self) -> None:
        with open("config/game.json","r",encoding="utf-8") as f:
            cfg = json.load(f)
        pyxel.init(cfg["width"], cfg["height"], title=cfg.get("title","Ludorium"), fps=cfg.get("fps",60))
        self.assets = AssetRegistry()
        self.assets.load_pyxres("assets/assets.pyxres")
        try:
            self.assets.load_atlas_csv("assets/atlas.csv")
        except FileNotFoundError:
            pass
        self.smgr = SceneManager()
        self.smgr.start(TitleScene(), self)
        pyxel.run(self._update, self._draw)

    def _update(self) -> None:
        dt = 1/pyxel.frame_rate
        self.smgr.update(self, dt)

    def _draw(self) -> None:
        self.smgr.draw()

if __name__ == "__main__":
    App()
```

---

## 4. スクリプト化（run/build/web）

* `scripts/run.py`：`python -m pyxel play`は不要。**開発中は `python main.py`** で十分。
* `scripts/build.py`：

  ```python
  import subprocess, sys, pathlib
  root = pathlib.Path(__file__).resolve().parents[1]
  subprocess.check_call(["pyxel","package", str(root), str(root/"main.py")])
  print("-> build: main.pyxapp")
  ```
* `scripts/export_web.py`：`main.pyxapp` を `dist/web/` に配置し、Pyxel Web Loader 用の最小 `index.html` を生成（テンプレは固定文字列でOK）。

**完了条件**：`python scripts/build.py`で`main.pyxapp`生成、Web出力も生成。
**検証**：`pyxel play main.pyxapp`が起動、`dist/web/index.html` をブラウザで開いて動作。

---

## 5. 設定ファイル例

* `config/game.json`

  ```json
  { "title": "Ludorium Sample", "width": 160, "height": 144, "fps": 60 }
  ```
* `assets/atlas.csv`

  ```
  player,0,0,16,16,16
  spark,0,32,16,8,8
  logo,0,0,0,32,16
  ```

---

## 6. 実装ステップ（Codex向け命令書）

**Step 0: プロジェクト雛形生成**

* 上述ディレクトリを作成。`README.md` に起動手順を書く。
* `config/game.json`、`assets/atlas.csv` の雛形を作る。
* **受入**：`python main.py`がエラー無く終了（まだ画面不要）。

**Step 1: Scene/SceneManager 実装**

* `engine/scene.py`/`scene_manager.py`を作成。`scenes/title_scene.py` 最小版。
* **受入**：タイトル表示・SPACEで `print("go")` 程度の確認。

**Step 2: Assets 実装**

* `engine/assets.py` を作り、`pyxel.load()` と `register_sprite()` を動かす。
* **受入**：`assets.register_sprite("logo",0,0,0,32,16)` で `pyxel.blt` 成功。

**Step 3: Layers / Camera**

* 既定3レイヤを提供。Cameraで座標オフセット。
* **受入**：UIテキストがカメラ非追従。

**Step 4: SpriteManager**

* `spawn/move/kill/ttl` と `flush_and_draw`。
* **受入**：重なり順が z/layer/order で安定、`ttl`で自動消滅。

**Step 5: Animation**

* 2～3枚の歩行アニメを回す。
* **受入**：`advance()`で `current()` が切り替わる。

**Step 6: Scheduler**

* `after/every/cancel/update`。
* **受入**：3回反復→停止、キャンセルが効く。

**Step 7: GameScene 最小実装**

* 矢印移動/SPACEで火花、カメラ追尾。
* **受入**：想定通り動く。クラッシュなし。

**Step 8: Map（任意）**

* `assets.register_tilemap("stage1", tm_index=0)` → `pyxel.bltm` で視口表示。
* **受入**：カメラ移動でスクロール。

**Step 9: スクリプト（build/export\_web）**

* .pyxapp生成とWeb出力テンプレ生成。
* **受入**：`pyxel play main.pyxapp` と `dist/web/index.html` 動作。

**Step 10: 清掃/最適化**

* クリティカルパスはローカル変数化・不要アロケーション削減。
* **受入**：60FPS維持（小規模でOK）。

---

## 7. テスト観点（手動/最小自動）

* **Scene遷移**：`on_enter`/`on_exit`が1回ずつ。
* **入力**：押しっぱなしとトリガの差が出る。
* **スプライト**：kill→表示消滅、visible=False→非表示維持、ttlで自動消滅。
* **並び順**：`bg < main < ui`、同layer内はz昇順・同値はorderで安定。
* **カメラ**：bgは視差、uiは固定。
* **アニメ**：fps変更で速度が変わる。
* **スケジューラ**：after/every/cancelの全パス。
* **ビルド**：`.pyxapp` 起動、Web出力起動。

---

## 8. パフォーマンス・拡張

* **ソート負荷**：1フレームのスプライト数が増えたら**バケット分け**（layer別の小ソート）推奨。
* **カリング**：画面外スプライトは `flush_and_draw` で弾く（`x+w<0 || x>width ...`）。
* **タイル**：`bltm` は視口矩形に限定。巨大マップは**チャンク単位**に。
* **将来拡張**：UIウィジェット、当たり判定グリッド、簡易イベントDSL、Tiled(.tmx)インポータなど。

---

## 9. 既定アセット規約（簡素）

* **透明色**：0（黒）運用 or `colkey` 指定で透過。
* **atlas.csv**：`name,bank,u,v,w,h`（ヘッダ無し）。半角カンマ区切り。
* **tilemap**：`tm_index` は Pyxel Editorでの順。`assets.register_tilemap("stage1",0)` のように手で対応。

---

## 10. README ひな型（要自動生成）

* セットアップ：`pip install pyxel`
* 実行：`python main.py`
* ビルド：`python scripts/build.py` → `main.pyxapp`
* Web出力：`python scripts/export_web.py` → `dist/web/index.html`
* 開発：`assets/assets.pyxres` を `pyxel edit assets/assets.pyxres` で編集

---

## 11. 受入サンプル（最低限の動く絵）

* タイトル：点滅ロゴ、SPACEで遷移。
* ゲーム：矢印で16×16の`player`を移動、SPACEで`spark`生成→`ttl=0.2`で消滅。
* UI：左上テキスト固定表示。
* 60FPSで安定。