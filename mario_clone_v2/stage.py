import pyxel as px

class Stage:
    def __init__(self):
        pass

    def update(self):
        pass

    def draw(self):
        px.cls(5)
        px.bltm(0, 0, 0, 0, 0, 1024, 256, colkey=0)