import pyxel
from play import *

class SceneManager:
    def __init__(self, app):
        self.app = app
        self._registry = {}   # {"title": TitleScene, ...}
        self.current = None

    def register(self, name, ctor):
        self._registry[name] = ctor

    def change(self, name, **kwargs):
        if self.current:
            self.current.on_exit()
        # ← ここが「毎回 new する」ポイント
        self.current = self._registry[name](self.app)
        self.current.on_enter(**kwargs)

    def update(self):
        if self.current: self.current.update()

    def draw(self):
        if self.current: self.current.draw()

class App:
    def __init__(self):
        pyxel.init(256, 128, fps=60)
        pyxel.load("my_resource.pyxres")  # リソースファイルをロード
        self.scenes = SceneManager(self)
        self.scenes.register("title", TitleScene)
        self.scenes.register("play",  PlayScene)
        self.scenes.change("title")
        pyxel.run(self.update, self.draw)

    def update(self):
        self.scenes.update()

    def draw(self):
        pyxel.cls(1)
        self.scenes.draw()

if __name__ == "__main__":
    App()