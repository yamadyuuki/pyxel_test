# main.py
import pyxel as px
from player import Player
from stage import Stage
from constants import MAP_W, MAP_H, ENEMY_SPAWN_Y
from entity_manager import EntityManager

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

        # EntityManagerでクリボーを管理
        self.entity_manager = EntityManager()
        self.entity_manager.add_goomba(100, ENEMY_SPAWN_Y)
        self.entity_manager.add_goomba(150, ENEMY_SPAWN_Y)

        self.cam_x, self.cam_y = 0, 0
        self.screen_w, self.screen_h = 256, 256

        # ゲーム状態管理
        self.state = "PLAYING"  # "PLAYING" or "GAME_OVER"

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

        # エンティティをリセットして再追加
        self.entity_manager.reset()
        self.entity_manager.add_goomba(100, ENEMY_SPAWN_Y)
        self.entity_manager.add_goomba(150, ENEMY_SPAWN_Y)

        self.cam_x = max(0, min(self.spawn_x - self.screen_w/2, MAP_W - self.screen_w))
        self.cam_y = max(0, min(self.spawn_y - self.screen_h/2, MAP_H - self.screen_h))

    def restart(self):
        """リトライ用：ゲームをリセットして状態をPLAYINGに戻す"""
        self.reset_game()
        self.state = "PLAYING"

    def update(self):
        # --- R でリセット ---
        if px.btnp(px.KEY_R):
            self.reset_game()
            return  # このフレームの残り更新はスキップ（安全策）

        if self.state == "PLAYING":
            self.player.update()
            self.stage.update()
            self.entity_manager.update_all()
            self._update_camera()

            # 落下判定（画面下に落ちたらゲームオーバー）
            if self.player.y > MAP_H:
                self.state = "GAME_OVER"

        elif self.state == "GAME_OVER":
            # リトライ処理
            if px.btnp(px.KEY_Y):
                self.restart()
            elif px.btnp(px.KEY_N):
                px.quit()

    def draw(self):
        px.cls(0)
        px.camera(self.cam_x, self.cam_y)
        # ヒント表示
        self.stage.draw()
        self.entity_manager.draw_all()
        self.player.draw()
        px.text(10, 10, "R: Reset", 7)

        # ゲームオーバー画面
        if self.state == "GAME_OVER":
            px.camera()  # カメラをリセットして画面座標で描画
            # 半透明の背景
            px.rect(0, 0, self.screen_w, self.screen_h, 0)
            # メッセージ表示
            px.text(self.screen_w // 2 - 30, self.screen_h // 2 - 10, "GAME OVER", 8)
            px.text(self.screen_w // 2 - 40, self.screen_h // 2 + 5, "RETRY? (Y/N)", 7)

if __name__ == "__main__":
    App()
