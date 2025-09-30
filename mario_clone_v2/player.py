# player.py
import pyxel as px
from constants import SPEED, GRAVITY, JUMP_POWER, MAX_FALL_SPEED, AIR_CONTROL,COYOTE_FRAMES
from system import rect_move
from system import rect_hits_block  # 足元判定に使う
from system import collect_gems_in_rect

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
        # 直近で「地面だった」フレーム番号（初期は十分古い値に）
        self.last_ground_frame = -999999

        # ---- ここから追加（立ち/しゃがみの定義）----
        self.is_crouching = False
        # 立ち姿のスプライトとサイズ
        self.stand_u, self.stand_v = 16, 0
        self.stand_w, self.stand_h = 16, 16
        # しゃがみ姿のスプライトとサイズ（質問で提示のフレーム）
        self.crouch_u, self.crouch_v = 32, 16
        self.crouch_w, self.crouch_h = 16, 8
        # ---- 追加ここまで ----

    def _check_on_ground(self, x, y):
        """足元1pxにブロックがあるかで接地判定"""
        return rect_hits_block(x, y + 1, self.w, self.h)

    def update(self):
        # --- 横入力 ---
        base_move = (px.btn(px.KEY_RIGHT) - px.btn(px.KEY_LEFT)) * SPEED
        if not self.on_ground:
            base_move *= AIR_CONTROL

        # 地上で下キーを押しているか
        want_crouch = self.on_ground and px.btn(px.KEY_DOWN)

        # ---- しゃがみ状態の更新 ----
        if want_crouch and not self.is_crouching:
            # しゃがみに入る：高さを縮め、足元固定のため y を下げる
            self.is_crouching = True
            old_h = self.h
            self.u, self.v = self.crouch_u, self.crouch_v
            self.w, self.h = self.crouch_w, self.crouch_h
            self.y += (old_h - self.h)  # 足元を据え置き

        elif (not want_crouch) and self.is_crouching:
            # 立ちに戻れるか判定（頭上にブロックがないか）
            delta_h = self.stand_h - self.h  # 立ちに戻すと増える高さ
            test_x = self.x
            test_y = self.y - delta_h  # 立ちに戻すと頭が上に伸びるので、y を上に戻した位置でテスト
            can_stand = not rect_hits_block(test_x, test_y, self.w, self.stand_h)
            if can_stand:
                self.is_crouching = False
                self.u, self.v = self.stand_u, self.stand_v
                self.w, self.h = self.stand_w, self.stand_h
                self.y = test_y  # 実際に上に戻す
            # 頭上に当たっているなら、しゃがみ継続（何もしない）

        # しゃがみ中は移動速度を少し下げる（任意）
        move = base_move * (0.6 if self.is_crouching else 1.0)

        # 向き更新
        if move > 0: self.facing = True
        elif move < 0: self.facing = False

        # --- 重力 ---
        self.vy += GRAVITY
        if self.vy > MAX_FALL_SPEED:
            self.vy = MAX_FALL_SPEED

        # --- ジャンプ（しゃがみ中は不可にする） ---
        want_jump = (px.btnp(px.KEY_UP) or px.btnp(px.KEY_SPACE))
        recently_grounded = (px.frame_count - self.last_ground_frame) <= COYOTE_FRAMES
        can_jump = (self.on_ground or recently_grounded) and (not self.is_crouching)
        if want_jump and can_jump:
            self.vy = -JUMP_POWER
            self.on_ground = False
            self.last_ground_frame = -999999

        # --- 実移動（Y→X） ---
        new_x, new_y = rect_move(self.x, self.y, self.w, self.h, dx=0, dy=self.vy)
        self.x, self.y = new_x, new_y

        # 縦衝突後の補正
        if self.vy >= 0 and self._check_on_ground(self.x, self.y):
            self.on_ground = True
            self.vy = 0.0
            self.last_ground_frame = px.frame_count
        else:
            self.on_ground = False
            if self.vy < 0 and rect_hits_block(self.x, self.y - 1, self.w, self.h):
                self.vy = 0.0

        # 横移動
        self.x, self.y = rect_move(self.x, self.y, self.w, self.h, dx=move, dy=0)

        # アイテム回収
        got = collect_gems_in_rect(self.x, self.y, self.w, self.h)
        if got > 0:
            self.gems_collected += got
            px.play(0, 0)


    
    def draw(self):
        if self.facing:
            px.blt(self.x, self.y, self.img, self.u, self.v, self.w, self.h, self.colkey)
        else:
            px.blt(self.x, self.y, self.img, self.u, self.v, -self.w, self.h, self.colkey)
