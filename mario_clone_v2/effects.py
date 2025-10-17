# effects.py
# ゲーム内エフェクトの管理
import pyxel as px
from constants import TILE_SIZE

class CoinEffect:
    """はてなブロックから飛び出すコインエフェクト"""
    def __init__(self, x, y):
        # ブロックの中心からコインを出現させる
        self.x = x
        self.y = y
        self.vy = -3.0  # 初期速度（上向き）
        self.gravity = 0.15  # 重力（徐々に減速）
        self.lifetime = 40  # 表示フレーム数（約0.67秒）
        self.age = 0
        self.alive = True

    def update(self):
        """エフェクトの更新"""
        self.age += 1

        # 寿命が来たら消滅
        if self.age >= self.lifetime:
            self.alive = False
            return

        # 上に移動（徐々に減速して落下）
        self.vy += self.gravity
        self.y += self.vy

    def draw(self):
        """エフェクトの描画"""
        if self.alive:
            # TILE_GEM (1,0) のスプライトを描画
            # タイルマップ座標 (1, 0) はピクセル座標では (8, 0)
            px.blt(self.x, self.y, 0, 8, 0, TILE_SIZE, TILE_SIZE, 0)
