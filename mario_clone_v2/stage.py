import pyxel as px
from constants import MAP_W, MAP_H
class Stage:
    def __init__(self):
        pass

    def update(self):
        pass

    def draw(self):
        px.cls(5)
        px.bltm(0, 0, 0, 0, 0, MAP_W, MAP_H, colkey=0)
        