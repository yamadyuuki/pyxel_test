import math
from .patterns import PatternFactory

# emitter.py（一例）
class Emitter:
    def __init__(self, x, y, bullets, patterns_data, factory=None):
        self.x, self.y = x, y
        self.bullets = bullets
        self.patterns_data = patterns_data
        self.factory = factory or PatternFactory(patterns_data)
        self.active = None
        self.active_name = None  # 追加：現在のパターン名を覚える

    def set_pattern(self, name: str):
        # すでに同じパターンなら「トグルOFF（停止）」にする
        if self.active_name == name and self.active is not None:
            self.active = None
            self.active_name = None
            # 止めたタイミングで弾を消す（要件次第でここは任意）
            self.bullets.clear_all()
            return

        # ここに来たら「別パターンに切替」
        # 切替時は既存弾を消してから新パターンをセット（順番はどちらでもOK）
        self.bullets.clear_all()
        self.active = self.factory.make(name)  # Circular / AimedBurst / Spinner を生成
        self.active_name = name

    def update(self, ctx):
        # パターン未設定 or 停止中
        if self.active is None:
            return
        # 現在パターンの1フレーム分を実行（必要なら弾をspawn）
        self.active.update_and_fire(self, ctx)
