# bullet.py 置き換え

import pyxel
import math

class Bullet:
    __slots__ = ("x","y","vx","vy","r","c","alive","t","life","behavior")
    def __init__(self):
        self.alive = False
        self.x = self.y = 0.0
        self.vx = self.vy = 0.0
        self.r = 0
        self.c = 7
        self.t = 0
        self.life = -1        # -1 は無制限
        self.behavior = None  # dict | None

class BulletSystem:
    def __init__(self, w, h, capacity=512):
        self.w, self.h = w, h
        self.capacity = capacity
        self.pool = [Bullet() for _ in range(capacity)]

    def clear_all(self):
        for b in self.pool:
            b.alive = False

    def spawn(self, x, y, vx, vy, r=1, c=7, life=-1, behavior=None):
        for b in self.pool:
            if not b.alive:
                b.alive = True
                b.x, b.y = x, y
                b.vx, b.vy = vx, vy
                b.r, b.c = r, c
                b.t = 0
                b.life = life
                b.behavior = behavior
                return b
        return None

    def update(self, ctx=None):
        # ctx からプレイヤー座標（なければ None）
        px, py = (None, None)
        if ctx and "player_pos" in ctx:
            px, py = ctx["player_pos"]

        for b in self.pool:
            if not b.alive:
                continue

            # --- ふるまい（任意） ---
            beh = b.behavior
            if beh:
                typ = beh.get("type")

                # 1) 重力（引力/斥力）
                if typ == "grav" and px is not None:
                    g = float(beh.get("g", 0.03))
                    mode = beh.get("mode", "attract")
                    vmax = float(beh.get("max_speed", 3.0))
                    dx, dy = (px - b.x), (py - b.y)
                    d = max(1e-5, math.hypot(dx, dy))
                    ax, ay = g * (dx/d), g * (dy/d)
                    if mode == "repel":
                        ax, ay = -ax, -ay
                    b.vx += ax; b.vy += ay
                    spd = math.hypot(b.vx, b.vy)
                    if spd > vmax:
                        k = vmax / spd
                        b.vx *= k; b.vy *= k

                # 2) 変速スケジュール
                elif typ == "speed_schedule":
                    for step in beh.get("steps", []):
                        if b.t == int(step.get("at", -1)):
                            spd = max(0.0, float(step.get("speed", 0.0)))

                            # --- ここを修正 ---
                            if spd > 0 and "aim_player" in beh and beh["aim_player"]:
                                # ctx からプレイヤー座標を取る
                                if ctx and "player_pos" in ctx:
                                    px, py = ctx["player_pos"]
                                    dx, dy = px - b.x, py - b.y
                                    ang = math.atan2(dy, dx)
                                else:
                                    ang = 0.0
                            else:
                                # 従来通り：現在の進行方向を保持
                                ang = math.atan2(b.vy, b.vx) if (b.vx or b.vy) else 0.0

                            # 新しい速度ベクトルに置き換え
                            b.vx = math.cos(ang) * spd
                            b.vy = math.sin(ang) * spd
                            
                                                       
                # 3) 近接爆発
                elif typ == "proximity_burst" and px is not None:
                    rad = float(beh.get("radius", 18))
                    if (px - b.x)**2 + (py - b.y)**2 <= rad*rad:
                        ch = beh.get("child", {})
                        n   = int(ch.get("count", 12))
                        v   = float(ch.get("speed", 1.2))
                        col = int(ch.get("color", 10))
                        for i in range(n):
                            a = (2*math.pi) * (i / n)
                            self.spawn(b.x, b.y, math.cos(a)*v, math.sin(a)*v, r=1, c=col)
                        if beh.get("once", True):
                            b.alive = False
                            continue  # 親が消えたので位置更新へ進まず次弾へ

            # 位置・寿命
            b.x += b.vx
            b.y += b.vy
            b.t += 1
            if b.life >= 0 and b.t >= b.life:
                b.alive = False

            # 画面外で消す
            if b.x < -4 or b.x > self.w + 4 or b.y < -4 or b.y > self.h + 4:
                b.alive = False

    def draw(self):
        for b in self.pool:
            if b.alive:
                pyxel.circ(b.x, b.y, 0, b.c)
