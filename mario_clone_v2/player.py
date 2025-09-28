# player.py
import pyxel as px
from constants import SPEED, GRAVITY, JUMP_POWER, MAX_FALL_SPEED, AIR_CONTROL
from system import rect_move
from system import rect_hits_block  # 足元判定に使う
from system import check_item_collection

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
        px.blt(self.x, self.y, self.img, self.u, self.v, self.w, self.h, self.colkey)

class Player(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y, 0, 16, 0, 16, 16, 0)
        self.facing = True   # false: 左向き, true: 右向き
        self.vy = 0.0        # 縦速度（+は下向き）
        self.on_ground = False
        self.gems_collected = 0

    def _check_on_ground(self, x, y):
        """足元1pxにブロックがあるかで接地判定"""
        return rect_hits_block(x, y + 1, self.w, self.h)

    def update(self):
        # --- 横入力 ---
        move = (px.btn(px.KEY_RIGHT) - px.btn(px.KEY_LEFT)) * SPEED
        if not self.on_ground:
            move *= AIR_CONTROL  # 空中制御（調整用）

        # 向き更新
        if move > 0:
            self.facing = True
        elif move < 0:
            self.facing = False

        # --- 重力を速度に加える ---
        self.vy += GRAVITY
        if self.vy > MAX_FALL_SPEED:
            self.vy = MAX_FALL_SPEED

        # --- ジャンプ（スペース or Z で発火） ---
        # 接地中のみジャンプ。上方向は負の速度を与える。
        if (px.btnp(px.KEY_UP) or px.btnp(px.KEY_SPACE)) and self.on_ground:
            self.vy = -JUMP_POWER
            self.on_ground = False

        # --- 実移動：Y => X の順で押し戻し付き移動 ---
        #   ・rect_move は衝突するとそれ以上進めない位置で止まる
        #   ・戻り値だけでは“ぶつかったか”が分からないので、移動後に足元/頭上の当たりを見て速度を補正する
        new_x, new_y = rect_move(self.x, self.y, self.w, self.h, dx=0, dy=self.vy)
        self.x, self.y = new_x, new_y

        # 縦衝突の後処理（足元・頭上を見る）
        if self.vy >= 0 and self._check_on_ground(self.x, self.y):
            # 着地：足元にブロック → 接地＆落下速度リセット
            self.on_ground = True
            self.vy = 0.0
        else:
            self.on_ground = False
            # 天井に頭をぶつけた可能性：上方向に動いた直後で頭上が埋まっていれば速度リセット
            if self.vy < 0 and rect_hits_block(self.x, self.y - 1, self.w, self.h):
                self.vy = 0.0

        # 横移動（縦の後に処理）
        self.x, self.y = rect_move(self.x, self.y, self.w, self.h, dx=move, dy=0)
        
        # --- 足元の宝石を取る ---
        check_item_collection(self)

    
    def draw(self):
        if self.facing:
            px.blt(self.x, self.y, self.img, self.u, self.v, self.w, self.h, self.colkey)
        else:
            px.blt(self.x, self.y, self.img, self.u, self.v, -self.w, self.h, self.colkey)
