import math

def deg2rad(d): return d * math.pi / 180.0

class BasePattern:
    def update_and_fire(self, emitter, ctx):
        raise NotImplementedError

class Circular(BasePattern):
    def __init__(self, speed, count, spread_deg=360, cooldown=30):
        self.speed = speed; self.count = count
        self.spread = spread_deg; self.cd = cooldown
        self.timer = 0

    def update_and_fire(self, em, ctx):
        if self.timer > 0:
            self.timer -= 1; return
        start = 0.0
        step = self.spread / self.count
        for i in range(self.count):
            a = deg2rad(start + i*step)
            em.bullets.spawn(em.x, em.y, math.cos(a)*self.speed, math.sin(a)*self.speed, r=1, c=10)
        self.timer = self.cd

class AimedBurst(BasePattern):
    def __init__(self, speed, count, interval=5):
        self.speed = speed; self.count = count; self.interval = interval
        self.i = 0; self.t = 0

    def update_and_fire(self, em, ctx):
        if self.i >= self.count: return
        if self.t % self.interval == 0:
            px, py = ctx["player_pos"]
            dx, dy = (px - em.x), (py - em.y)
            d = max(1e-5, math.hypot(dx, dy))
            vx, vy = (dx/d*self.speed, dy/d*self.speed)
            em.bullets.spawn(em.x, em.y, vx, vy, r=1, c=8)
            self.i += 1
        self.t += 1

class Spinner(BasePattern):
    def __init__(self, speed, count, angular_speed_deg=3, cooldown=3):
        self.speed = speed; self.count = count
        self.w = angular_speed_deg; self.cd = cooldown
        self.base = 0.0; self.timer = 0

    def update_and_fire(self, em, ctx):
        if self.timer > 0:
            self.timer -= 1; self.base += self.w; return
        step = 360 / self.count
        for i in range(self.count):
            a = deg2rad(self.base + i*step)
            em.bullets.spawn(em.x, em.y, math.cos(a)*self.speed, math.sin(a)*self.speed, r=1, c=9)
        self.base += self.w
        self.timer = self.cd

class RollingFire(BasePattern):
    """
    BulletML [1943]_rolling_fire の見た目を最小改修で再現:
      - 40+$rand*20 待機
      - 4fで相対-90度に向き変更
      - 4fで速度を最終値へ加速
      - 4f待機
      - 以降 毎フレーム +seq_deg 回転しながら一定間隔で1発ずつ発射
      - 最後に post_wait の待機後に停止
    """
    def __init__(
        self,
        speed_final=3.0,
        pre_wait=40,
        turn_rel_deg=-90,
        turn_term=4,
        accel_term=0, # 加速にかけるフレーム数
        micro_wait=4,
        seq_deg=15,
        post_wait=80,
        fire_interval=1,
        life=360,
        rand_wait_amplitude=20,   # XMLの +$rand*20 相当のゆらぎ（0で無効）
        seed=0
    ):
        import random
        self.rng = random.Random(seed)

        # 時間管理
        self.t = 0
        self.life = life

        # 角度と速度の状態（度で持つ）
        self.theta = 0.0
        self.speed = 0.0

        # フェーズ時間
        self.pre_wait = pre_wait + (self.rng.randrange(rand_wait_amplitude+1) if rand_wait_amplitude>0 else 0)
        self.turn_rel = turn_rel_deg
        self.turn_term = max(1, turn_term)
        self.accel_term = max(1, accel_term)
        self.micro_wait = micro_wait
        self.seq_deg = seq_deg
        self.post_wait = post_wait + (self.rng.randrange(rand_wait_amplitude+1) if rand_wait_amplitude>0 else 0)
        self.fire_interval = max(1, fire_interval)

        # 内部補間
        self.turn_per_frame = self.turn_rel / self.turn_term
        self.speed_start = 0.0
        self.speed_final = speed_final
        self.speed_step = (self.speed_final - self.speed_start) / self.accel_term

        # 連射用
        self.fire_clock = 0

        # フェーズ境界（フレーム絶対時刻）
        self.t0 = self.pre_wait
        self.t1 = self.t0 + self.turn_term
        self.t2 = self.t1 + self.accel_term
        self.t3 = self.t2 + self.micro_wait
        self.t4 = self.t3 + self.life         # 回転連射フェーズの長さ
        self.t5 = self.t4 + self.post_wait    # 終了

    def update_and_fire(self, em, ctx):
        # 時間更新
        t = self.t

        # --- フェーズ別処理 ---
        if t < self.t0:
            # 事前待機
            pass

        elif t < self.t1:
            # 方向変更を turn_term で線形に
            self.theta += self.turn_per_frame

        elif t < self.t2:
            # 速度を accel_term で線形加速
            self.speed += self.speed_step

        elif t < self.t3:
            # micro wait
            pass

        elif t < self.t4:
            # 以後は毎フレーム seq_deg で回しながら一定間隔で弾を1発
            if self.t >= self.t3:
                self.theta += self.seq_deg
            # 連射クロック
            if self.fire_clock % self.fire_interval == 0:
                a = deg2rad(self.theta)
                vx, vy = math.cos(a) * self.speed, math.sin(a) * self.speed
                em.bullets.spawn(em.x, em.y, vx, vy, r=1, c=14)  # 見やすい色
            self.fire_clock += 1

        elif t >= self.t5:
            # 終了（Emitter側でトグルOFFするのと同等の扱い）
            em.active = None
            em.active_name = None
            return

        self.t += 1

class PatternFactory:
    def __init__(self, patterns_data: dict):
        self.data = patterns_data

    def make(self, name: str):
        cfg = self.data[name]; typ = cfg["type"]
        if typ == "circular":
            return Circular(cfg["bullet_speed"], cfg["count"], cfg.get("spread_deg",360), cfg.get("cooldown",30))
        if typ == "aimed":
            return AimedBurst(cfg["bullet_speed"], cfg["count"], cfg.get("interval",5))
        if typ == "spinner":
            return Spinner(cfg["bullet_speed"], cfg["count"], cfg.get("angular_speed_deg",3), cfg.get("cooldown",3))

        # ← ここから追記
        if typ == "rolling_fire":
            return RollingFire(
                speed_final   = cfg.get("speed_final", 3.0),
                pre_wait      = cfg.get("pre_wait", 40),
                turn_rel_deg  = cfg.get("turn_rel_deg", -90),
                turn_term     = cfg.get("turn_term", 4),
                accel_term    = cfg.get("accel_term", 4),
                micro_wait    = cfg.get("micro_wait", 4),
                seq_deg       = cfg.get("seq_deg", 15),
                post_wait     = cfg.get("post_wait", 80),
                fire_interval = cfg.get("fire_interval", 1),
                life          = cfg.get("life", 360),
                rand_wait_amplitude = cfg.get("rand_wait_amplitude", 20),
                seed          = cfg.get("seed", 0),
            )
        # ここまで

        raise ValueError(f"unknown pattern: {typ}")
