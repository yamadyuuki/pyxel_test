import pyxel

class TitleScene:
    def __init__(self, game):
        self.game = game # ゲームクラス:
        self.alpha = 0.0 # 画面の透明度(0.0:透明, 1.0:不透明)
        
    def update(self):
        # 画面の透明度を変更する
        if self.alpha < 1.0:
            self.alpha += 0.015
        
        # キー入力をチェックする
        if pyxel.btnp(pyxel.KEY_RETURN):
            # 画面の透明度を不透明にする
            pyxel.dither(1.0)

            #プレイ画面に切り替える
            self.game.change_scene("play")

    def draw(self):
        pyxel.cls(0)
        pyxel.dither(self.alpha)
        pyxel.bltm(0, 0, 1, 0, 0, 256, 256)
        pyxel.blt(0, 64, 0, 0, 48, 64, 16, 0)
           # テキストを描画する
        pyxel.rect(30, 97, 67, 11, 0)
        pyxel.text(34, 100, "PRESS ENTER KEY", 7)
