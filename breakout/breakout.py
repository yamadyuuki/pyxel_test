import pyxel

# ballの設定
BALL_W = 2
BALL_H = 2
BALL_MAX_SPEED = 3.0
BALL_START_ANGLE = 0.6  # 初速の左右バラつき係数(0.0~1.0)

def clamp(v, lo, hi):
    return max(lo, min(v, hi))

def rects_intersect(ax, ay, aw, ah, bx, by, bw, bh):
    return (ax < bx + bw and bx < ax + aw and
            ay < by + bh and by < ay + ah)

SCREEN_W = 256
SCREEN_H = 256
BALL_SPEED = 4
BALL_SPEED_UP = 0.05

BLOCK_TYPE = [
    {"hp": 3, "color": 8,  "rows": 2},  # HP3のブロックを2行
    {"hp": 2, "color": 10, "rows": 3},  # HP2を3行
    {"hp": 1, "color": 11, "rows": 1}   # HP1を5行
]

HP_COLOR = {
    3: 8,   # 赤系
    2: 10,  # 黄系
    1: 11,  # 緑系
}

BLOCK_W = 16
BLOCK_H = 8
BLOCK_MARGIN_X = 1
BLOCK_MARGIN_Y = 1

BLOCK_COLS = SCREEN_W // BLOCK_W      # 10列（160/16）
BLOCK_ROWS = 10                        # 行数は好みで
BLOCK_TOP = 40 # ブロック群の上端位置

START_SCENE = 0
PLAY_SCENE = 1
PAUSE_SCENE = 2
GAME_OVER_SCENE = 3

# パドルの設定
PADDLE_W = 24      # 板の幅
PADDLE_H = 4       # 板の高さ
PADDLE_SPEED = 3   # 板の移動速度

# ライフポイント
LIFE_POINTS = 3

class App:
    def __init__(self):
        pyxel.init(SCREEN_W, SCREEN_H, title="Breakout Game", fps=60)
        pyxel.load("my_resource.pyxres") # リソースの読み込み
#        self.jp_font = pyxel.Font("umplus_j10r.bdf") # 日本語フォントの読み込み
        self.init_game()
        pyxel.run(self.update, self.draw)

    def init_game(self):
        self.current_scene = START_SCENE
        #パドルの初期化
        self.paddle_x = (SCREEN_W - PADDLE_W) // 2
        self.paddle_y = SCREEN_H - PADDLE_H - 8
        # ボールの初期化
        self.ball_reset(attached=True)  # 最初はパドルに乗せておく
        self.lives = LIFE_POINTS  # ライフポイントの初期化
        self.blocks = self.build_blocks()  # ブロックの初期化

    # --- ボール初期化 ---
    def ball_reset(self, attached=False):
        # パドル中央に配置
        self.ball_x = self.paddle_x + PADDLE_W / 2 - BALL_W / 2
        self.ball_y = self.paddle_y - BALL_H - 1
        # 速度
        self.vx = BALL_SPEED * (pyxel.rndf(-BALL_START_ANGLE, BALL_START_ANGLE))
        self.vy = -BALL_SPEED
        self.vx = clamp(self.vx, -BALL_MAX_SPEED, BALL_MAX_SPEED)
        self.attached = attached  # Trueの間はパドルに追従（SPACEで発射）

    # --- ボール更新 ---
    def update_ball(self):
        # パドルに“乗っている”状態：左右移動に追従、Spaceで発射
        if self.attached:
            self.ball_x = self.paddle_x + PADDLE_W / 2 - BALL_W / 2
            self.ball_y = self.paddle_y - BALL_H - 1
            if pyxel.btnp(pyxel.KEY_SPACE):  # 発射
                self.attached = False
            return

        prev_x, prev_y = self.ball_x, self.ball_y

        # 位置更新
        self.ball_x += self.vx
        self.ball_y += self.vy

        # --- 壁反射 ---
        if self.ball_x <= 0:
            self.ball_x = 0
            self.vx *= -1
        elif self.ball_x + BALL_W >= SCREEN_W:
            self.ball_x = SCREEN_W - BALL_W
            self.vx *= -1
        if self.ball_y <= 0:
            self.ball_y = 0
            self.vy *= -1

        # --- 画面下に落ちたら再装填 ---
        if self.ball_y > SCREEN_H:
            self.lives -= 1
            if self.lives <= 0:
                self.current_scene = GAME_OVER_SCENE # ゲームオーバーシーンへ
            else:
                self.ball_reset(attached=True)
            return
        # --- ブロック衝突 ---
        self.check_block_collision(prev_x, prev_y)
        
        # --- パドル衝突 ---
        if rects_intersect(self.ball_x, self.ball_y, BALL_W, BALL_H,
                           self.paddle_x, self.paddle_y, PADDLE_W, PADDLE_H):
            # パドルの上面に戻す
            self.ball_y = self.paddle_y - BALL_H - 1
            # 縦速度は上向きへ
            self.vy = -abs(self.vy)

            """""
            # 打点によって横速度を調整（中心差分を-1~1に正規化）
            center = self.paddle_x + PADDLE_W / 2
            offset = ((self.ball_x + BALL_W / 2) - center) / (PADDLE_W / 2)
            self.vx = clamp(offset * BALL_MAX_SPEED, -BALL_MAX_SPEED, BALL_MAX_SPEED)
            
            # ほんの少しスピードアップ（上限あり）
            speed = (self.vx**2 + self.vy**2) ** 0.5
            speed = min(speed + BALL_SPEED_UP, BALL_MAX_SPEED * 1.2)
            # 角度そのままで速度をスケーリング
            if speed > 0:
                norm = (self.vx**2 + self.vy**2) ** 0.5 or 1.0
                self.vx = self.vx / norm * speed
                self.vy = self.vy / norm * speed
            """
    # --- ボール描画 ---
    def draw_ball(self):
        pyxel.rect(int(self.ball_x), int(self.ball_y), BALL_W, BALL_H, pyxel.COLOR_WHITE)

    def update(self):
        if pyxel.btnp(pyxel.KEY_ESCAPE):
             pyxel.quit()
        if pyxel.btnp(pyxel.KEY_R):
            self.init_game()
            self.current_scene = START_SCENE
            self.update_start_scene()
        if self.current_scene == START_SCENE:
            self.update_start_scene()
        elif self.current_scene == PLAY_SCENE:
            self.update_play_scene()
        elif self.current_scene == PAUSE_SCENE:
            self.update_pause_scene()

    def update_start_scene(self):
        """スタートシーンの更新"""
        if pyxel.btnp(pyxel.KEY_SPACE):
            self.current_scene = PLAY_SCENE

    def update_play_scene(self):
        """プレイシーンの更新"""
        if pyxel.btnp(pyxel.KEY_P):
            self.current_scene = PAUSE_SCENE
        # パドルの更新処理を呼び出し
        self.update_paddle()
        # ボールの更新処理を呼び出し
        self.update_ball()

    def update_pause_scene(self):
        """ポーズシーンの更新"""
        if pyxel.btnp(pyxel.KEY_SPACE):
            self.current_scene = PLAY_SCENE

    # パドルの更新
    def update_paddle(self):
         if pyxel.btn(pyxel.KEY_RIGHT) and self.paddle_x < SCREEN_W -PADDLE_W - BLOCK_MARGIN_X:
            self.paddle_x += PADDLE_SPEED
         if pyxel.btn(pyxel.KEY_LEFT) and self.paddle_x > BLOCK_MARGIN_X:
            self.paddle_x -= PADDLE_SPEED


    def draw(self):
        if self.current_scene == START_SCENE:
            self.draw_start_scene()
        elif self.current_scene == PLAY_SCENE:
            self.draw_play_scene()
        elif self.current_scene == PAUSE_SCENE:
            self.draw_pause_scene()
        elif self.current_scene == GAME_OVER_SCENE:
            self.draw_game_over_scene()
    
    def draw_start_scene(self): # スタートシーンの描画
        pyxel.cls(pyxel.COLOR_NAVY)
        pyxel.text(SCREEN_W // 2 - 30, SCREEN_H // 2 - 10, "BREAKOUT GAME", pyxel.COLOR_WHITE)
        pyxel.text(SCREEN_W // 2 - 35, SCREEN_H // 2 + 10, "Press SPACE to start", pyxel.COLOR_WHITE)

    def draw_play_scene(self): # プレイシーンの描画
          pyxel.cls(pyxel.COLOR_CYAN)
          self.draw_hud()
          self.draw_blocks()
          self.draw_paddle()
          self.draw_ball()

    def draw_blocks(self):
        for b in self.blocks:
            b.draw()
    def draw_pause_scene(self): # ポーズシーンの描画
            pyxel.cls(pyxel.COLOR_GRAY)
            pyxel.text(SCREEN_W // 2 - 20, SCREEN_H // 2, "PAUSED", pyxel.COLOR_WHITE)
            pyxel.text(SCREEN_W // 2 - 30, SCREEN_H // 2 + 10, "Press SPACE to continue", pyxel.COLOR_WHITE)

    def draw_game_over_scene(self): # ゲームオーバーシーンの描画
        pyxel.cls(pyxel.COLOR_RED)
        pyxel.text(SCREEN_W // 2 - 30, SCREEN_H // 2 - 10, "GAME OVER", pyxel.COLOR_WHITE)

    # 板の描画
    def draw_paddle(self):
        """板の描画"""
        # 単色の矩形で板を描画
        pyxel.rect(self.paddle_x, self.paddle_y, PADDLE_W, PADDLE_H, pyxel.COLOR_WHITE)
        # より見た目を良くしたい場合は、枠線を追加
        pyxel.rectb(self.paddle_x, self.paddle_y, PADDLE_W, PADDLE_H, pyxel.COLOR_GRAY)    

    def build_blocks(self):
        blocks = []
        cols = block_cols()
        y = BLOCK_TOP
        for t in BLOCK_TYPE:
            for r in range(t["rows"]):      # 行数ぶん繰り返す
                for c in range(cols):
                    x = BLOCK_MARGIN_X + c * (BLOCK_W + BLOCK_MARGIN_X)
                    blocks.append(Block(x, y, t))  # 種類そのものを渡す
                y += BLOCK_H + BLOCK_MARGIN_Y
        return blocks

    # ブロックの列数を計算
    def block_cols():
        return (SCREEN_W + BLOCK_MARGIN_X) // (BLOCK_W + BLOCK_MARGIN_X)
    
    def check_block_collision(self, prev_x, prev_y):
    # ボールとブロックの当たり判定。当たったブロックのhpを減らし、0なら消滅。反射方向は「どこから入ってきたか」で判定。
        for b in self.blocks:
            if not b.alive:
                continue

            if rects_intersect(self.ball_x, self.ball_y, BALL_W, BALL_H,
                            b.x, b.y, b.w, b.h):
                # --- 反射方向の判定（前フレーム位置から推定） ---
                from_top    = prev_y + BALL_H <= b.y and self.ball_y + BALL_H > b.y
                from_bottom = prev_y >= b.y + b.h and self.ball_y < b.y + b.h
                from_left   = prev_x + BALL_W <= b.x and self.ball_x + BALL_W > b.x
                from_right  = prev_x >= b.x + b.w and self.ball_x < b.x + b.w

                if from_top or from_bottom:
                    self.vy *= -1
                    # めり込み補正（上/下側へ押し戻す）
                    if from_top:
                        self.ball_y = b.y - BALL_H - 0.01
                    else:
                        self.ball_y = b.y + b.h + 0.01
                elif from_left or from_right:
                    self.vx *= -1
                    # めり込み補正（左/右側へ押し戻す）
                    if from_left:
                        self.ball_x = b.x - BALL_W - 0.01
                    else:
                        self.ball_x = b.x + b.w + 0.01
                else:
                    # 万一どこから入ったか特定できないときは縦に反射
                    self.vy *= -1

                # --- ブロック耐久の減少 ---
                b.hp -= 1
                if b.hp <= 0:
                    b.alive = False

                # 1フレームで複数ヒットを防ぐ
                break
    def draw_hud(self):
        # テキスト
        pyxel.text(4, 4, "LIVES:", pyxel.COLOR_YELLOW)
        # アイコン（小さな丸を並べる）
        for i in range(self.lives - 1):
            x = 33 + i * 10   # 並び位置
            pyxel.circ(x, 6, 3, pyxel.COLOR_RED)

# ブロックの描画
class Block:
    def __init__(self, x, y, t):
        self.x = x
        self.y = y
        self.w = BLOCK_W
        self.h = BLOCK_H
        self.hp = t["hp"]
        self.color = t["color"]
        self.alive = True

    def draw(self):
        if not self.alive:
            return
        if not self.alive:
            return
        color = HP_COLOR.get(self.hp, 11)
        pyxel.rect(self.x, self.y, self.w, self.h, color)

        if self.hp == 3:
            # フレームごとに色を循環（Pyxelは0~15の16色）
            border_color = (pyxel.frame_count // 20) % 16
        else:
            border_color = pyxel.COLOR_WHITE

        pyxel.rectb(self.x, self.y, self.w, self.h, border_color)

# ブロックの列数を計算
def block_cols():
    return (SCREEN_W + BLOCK_MARGIN_X) // (BLOCK_W + BLOCK_MARGIN_X)


App()