# player.py
import pyxel

class Player:
    def __init__(self, x: int, y: int, left_area_w: int, h: int, radius: int = 1, color: int = 3):
        """
        left_area_w: 右パネルを除いた左のプレイエリア幅
        h          : 画面高さ
        """
        self.x = x
        self.y = y
        self.w = left_area_w
        self.h = h
        self.r = radius
        self.color = color  # Pyxelの緑系。3=green

        self.speed = 1

    def update(self):
        dx = dy = 0
        if pyxel.btn(pyxel.KEY_LEFT):
            dx -= self.speed
        if pyxel.btn(pyxel.KEY_RIGHT):
            dx += self.speed
        if pyxel.btn(pyxel.KEY_UP):
            dy -= self.speed
        if pyxel.btn(pyxel.KEY_DOWN):
            dy += self.speed

        self.x += dx
        self.y += dy

        # 画面端＆右パネル手前でクリップ
        if self.x < self.r:
            self.x = self.r
        if self.y < self.r:
            self.y = self.r
        if self.x > self.w - 1 - self.r:
            self.x = self.w - 1 - self.r
        if self.y > self.h - 1 - self.r:
            self.y = self.h - 1 - self.r

    def draw(self):
        pyxel.circ(self.x, self.y, self.r, self.color)
