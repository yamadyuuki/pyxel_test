import pyxel

TILE_NONE = 0
TILE_STONE = 1
TILE_GEM = 2
TILE_HOUSE = 3

TILE_TO_TILETYPE = {
    (4, 0): TILE_STONE,
    (5, 0): TILE_GEM,
    (4, 2): TILE_HOUSE,
    (5, 2): TILE_HOUSE,
    (4, 3): TILE_HOUSE,
    (5, 3): TILE_HOUSE,
}

TILE_SIZE = 8
BLOCKING_TYPES = {TILE_STONE, TILE_HOUSE}
COLLECTIBLE_TYPES = {TILE_GEM}

# ゲーム画面サイズ
W = 256
H = 256

# プレイヤーサイズ
PW = 16
PH = 16
SPEED = 1

# マップ設定
MAP_W, MAP_H = 512, 512

def clamp(v, lo, hi):
    return max(lo, min(v, hi))

def get_tile_type(x, y):
    """ワールド座標(x,y)にあるタイルタイプを返す"""
    tx = x // TILE_SIZE
    ty = y // TILE_SIZE
    tile = pyxel.tilemaps[0].pget(tx, ty)  # (u, v) タプル
    return TILE_TO_TILETYPE.get(tile, TILE_NONE)

def set_tile_empty(x, y):
    """指定座標のタイルを空に設定"""
    tx = x // TILE_SIZE
    ty = y // TILE_SIZE
    pyxel.tilemaps[0].pset(tx, ty, (0, 0))  # 空のタイルに設定

def is_block_at(x, y):
    """その座標にブロックタイルがあるか"""
    tile_type = get_tile_type(x, y)
    
    # 通常のブロック判定
    if tile_type in BLOCKING_TYPES:
        return True
    
    # 家の特別判定: 家は16x16ピクセル（2x2タイル）なので
    # 家タイルの左上から1タイル分の範囲も進入禁止とする
    # タイルマップ上の位置を計算
    tx, ty = x // TILE_SIZE, y // TILE_SIZE
    
    return False

def rect_hits_block(x, y, w, h):
    """矩形がブロックタイルに重なっているか（四隅チェック）"""
    return (
        is_block_at(x,         y        ) or
        is_block_at(x + w - 1, y        ) or
        is_block_at(x,         y + h - 1) or
        is_block_at(x + w - 1, y + h - 1)
    )

def _move_axis_pushback(x, y, w, h, delta, axis):
    """
    axis: 'x' or 'y'
    delta: 目標移動量（正負のfloat）
    1pxずつ進め、ブロックに当たったらそこで止める
    """
    if delta == 0:
        return x, y

    # 何pxぶん進めるか（小数でも天井切り上げで確実に回数を回す）
    steps = pyxel.ceil(abs(delta))
    # 1ステップの符号（+1 or -1）
    step = 1 if delta > 0 else -1

    for _ in range(steps):
        nx, ny = x, y
        if axis == 'x':
            nx = x + step
        else:
            ny = y + step

        # マップ外に出ないようクランプ
        nx = clamp(nx, 0, MAP_W - w)
        ny = clamp(ny, 0, MAP_H - h)

        # 次の位置で衝突するか？
        if rect_hits_block(nx, ny, w, h):
            # ここでストップ（これ以上は進めない）
            break

        # 衝突しなければ1px進める
        x, y = nx, ny

    return x, y

def rect_move(x, y, w, h, dx, dy):
    """
    連続衝突検出（push-back）版の移動。
    まずY軸方向に1pxずつ進め、衝突したら止める。
    次にX軸方向も同様に進める。
    """
    # --- Y軸を先に処理 ---
    x, y = _move_axis_pushback(x, y, w, h, dy, axis='y')
    # --- X軸を次に処理 ---
    x, y = _move_axis_pushback(x, y, w, h, dx, axis='x')
    return x, y


class Scene:
    def __init__(self, app): self.app = app
    def on_enter(self, **kwargs): pass  # 遷移直後に呼ばれる
    def on_exit(self): pass             # 遷移直前に呼ばれる
    def update(self): pass
    def draw(self): pass

class TitleScene(Scene):
    def update(self):
        if pyxel.btnp(pyxel.KEY_SPACE):
            self.app.scenes.change("play", stage=1)  # 例:引数で初期値渡し

    def draw(self):
        pyxel.cls(1)
        pyxel.text(100, 100, "PRESS SPACE", 7)

class GameObject:
    def __init__(self, x, y, img, u, v, w, h, colkey=0):
        self.x = x
        self.y = y
        self.img = img
        self.u = u
        self.v = v
        self.w = w
        self.h = h
        self.colkey = colkey
    
    def draw(self):
        pyxel.blt(self.x, self.y, self.img, self.u, self.v, self.w, self.h, self.colkey)

# プレイヤー
class Player(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y, 0, 16, 0, 16, 16, 0)
        self.facing = False  # false: 左向き, true: 右向き
        self.gems_collected = 0  # 収集した宝石の数

    def update(self):
        dx = (pyxel.btn(pyxel.KEY_RIGHT) - pyxel.btn(pyxel.KEY_LEFT)) * SPEED
        dy = (pyxel.btn(pyxel.KEY_DOWN) - pyxel.btn(pyxel.KEY_UP)) * SPEED
            #右向き
        if dx > 0:
            self.facing = True
            #左向き
        elif dx < 0:
            self.facing = False

        # 衝突判定
        self.x, self.y = rect_move(self.x, self.y, self.w, self.h, dx, dy)      
        # 宝石などのアイテム収集判定
        self.check_item_collection()

    def check_item_collection(self):
        """プレイヤーの周囲のアイテム収集判定"""
        # プレイヤーの周囲8点をチェック
        for i in [0, 7, 15]:  # 上端、中央、下端
            for j in [0, 7, 15]:  # 左端、中央、右端
                check_x = self.x + j
                check_y = self.y + i
                tile_type = get_tile_type(check_x, check_y)
                
                # 宝石の場合
                if tile_type == TILE_GEM:
                    # 宝石を収集（タイルを空に設定）
                    set_tile_empty(check_x, check_y)
                    self.gems_collected += 1
                    pyxel.play(0,2)  # 効果音再生（チャンネル0、サウンド0）

    def draw(self):
        if self.facing:
            # 右向き（水平反転）: u,vはそのまま。wを負に
            pyxel.blt(self.x, self.y, self.img, self.u, self.v, self.w, self.h, self.colkey)
        else:
            # 左向き（通常）
            pyxel.blt(self.x, self.y, self.img, self.u, self.v, -self.w, self.h, self.colkey)

class PlayScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.player = None
        self.cam_x = 0
        self.cam_y = 0

    def on_enter(self, stage=1):
        self.stage = stage
        self.player = Player(100, 100)  # プレイヤーを画面中央付近に配置

    def update(self):
        if pyxel.btnp(pyxel.KEY_R):
            self.app.scenes.change("title")

        if self.player:
            self.player.update()

            # --- カメラをプレイヤーへ追従 ---
            # 画面中央にプレイヤーが来るように（微調整で +PW//2 なども可）
            target_x = self.player.x - W // 2 + self.player.w // 2
            target_y = self.player.y - H // 2 + self.player.h // 2

            # マップ外に出ないようクランプ
            # MAP_W/H は "ワールドのピクセル幅/高さ"
            self.cam_x = clamp(target_x, 0, MAP_W - W)
            self.cam_y = clamp(target_y, 0, MAP_H - H)

    def draw(self):
        pyxel.cls(1)
        # 画面256x256pxを覆うだけのタイル数
        tile_w = 256 // 8  # 32
        tile_h = 256 // 8  # 32
        # タイルマップ0の(0,0)から 32x32 タイルぶんを (0,0) に描画
        pyxel.bltm(0, 0, 0, 0, 0, tile_w, tile_h)

        # --- 1) マップを貼る（カメラに合わせて）---
        u = self.cam_x // TILE_SIZE
        v = self.cam_y // TILE_SIZE
        ox = -(self.cam_x % TILE_SIZE)  # sub-tile オフセット
        oy = -(self.cam_y % TILE_SIZE)

        tile_w = (W // TILE_SIZE) + 2  # 端のはみ出しに+1〜2しておく
        tile_h = (H // TILE_SIZE) + 2

        pyxel.bltm(ox, oy, 0, u, v, tile_w, tile_h)

        # --- 2) プレイヤーを“画面座標”で描く ---
        # ワールド座標からカメラ分を引く
        sx = self.player.x - self.cam_x
        sy = self.player.y - self.cam_y

        # プレイヤーの左右反転を維持したまま描画
        if self.player.facing:
            pyxel.blt(sx, sy, self.player.img, self.player.u, self.player.v,
                      self.player.w, self.player.h, self.player.colkey)
        else:
            pyxel.blt(sx, sy, self.player.img, self.player.u, self.player.v,
                      -self.player.w, self.player.h, self.player.colkey)

