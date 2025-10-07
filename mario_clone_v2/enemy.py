# enemy.py
import random
from constants import ENEMY_IMG, ENEMY_U, ENEMY_V, ENEMY_W, ENEMY_H, ENEMY_COLKEY
from game_object import GameObject


class Goomba(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y, ENEMY_IMG, ENEMY_U, ENEMY_V, ENEMY_W, ENEMY_H, ENEMY_COLKEY)
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
