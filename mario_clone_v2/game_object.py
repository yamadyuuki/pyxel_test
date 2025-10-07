# game_object.py
import pyxel as px

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
