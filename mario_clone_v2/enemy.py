# enemy.py
import random
import pyxel as px
from constants import ENEMY_IMG, ENEMY_U, ENEMY_V, ENEMY_W, ENEMY_H, ENEMY_COLKEY

class Goomba:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.img = ENEMY_IMG
        self.u = ENEMY_U
        self.v = ENEMY_V
        self.w = ENEMY_W
        self.h = ENEMY_H
        self.colkey = ENEMY_COLKEY

        self.direction_timer = random.randint(120, 180)
        self.direction = 1  # 1:右, -1:左
        self.speed = 0.5

    def update(self):
        # タイマーをデクリメント
        self.direction_timer -= 1
        if self.direction_timer <= 0:
            # 方向を反転
            self.direction *= -1
            # タイマーをリセット
            self.direction_timer = random.randint(120, 180)

        # x座標を更新
        self.x += self.direction * self.speed

    def draw(self):
        px.blt(self.x, self.y, self.img, self.u, self.v, self.w, self.h, self.colkey)
