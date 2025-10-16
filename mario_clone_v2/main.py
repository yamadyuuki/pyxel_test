# main.py
import pyxel as px
from player import Player
from stage import Stage
from constants import MAP_W, MAP_H, ENEMY_SPAWN_POSITIONS
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

        # EntityManagerでクリボーを管理（初期配置を渡す）
        self.entity_manager = EntityManager(ENEMY_SPAWN_POSITIONS)

        self.deaths = 0              # やられ回数
        self.stage_start_frame = px.frame_count  # ステージ開始フレーム

        self.cam_x, self.cam_y = 0, 0
        self.screen_w, self.screen_h = 256, 256

        # ゲーム状態管理
        # 状態: "START" -> タイトル/スタート画面表示
        #       "PLAYING" -> ゲーム中
        #       "PAUSED" -> ポーズ中
        #       "GAME_OVER" -> ゲームオーバー
        self.state = "START"

        self.debug_mode = False # デバッグモード用のフラグ

        # 起動時はゲームを初期化しておく
        self.reset_game()

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

        # エンティティを初期配置に戻す
        self.entity_manager.reset()

        self.cam_x = max(0, min(self.spawn_x - self.screen_w/2, MAP_W - self.screen_w))
        self.cam_y = max(0, min(self.spawn_y - self.screen_h/2, MAP_H - self.screen_h))

        # 経過時間リセット
        self.stage_start_frame = px.frame_count

    def restart(self):
        """リトライ用：ゲームをリセットして状態をPLAYINGに戻す"""
        self.reset_game()
        self.state = "PLAYING"

    def update(self):
        # --- Qでデバッグモード切替 ---
        if px.btnp(px.KEY_Q):
            self.debug_mode = not self.debug_mode

        # --- R でリセット ---
        if px.btnp(px.KEY_R):
            self.reset_game()
            return  # このフレームの残り更新はスキップ（安全策）

        if self.state == "START":
            # スタート画面で SPACE が押されたらゲーム開始
            if px.btnp(px.KEY_SPACE):
                self.state = "PLAYING"
                # ステージ開始時間を今のフレームとしてリセット
                self.stage_start_frame = px.frame_count
            return

        if self.state == "PLAYING":
            # Pキーでポーズ
            if px.btnp(px.KEY_P):
                self.state = "PAUSED"
                return

            self.player.update()
            self.stage.update()
            self.entity_manager.update_all()
            self._update_camera()

            # クリボーとの当たり判定
            collision = self.entity_manager.check_collision_with_player(self.player)
            if collision:
                collision_type, goomba = collision
                if collision_type == "stomp":
                    # 踏んだ → クリボー削除 & 小ジャンプ
                    self.entity_manager.remove_goomba(goomba)
                    self.player.vy = -4  # 小ジャンプ
                elif collision_type == "hit":
                    # 横から当たった → ゲームオーバー
                    self.state = "GAME_OVER"
                    self.deaths += 1

            # 落下判定（画面下に落ちたらゲームオーバー）
            if self.player.y > MAP_H:
                self.state = "GAME_OVER"
                self.deaths += 1

        elif self.state == "PAUSED":
            # ポーズ解除
            if px.btnp(px.KEY_P):
                self.state = "PLAYING"

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

        # デバッグ用の縦線表示
        if self.debug_mode:
            # 100px間隔の線
            start_x = int(self.cam_x // 100) * 100
            end_x = int((self.cam_x + self.screen_w) // 100 + 1) * 100
            
            for x in range(start_x, end_x, 100):
                if x <= 0: continue # 0以下は描画しない
                # 点線を描画 (y方向に4pxごとに点を打つ)
                for y in range(0, MAP_H, 4):
                    px.pset(x, y, 6) # 薄い灰色で点を描画
                
                # 座標の数値を表示
                px.text(x + 2, 10, f"{str(x)}px", 7) # 白色で数値を表示

        # UI表示（カメラ座標に固定）
        ui_x = self.cam_x + 5
        ui_y = self.cam_y + 5
        px.text(ui_x, ui_y, f"GEMS: {self.player.gems_collected}", 7)

        # 経過時間（秒）を計算
        elapsed_frames = px.frame_count - self.stage_start_frame
        timer_sec = elapsed_frames / 60
        px.text(ui_x, ui_y + 8, f"TIME: {timer_sec:.2f}", 7)

        px.text(ui_x, ui_y + 16, f"DEATHS: {self.deaths}", 7)
        px.text(ui_x, ui_y + 24, "R: Reset", 7)

        # デバッグ表示（ジャンプバッファ・コヨーテタイム）
        if self.state == "PLAYING":
            debug_x = self.cam_x + 5
            debug_y = self.cam_y + 40

            # コヨーテタイム残りフレーム
            coyote_remaining = max(0, (self.player.last_ground_frame + 6) - px.frame_count)
            px.text(debug_x, debug_y, f"Coyote: {coyote_remaining}", 10 if coyote_remaining > 0 else 5)

            # ジャンプバッファ残りフレーム
            buffer_remaining = max(0, self.player.jump_buffer_until - px.frame_count)
            px.text(debug_x, debug_y + 8, f"Buffer: {buffer_remaining}", 10 if buffer_remaining > 0 else 5)

        # ポーズ画面
        if self.state == "PAUSED":
            px.camera()  # カメラをリセットして画面座標で描画
            # 半透明の背景
            px.rect(0, 0, self.screen_w, self.screen_h, 1)
            # メッセージ表示
            px.text(self.screen_w // 2 - 20, self.screen_h // 2 - 4, "PAUSED", 7)
            px.text(self.screen_w // 2 - 35, self.screen_h // 2 + 8, "Press P to Resume", 7)

        # ゲームオーバー画面
        if self.state == "GAME_OVER":
            px.camera()  # カメラをリセットして画面座標で描画
            # 半透明の背景
            px.rect(0, 0, self.screen_w, self.screen_h, 0)
            # メッセージ表示
            px.text(self.screen_w // 2 - 30, self.screen_h // 2 - 10, "GAME OVER", 8)
            px.text(self.screen_w // 2 - 40, self.screen_h // 2 + 5, "RETRY? (Y/N)", 7)

        # スタート画面
        if self.state == "START":
            px.camera()
            # 背景（暗め）
            px.rect(0, 0, self.screen_w, self.screen_h, 1)
            # タイトル
            px.text(self.screen_w // 2 - 40, self.screen_h // 2 - 18, "MARIO CLONE", 7)
            px.text(self.screen_w // 2 - 60, self.screen_h // 2 - 2, "Press SPACE to Start", 7)
            px.text(self.screen_w // 2 - 70, self.screen_h // 2 + 14, "R: Reset resources (debug)", 7)

if __name__ == "__main__":
    App()
