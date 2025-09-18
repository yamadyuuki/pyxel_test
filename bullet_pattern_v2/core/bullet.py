# bullet.py
import pyxel

class Bullet:
    __slots__ = ("x", "y", "vx", "vy", "r", "c", "alive")
    def __init__(self):
        self.alive = False
        self.x = self.y = 0.0
        self.vx = self.vy = 0.0
        self.r = 0
        self.c = 7

class BulletSystem:
    def __init__(self, w, h, capacity=512):
        self.w, self.h = w, h
        self.capacity = capacity
        # ← 統一して「pool」に弾オブジェクトを保持
        self.pool = [Bullet() for _ in range(capacity)]

    def clear_all(self):
        for b in self.pool:
            b.alive = False

    def spawn(self, x, y, vx, vy, r=1, c=7):
        for b in self.pool:
            if not b.alive:
                b.alive = True
                b.x, b.y = x, y
                b.vx, b.vy = vx, vy
                b.r, b.c = r, c
                return b
        return None  # 溢れたら捨てる

    def update(self):
        for b in self.pool:
            if not b.alive:
                continue
            b.x += b.vx
            b.y += b.vy
            # 画面外で消す（少し余白を持たせる）
            if b.x < -4 or b.x > self.w + 4 or b.y < -4 or b.y > self.h + 4:
                b.alive = False

    def draw(self):
        for b in self.pool:
            if b.alive:
                pyxel.circ(b.x, b.y, 0, b.c)
