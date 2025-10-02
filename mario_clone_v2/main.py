# main.py
import pyxel as px
from player import Player
from stage import Stage
from constants import MAP_W, MAP_H

class App:
    def __init__(self):
        px.init(256, 256, title="Mario Clone", fps=60)
        self.res_path = "my_resource.pyxres"
        px.load(self.res_path)
        px.mouse(True)

        # スポーン位置（必要に応じて調整）
        self.spawn_x, self.spawn_y = 30, 120

        self.stage = Stage()
        self.player = Player(self.spawn_x, self.spawn_y)

        self.cam_x, self.cam_y = 0, 0
        self.screen_w, self.screen_h = 256, 256

        px.run(self.update, self.draw)

    def _update_camera(self):
        # プレイヤー中心を画面中央に置くターゲット
        target_x = self.player.x + self.player.w / 2 - self.screen_w / 2
        target_y = self.player.y + self.player.h / 2 - self.screen_h / 2

        # スムージング（不要なら cam_x = target_x に置き換えOK）
        alpha = 0.15
        self.cam_x += (target_x - self.cam_x) * alpha
        self.cam_y += (target_y - self.cam_y) * alpha

        # マップ内にクランプ
        self.cam_x = max(0, min(self.cam_x, MAP_W - self.screen_w))
        self.cam_y = max(0, min(self.cam_y, MAP_H - self.screen_h))

    def reset_game(self):
        # リソース再読込でタイルマップを初期化（宝石なども元通り）
        px.load(self.res_path)
        # シーン/プレイヤーを作り直し
        self.stage = Stage()
        self.player = Player(self.spawn_x, self.spawn_y)

        self.cam_x = max(0, min(self.spawn_x - self.screen_w/2, MAP_W - self.screen_w))
        self.cam_y = max(0, min(self.spawn_y - self.screen_h/2, MAP_H - self.screen_h))

    def update(self):
        # --- R でリセット ---
        if px.btnp(px.KEY_R):
            self.reset_game()
            return  # このフレームの残り更新はスキップ（安全策）

        self.player.update()
        self.stage.update()
        self._update_camera()

    def draw(self):
        px.cls(0)
        px.camera(self.cam_x, self.cam_y)
        # ヒント表示
        self.stage.draw()
        self.player.draw()
        px.text(10, 10, "R: Reset", 7)

if __name__ == "__main__":
    App()
