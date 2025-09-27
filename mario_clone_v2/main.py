import pyxel as px
from player import Player
from stage import Stage

class App:
    def __init__(self):
        px.init(256, 256, title="Platformer Sample", fps=60)
        px.load("my_resource.pyxres")
        px.mouse(True)
        self.stage = Stage()
        self.player = Player(120, 120)
        px.run(self.update, self.draw)

    def update(self):
        self.player.update()
        self.stage.update()

    def draw(self):
        px.cls(0)
        px.text(10, 10, "Hello, Pyxel!", 7)
        self.stage.draw()
        self.player.draw()

if __name__ == "__main__":
    App()