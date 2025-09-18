# core/world.py
import json
import pyxel
from .bullet import BulletSystem
from .emitter import Emitter
from .timeline import Timeline
from .ui import PatternMenu
from .player import Player

class Enemy:
    def __init__(self, x, y, hp, timeline, emitter):
        self.x, self.y = x, y
        self.hp = hp
        self.timeline = timeline
        self.emitter = emitter

    def update(self, t, ctx, use_timeline=True):
        self.emitter.x, self.emitter.y = self.x, self.y
        if use_timeline:
            self.timeline.tick(t, self.emitter, ctx)
        self.emitter.update(ctx)

    def draw(self):
        pyxel.circ(self.x, self.y, 3, 8)

class World:
    def __init__(self, W, H, panel_w=70):
        self.W, self.H = W, H
        self.panel_w = panel_w
        self.t = 0
        self.timeline_enabled = False
        self.bullets = BulletSystem(W + panel_w, H)  # 弾は全画面で生かす

        with open("data/patterns_demo.json","r",encoding="utf-8") as f:
            self.patterns_data = json.load(f)["patterns"]
        with open("data/stage01.json","r",encoding="utf-8") as f:
            stage = json.load(f)

        self.enemies = []
        for e in stage["enemies"]:
            tl = Timeline(e["script"])
            em = Emitter(e["x"], e["y"], self.bullets, self.patterns_data)
            self.enemies.append(Enemy(e["x"], e["y"], e.get("hp", 1), tl, em))

        # 右パネル：データにあるパターンキーを一覧表示
        items = list(self.patterns_data.keys())
        panel_x = self.W  # ゲーム領域の右隣から開始
        self.menu = PatternMenu(panel_x, 0, self.panel_w, self.H, items)
        left_area_w = self.W  # 右パネルを除いた左エリアの幅
        self.player = Player(
            x=left_area_w // 2,
            y=self.H // 2,
            left_area_w=left_area_w,
            h=self.H,
            radius=1,
            color=3,  # 緑の点
        )        

    def update(self):
        ctx = {"player_pos": (self.player.x, self.player.y)}
        self.player.update()
        decided = self.menu.handle_input()
        if decided:
            # ひとまず先頭の敵の発射器に適用（必要なら選択中の敵に拡張）
            if self.enemies:
                self.enemies[0].emitter.set_pattern(decided)
            # self.timeline_enabled = True

        for enemy in self.enemies:
            enemy.update(self.t, ctx, use_timeline=self.timeline_enabled)

        self.bullets.update()

        self.t += 1

    def draw(self):
        # 左：ゲーム領域のガイド（任意）
        pyxel.rectb(0, 0, self.W, self.H, 13)
        for enemy in self.enemies:
            enemy.draw()
        self.bullets.draw()
        self.player.draw()
        
        # 右：メニュー
        self.menu.draw("PATTERNS")
