import pyxel
from RPG_constants import *
from Pyxel_RPG_title import TitleScene

TILE_SIZE = 8  # 1タイルのサイズ（px）
BLOCKING_TYPES = {TILE_STONE, TILE_HOUSE}  # 進入禁止タイル
COLLECTIBLE_TYPES = {TILE_GEM}  # 収集可能アイテム

# リセットボタンの位置とサイズ
RESET_BTN_X = 190
RESET_BTN_Y = 10
RESET_BTN_W = 50
RESET_BTN_H = 15

# ゲーム画面サイズ
W = 256
H = 256

# プレイヤーサイズ
PW = 16
PH = 16
SPEED = 10

# マップ設定
MAP_W, MAP_H = 512, 512
TM = 0  # タイルマップ番号

def clamp(v, lo, hi):
    return max(lo, min(v, hi))

BG_X = 0
BG_Y = 16
BG_W = 32
BG_H = 32
BG_BANK = 0

SCROLL_BORDER_X = 64
SCROLL_BORDER_Y = 64

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



# 汎用オブジェクト
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
        super().__init__(x, y, 1, 0, 0, PW, PH, 0)
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

    def draw_player(self):
        if self.facing:
            # 右向き（水平反転）: u,vはそのまま。wを負に
            pyxel.blt(self.x, self.y, self.img, self.u, self.v, -self.w, self.h, self.colkey)
        else:
            # 左向き（通常）
            pyxel.blt(self.x, self.y, self.img, self.u, self.v, self.w, self.h, self.colkey)


# メインゲーム
class App:
    def __init__(self):
        pyxel.init(W, H, title="RPG Camera", fps=60)
        pyxel.mouse(True)  # マウスカーソルを表示
        pyxel.load("my_resource.pyxres")
        
        self.cam_x = 0
        self.cam_y = 0

        self.scene = {
            "title" : TitleScene(self),  # タイトルシーン
            "play" : self  # プレイシーン（メインゲーム）
        } #シーンの辞書
        self.scene_name = "title"  # 初期シーン
        self.change_scene(self.scene_name)

        self.player = Player(60, 60)
        self.debug_mode = False  # デバッグモードフラグ
        
        pyxel.run(self.update, self.draw)

    def change_scene(self, scene_name):
        self.scene_name = scene_name
        self.scene[self.scene_name].update()

    def update(self):
        
        if pyxel.btnp(pyxel.KEY_ESCAPE):
            pyxel.quit()
        
        if pyxel.btnp(pyxel.KEY_T):
            if self.scene_name == "play":
                self.scene_name = "title"
                self.scene["title"].alpha = 0.0
            elif self.scene_name == "title":
                self.scene_name = "play"
            return

        # 各シーン固有の更新処理
        if self.scene_name == "title":
            self.scene["title"].update()
        elif self.scene_name == "play": 
            # デバッグモード切り替え
            if pyxel.btnp(pyxel.KEY_D):
                self.debug_mode = not self.debug_mode
            elif self.scene_name == "play":    
                # リセットボタン（Rキー）
                if pyxel.btnp(pyxel.KEY_R):
                    self.reset_game()
                    return  # リセット後は他の処理をスキップ
                
                if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                    mouse_x = pyxel.mouse_x
                    mouse_y = pyxel.mouse_y
                
                    # リセットボタンの範囲内をクリックしたかチェック
                    if (RESET_BTN_X <= mouse_x <= RESET_BTN_X + RESET_BTN_W and
                        RESET_BTN_Y <= mouse_y <= RESET_BTN_Y + RESET_BTN_H):
                        self.reset_game()
                        return  # リセット後は他の処理をスキップ
            
                self.player.update()

                # X方向カメラ追従
                if self.player.x > self.cam_x + W - SCROLL_BORDER_X:
                    self.cam_x = min(self.player.x - (W - SCROLL_BORDER_X), MAP_W - W)
                elif self.player.x < self.cam_x + SCROLL_BORDER_X:
                    self.cam_x = max(self.player.x - SCROLL_BORDER_X, 0)

                # Y方向カメラ追従
                if self.player.y > self.cam_y + H - SCROLL_BORDER_Y:
                    self.cam_y = min(self.player.y - (H - SCROLL_BORDER_Y), MAP_H - H)
                elif self.player.y < self.cam_y + SCROLL_BORDER_Y:
                    self.cam_y = max(self.player.y - SCROLL_BORDER_Y, 0)

    def draw(self):
        if self.scene_name == "title":
            self.scene["title"].draw()
        elif self.scene_name == "play":

            pyxel.cls(3)
            pyxel.camera(self.cam_x, self.cam_y)
            
            # タイルマップを描画（透明色を指定）
            pyxel.bltm(0, 0, 0, 0, 0, 256, 256, colkey=0)
            self.player.draw_player()
            
            # デバッグ情報表示（デバッグモード時）
            if self.debug_mode:
                # プレイヤーの位置と当たり判定を表示
                player_tile_x = self.player.x // TILE_SIZE
                player_tile_y = self.player.y // TILE_SIZE
                tile_type = get_tile_type(self.player.x, self.player.y)
                
                pyxel.text(self.player.x, self.player.y - 10, 
                        f"({player_tile_x},{player_tile_y}) T:{tile_type}", 7)
                
            # デバッグモードの状態表示
            if self.debug_mode:
                pyxel.text(10, H - 10, "DEBUG: ON (D key)", 8)
        
                # 周囲のタイルの当たり判定を可視化
                for y in range(player_tile_y - 2, player_tile_y + 3):
                    for x in range(player_tile_x - 2, player_tile_x + 3):
                        if is_block_at(x * TILE_SIZE, y * TILE_SIZE):
                            pyxel.rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE, 8)
                        # 宝石タイルを緑色で表示
                        if get_tile_type(x * TILE_SIZE, y * TILE_SIZE) == TILE_GEM:
                            pyxel.rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE, 11)
    
            pyxel.camera()  # UI描画のためリセット
            
            # UIの表示
            pyxel.text(10, 10, f"HP: 8", 7)
            pyxel.text(10, 30, f"Gems: {self.player.gems_collected}", 7)

            # リセットボタンの描画
            self.draw_reset_button()

            
            # デバッグモードの状態表示
            if self.debug_mode:
                pyxel.text(10, H - 10, "DEBUG: ON (D key)", 8)

    def draw_reset_button(self):
        """リセットボタンを描画"""
        # ボタンの背景
        pyxel.rect(RESET_BTN_X, RESET_BTN_Y, RESET_BTN_W, RESET_BTN_H, 5)
        
        # ボタンの枠線
        pyxel.rectb(RESET_BTN_X, RESET_BTN_Y, RESET_BTN_W, RESET_BTN_H, 7)
        
        # ボタンのテキスト
        text_x = RESET_BTN_X + 5
        text_y = RESET_BTN_Y + 3
        pyxel.text(text_x, text_y, "Reset R Key", 7)
        
        # マウスがボタン上にあるときはハイライト
        mouse_x = pyxel.mouse_x
        mouse_y = pyxel.mouse_y
        
        if (RESET_BTN_X <= mouse_x <= RESET_BTN_X + RESET_BTN_W and
            RESET_BTN_Y <= mouse_y <= RESET_BTN_Y + RESET_BTN_H):
            # ハイライト表示
            pyxel.rectb(RESET_BTN_X - 1, RESET_BTN_Y - 1, RESET_BTN_W + 2, RESET_BTN_H + 2, 10)   

    def reset_game(self):
        """ゲームをリセットする関数"""
        # プレイヤーの初期位置と状態をリセット
        self.player.x = 60  # 初期X座標
        self.player.y = 60  # 初期Y座標
        self.player.gems_collected = 0  # 収集した宝石をリセット
        
        # カメラ位置をリセット
        self.cam_x = 0
        self.cam_y = 0
        
        # タイルマップをリロード（宝石などを元に戻す）
        pyxel.load("my_resource.pyxres")


App()