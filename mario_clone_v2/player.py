import pyxel as px
from constants import SPEED
from collision import rect_move

class GameObject:
    def __init__(self, x, y, img, u, v, w, h, colkey=0):
        self.x = x
        self.y = y
        self.img = img
        self.u = u
        self.v = v
        self.w = w
        self.h = h
        self.colkey = colkey
    
    def draw(self):
        px.blt(self.x, self.y, self.img, self.u, self.v, self.w, self.h, self.colkey)

class Player(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y, 0, 16, 0, 16, 16, 0)
        self.facing = True  # false: 左向き, true: 右向き

    def update(self):
        dx = (px.btn(px.KEY_RIGHT) - px.btn(px.KEY_LEFT)) * SPEED
        dy = (px.btn(px.KEY_DOWN) - px.btn(px.KEY_UP)) * SPEED
            #右向き
        if dx > 0:
            self.facing = True
            #左向き
        elif dx < 0:
            self.facing = False

        self.x, self.y = rect_move(self.x, self.y, self.w, self.h, dx, dy)      

    def draw(self):
        if self.facing:
            px.blt(self.x, self.y, self.img, self.u, self.v, self.w, self.h, self.colkey)
        else:
            px.blt(self.x, self.y, self.img, self.u , self.v, -self.w, self.h, self.colkey)

