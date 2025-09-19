import pyxel
from core.world import World

# 左がゲーム領域、右がメニュー
GAME_W, GAME_H = 200, 150
PANEL_W = 70
W, H = GAME_W + PANEL_W, GAME_H


# ゲーム状態（簡単なステートマシン）
STATE_TITLE = 0
STATE_PLAY  = 1

class App:
    def __init__(self):
        pyxel.init(W, H, title="Barrage MVP", fps=60)
        pyxel.mouse(True)
        self.state = STATE_TITLE
        self.world = World(GAME_W, GAME_H, panel_w=PANEL_W)  # ゲーム本体は開始時に生成
        pyxel.run(self.update, self.draw)

    # --- 入力とロジック ---
    def update(self):
        if pyxel.btnp(pyxel.KEY_R):
            self.reset_game()
        # ESCはPyxel標準で終了（別途処理不要）
        if self.state == STATE_TITLE:
            # SPACEを「押した瞬間」で判定（btnp: ボタン・プレス）
            if pyxel.btnp(pyxel.KEY_SPACE):
                self.start_game()
        elif self.state == STATE_PLAY:
            # ゲーム中の更新
            self.world.update()
            # ここでポーズ等を入れたければ追加可能
            # if pyxel.btnp(pyxel.KEY_P): ...

    def reset_game(self):
        self.state = STATE_PLAY
        self.world = World(GAME_W, GAME_H, panel_w=PANEL_W)   # Worldを初期化
        # もしスコアや残機があるならここでリセット

    # --- 描画 ---
    def draw(self):
        pyxel.cls(1)
        if self.state == STATE_TITLE:
            self.draw_title()
        elif self.state == STATE_PLAY:
            self.world.draw()

    # --- ヘルパ ---
    def start_game(self):
        # 新しいWorldを生成してゲーム開始
        self.world = World(GAME_W, GAME_H, panel_w=PANEL_W)
        self.state = STATE_PLAY

    def draw_title(self):
        title = "BARRAGE MVP"
        msg1  = "PRESS SPACE TO START"
        msg2  = "ESC TO QUIT"
        # 文字を中央寄せ（ざっくり）
        x_title = (W - len(title)*4) // 2
        x_msg1  = (W - len(msg1)*4)  // 2
        x_msg2  = (W - len(msg2)*4)  // 2
        pyxel.text(x_title, H//2 - 16, title, 10)
        pyxel.text(x_msg1,  H//2,      msg1, 7)
        pyxel.text(x_msg2,  H//2 + 12, msg2, 6)

if __name__ == "__main__":
    App()
