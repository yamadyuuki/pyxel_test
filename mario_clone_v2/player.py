# player.py
import pyxel as px
from constants import SPEED, GRAVITY, JUMP_POWER, MAX_FALL_SPEED, AIR_CONTROL,COYOTE_FRAMES, JUMP_BUFFER_FRAMES, TILE_PLATFORM, TILE_SIZE, TILE_QUESTION
import system
from system import rect_move
from system import rect_hits_block, get_tile_type  # 足元判定に使う
from game_object import GameObject
from system import collect_gems_in_rect

class Player(GameObject):
    def __init__(self, x, y, entity_manager=None):
        super().__init__(x, y, 0, 16, 0, 16, 16, 0)
        self.facing = True   # false: 左向き, true: 右向き
        self.vx = 0.0        # 横速度
        self.vy = 0.0        # 縦速度（+は下向き）
        self.on_ground = False
        self.gems_collected = 0
        # 直近で「地面だった」フレーム番号（初期は十分古い値に）
        self.last_ground_frame = -999999
        self.entity_manager = entity_manager  # エフェクト生成用

        # ---- ここから追加（立ち/しゃがみの定義）----
        self.is_crouching = False
        # 立ち姿のスプライトとサイズ
        self.stand_u, self.stand_v = 16, 0
        self.stand_w, self.stand_h = 16, 16
        # しゃがみ姿のスプライトとサイズ（質問で提示のフレーム）
        self.crouch_u, self.crouch_v = 32, 8
        self.crouch_w, self.crouch_h = 16, 8
        # ---- 追加ここまで ----
        self.jump_buffer_until = -10**9
        # 前フレーム位置（上から乗った判定に使用）
        self.prev_x = self.x
        self.prev_y = self.y
        self.is_dashing = False

    def _check_on_ground(self, x, y):
        """足元1pxにブロックがあるかで接地判定"""
        return rect_hits_block((x), (y + 1), self.w, self.h)

    def update(self):
        # 前フレームの位置を保存（着地方向の判定に使用）
        self.prev_x, self.prev_y = self.x, self.y
        # --- 横入力 ---
        base_move = (px.btn(px.KEY_RIGHT) - px.btn(px.KEY_LEFT)) * SPEED
        self.is_dashing = px.btn(px.KEY_D)
        if self.is_dashing:
            base_move *= 1.5

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
            can_stand = not rect_hits_block((test_x), (test_y), self.w, self.stand_h)
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

        # # --- ジャンプ（しゃがみ中は不可にする） ---
        # want_jump = (px.btnp(px.KEY_UP) or px.btnp(px.KEY_SPACE))
        # recently_grounded = (px.frame_count - self.last_ground_frame) <= COYOTE_FRAMES
        # can_jump = (self.on_ground or recently_grounded) and (not self.is_crouching)
        # if want_jump and can_jump:
        #     self.vy = -JUMP_POWER
        #     self.on_ground = False
        #     self.last_ground_frame = -999999

        # ジャンプボタンが押されたらバッファタイムをセット
        if px.btnp(px.KEY_UP) or px.btnp(px.KEY_SPACE):
            self.jump_buffer_until = px.frame_count + JUMP_BUFFER_FRAMES

        recently_grounded = (px.frame_count - self.last_ground_frame) <= COYOTE_FRAMES
        can_jump = (self.on_ground or recently_grounded) and (not self.is_crouching)

        # バッファ内かつジャンプ可能ならジャンプを実行
        if px.frame_count <= self.jump_buffer_until and can_jump:
            self.vy = -JUMP_POWER
            self.on_ground = False
            self.last_ground_frame = -999999
            # バッファを消費
            self.jump_buffer_until = -10**9

        # --- 実移動（Y→X） ---
        new_x, new_y = rect_move(self.x, self.y, self.w, self.h, dx=0, dy=self.vy)
        self.x, self.y = new_x, new_y

        # 縦衝突後の補正
        if self.vy >= 0 and self._check_on_ground(self.x, self.y):
            # 足元のタイルをチェック
            foot_y = self.y + self.h
            foot_points = (
                self.x + 1,
                self.x + self.w // 2,
                self.x + self.w - 2,
            )
            platform_contact = False
            for fx in foot_points:
                if get_tile_type(fx, foot_y) == TILE_PLATFORM:
                    platform_contact = True
                    break
            tile_under = TILE_PLATFORM if platform_contact else get_tile_type(self.x + self.w / 2, foot_y)

            if tile_under == TILE_PLATFORM:
                # 上から乗ったときのみ発動（横・下からは無効）
                ty_under = int((self.y + self.h) // TILE_SIZE)
                platform_top = ty_under * TILE_SIZE
                prev_bottom = self.prev_y + self.h - 1
                if prev_bottom <= platform_top:
                    # ジャンプ台なら、大ジャンプ
                    self.vy = -JUMP_POWER * 1.5
                    self.on_ground = False
                    # px.play(0, 1) # ジャンプ音
                else:
                    # 横から触れた場合は通常床扱いしない（すり抜け防止のため接地にする）
                    self.on_ground = True
                    self.vy = 0.0
                    self.last_ground_frame = px.frame_count
            else:
                # 通常の床
                self.on_ground = True
                self.vy = 0.0
                self.last_ground_frame = px.frame_count
        else:
            self.on_ground = False
            if self.vy < 0 and rect_hits_block((self.x), (self.y - 1), self.w, self.h):
                # 頭上のタイルをチェック（ハテナブロックに当たったか）
                head_y = self.y - 1
                head_points = (
                    self.x + 1,
                    self.x + self.w // 2,
                    self.x + self.w - 2,
                )
                for hx in head_points:
                    tile_type = get_tile_type(hx, head_y)
                    if tile_type == TILE_QUESTION:
                        # ハテナブロックを叩いた
                        px.play(0, 1)  # ハテナブロック音

                        # ブロックの座標を計算
                        tx = int(hx // TILE_SIZE)
                        ty = int(head_y // TILE_SIZE)

                        # コインエフェクトを生成（ブロックの中心から出現）
                        if self.entity_manager:
                            coin_x = tx * TILE_SIZE
                            coin_y = ty * TILE_SIZE
                            self.entity_manager.add_coin_effect(coin_x, coin_y)

                        # ブロックを空にする（叩いた後は使用済みにする）
                        system.set_tile_empty(hx, head_y)
                        break
                self.vy = 0.0

        # 横移動
        self.x, self.y = rect_move(self.x, self.y, self.w, self.h, dx=move, dy=0)

        # アイテム回収
        got = collect_gems_in_rect((self.x), (self.y), self.w, self.h)
        if got > 0:
            self.gems_collected += got
            px.play(0, 0)  # アイテム取得音


    def draw(self):
        # ダッシュ中はカラーパレットを変更
        if self.is_dashing:
            # 白色(7)を赤色(8)に変更
            px.pal(7, 8)

        # 立ち/しゃがみで高さが変わるので、都度 self.h を使う
        if self.facing:
            px.blt(self.x, self.y, self.img, self.u, self.v, self.w, self.h, self.colkey)
        else:
            px.blt(self.x, self.y, self.img, self.u, self.v, -self.w, self.h, self.colkey)

        # カラーパレットを元に戻す
        if self.is_dashing:
            px.pal()
