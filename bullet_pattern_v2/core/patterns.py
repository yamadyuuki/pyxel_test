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

class HomingLaserApprox(BasePattern):
    """
    元XMLの要旨（簡略）:
      - 8回くり返し:
        - 基準角(base)に向けて1発撃ち、さらに1fおきに同角で8連射 → 10fウェイト
      - 弾側ロジック:
        - 速度 2 → 0.3（30fで減速）→ 100f待ち → 5（100fで加速）
        - かつ「ターゲット方向へ term=60-$rank*20 で向きを合わせる」を繰り返し
    近似方針:
      - 弾の“曲げ”は未実装なので、将来の弾のみが追尾角度に寄る＝「都度 再照準して撃つ」
      - 速度段階は「時間帯で弾速を切替」する近似
    参照: [G_DARIUS]_homing_laser.xml
    """
    def __init__(self,
                 base_spread_deg=120, repeats=8, cluster=9, interval_in_cluster=1, wait_between=10,
                 slow_speed=2.0, slow_term=30, coast_wait=100, fast_speed=5.0, fast_term=100,
                 aim_term=60, aim_step_max_deg=6, seed=0):
        import random
        self.rng = random.Random(seed)

        # パターン全体の時計
        self.t = 0

        # 射出仕様
        self.base_spread = base_spread_deg          # -spread/2 .. +spread/2
        self.repeats = repeats
        self.cluster = cluster                      # 1f刻みで同角連射する弾数
        self.interval_in_cluster = max(1, interval_in_cluster)
        self.wait_between = wait_between

        # 速度段階（時間帯で切替する近似）
        self.slow_speed = slow_speed
        self.slow_term = slow_term
        self.coast_wait = coast_wait
        self.fast_speed = fast_speed
        self.fast_term = fast_term

        # 追尾（未来の弾の照準角のみ反映）
        self.aim_term = max(1, aim_term)            # だいたい60fで追いつく想定
        self.aim_step_max = aim_step_max_deg

        # 現在の基準角
        self.base_angle = self.rng.uniform(-self.base_spread/2, self.base_spread/2)

        # 状態
        self.phase = 0
        self.fired_in_cluster = 0
        self.wait_timer = 0
        self.done_repeat = 0
        self.cluster_tick = 0

    def _current_speed(self):
        # 時間帯で弾速を切替（減速→待機→加速の雰囲気を近似）
        if self.t < self.slow_term:
            return self.slow_speed
        if self.t < self.slow_term + self.coast_wait:
            return max(0.3, self.slow_speed * 0.5)  # “0.3へ減速＆惰行”の雰囲気
        # 以降は速いレーザー風
        return self.fast_speed

    def _aim_step(self, em, ctx):
        # プレイヤー方向に少しずつ基準角を寄せる（未来の弾にだけ効く）
        px, py = ctx["player_pos"]
        dx, dy = (px - em.x), (py - em.y)
        target = math.degrees(math.atan2(dy, dx))
        # 角度差を -180..180 に正規化
        diff = (target - self.base_angle + 180) % 360 - 180
        step = max(-self.aim_step_max, min(self.aim_step_max, diff / self.aim_term))
        self.base_angle += step

    def update_and_fire(self, em, ctx):
        # 毎フレーム少しずつ照準角を寄せる（未来の弾に反映）
        self._aim_step(em, ctx)

        # クラスタ連射中
        if self.fired_in_cluster < self.cluster:
            if self.cluster_tick % self.interval_in_cluster == 0:
                a = deg2rad(self.base_angle)
                v = self._current_speed()
                em.bullets.spawn(em.x, em.y, math.cos(a)*v, math.sin(a)*v, r=1, c=7)
                self.fired_in_cluster += 1
            self.cluster_tick += 1

        # クラスタ完了 → インターバル待ち
        elif self.wait_timer < self.wait_between:
            self.wait_timer += 1

        # 次クラスタへ
        else:
            self.done_repeat += 1
            if self.done_repeat >= self.repeats:
                em.active = None
                em.active_name = None
                return
            # 次クラスタのセットアップ
            # 初弾は「-spread..+spread」のどこかから開始
            self.base_angle = self.rng.uniform(-self.base_spread/2, self.base_spread/2)
            self.fired_in_cluster = 0
            self.cluster_tick = 0
            self.wait_timer = 0

        self.t += 1


# === [Guwange] Round 2 Boss: Circle Fire（近似版） ============
class CircleFireApprox(BasePattern):
    """
    元XMLの要旨（簡略）:
      - fireRef circle を18回（=20度刻みで一周）
        - “外殻” bullet: speed=6 で飛び、3f後に
          その位置から “子弾” を absolute=$2, speed=1.5+$rank で発射、親は消える
      - top で子弾の絶対角 $2 を 180-45+90*$rand に決定
    近似方針:
      - 親弾の移動は弾クラスを使わず、パターン内部で「3f後の位置 = 発射点 + 速度*3」で子弾を直接spawn
      - これで “リングから子弾が生まれる”見た目を再現
    参照: [Guwange]_round_2_boss_circle_fire.xml
    """
    def __init__(self,
                 ring_count=18, step_deg=20,
                 shell_speed=6.0, shell_delay=3,
                 child_abs_deg=None, child_speed=1.5,
                 color_shell=10, color_child=8,
                 seed=0):
        import random
        self.rng = random.Random(seed)
        self.t = 0

        self.ring_count = ring_count
        self.step_deg = step_deg
        self.shell_speed = shell_speed
        self.shell_delay = shell_delay
        self.child_speed = child_speed

        # 子弾の絶対角（指定なければ 180-45+90*rand）
        self.child_abs = (180 - 45 + 90 * self.rng.random()) if child_abs_deg is None else child_abs_deg

        self.color_shell = color_shell
        self.color_child = color_child

        # 角度シーケンスの基準（開始角は0でOK）
        self.base = 0.0

        # “3f後に子弾を撃つべき位置”を積むキュー: (fire_frame, x, y)
        self.queue = []

        # 一周したら終了
        self.done = False

    def update_and_fire(self, em, ctx):
        if self.done:
            em.active = None
            em.active_name = None
            return

        # 1周ぶんの外殻を瞬間生成し、子弾予定をキューに積む
        if self.t == 0:
            for i in range(self.ring_count):
                ang = self.base + i * self.step_deg
                a = deg2rad(ang)
                # 外殻の見栄え（任意）：点を置いて視覚的にリングを出す
                em.bullets.spawn(em.x, em.y, math.cos(a)*self.shell_speed, math.sin(a)*self.shell_speed, r=1, c=self.color_shell)
                # shell_delay フレーム後の位置を計算して、そこで子弾を撃つ
                x2 = em.x + math.cos(a) * self.shell_speed * self.shell_delay
                y2 = em.y + math.sin(a) * self.shell_speed * self.shell_delay
                self.queue.append((self.t + self.shell_delay, x2, y2))

        # 子弾の射出：予定時刻に到達したものを発射
        # （absolute=self.child_abs）
        while self.queue and self.queue[0][0] <= self.t:
            _, sx, sy = self.queue.pop(0)
            ca = deg2rad(self.child_abs)
            vx, vy = math.cos(ca)*self.child_speed, math.sin(ca)*self.child_speed
            em.bullets.spawn(sx, sy, vx, vy, r=1, c=self.color_child)

        # 一巡処理が済んだら数フレで終わり
        if not self.queue:
            # 余韻を少しだけ与えて終了
            if self.t > self.shell_delay + 2:
                self.done = True

        self.t += 1

class AimedNWay(BasePattern):
    """
    プレイヤー方向を中心に、左右対称のN-way（扇形）に発射する。
    ways: 方向数（奇数の場合は中央1本＋左右対称、偶数の場合は中央が谷で左右対称）
    spread_deg: 全体の扇角（例: 40なら -20..+20 を等間隔）
    cooldown: 次の扇を撃つまでの待ちフレーム
    """
    def __init__(self, bullet_speed=0.5, ways=5, spread_deg=40, cooldown=20, color=10):
        self.v = bullet_speed
        self.ways = max(2, ways)
        self.spread = float(spread_deg)
        self.cd = max(0, cooldown)
        self.timer = 0
        self.color = color

    def update_and_fire(self, em, ctx):
        if self.timer > 0:
            self.timer -= 1
            return
        # 中心角度（プレイヤー方向）
        px, py = ctx["player_pos"]
        dx, dy = (px - em.x), (py - em.y)
        base = math.degrees(math.atan2(dy, dx))

        if self.ways == 1:
            angles = [base]
        else:
            step = self.spread / (self.ways - 1)
            start = base - self.spread * 0.5
            angles = [start + i * step for i in range(self.ways)]

        for deg in angles:
            a = deg2rad(deg)
            em.bullets.spawn(
                em.x, em.y,
                math.cos(a) * self.v, math.sin(a) * self.v,
                r=1, c=self.color
            )
        self.timer = self.cd

class TwoSplitFanApprox(BasePattern):
    """
    最初に“親弾2発”を撃ち、一定距離(=travel_frames)直進した位置から
    親の向き±child_fan_degで“子弾”を左右に分岐させる近似。
    親弾はそのまま飛び続ける（消去はしない）。
    """
    def __init__(self,
                 initial_speed=1.0,
                 initial_offset_deg=8,     # 中心(=狙い角)から±この角度で2発
                 travel_frames=12,         # 何フレーム直進した地点で分岐するか
                 child_speed=1.2,
                 child_fan_deg=30,         # 親の角度から±この角度に子弾
                 cooldown=45,              # 次の2分岐を撃つまでの待ち
                 color_parent=11, color_child=14,
                 aimed=True,               # Trueならプレイヤー狙い、Falseなら下向き(90deg)
                 seed=0):
        import random
        self.rng = random.Random(seed)
        self.t = 0
        self.cooldown = cooldown
        self.timer = 0

        self.v0 = initial_speed
        self.off = float(initial_offset_deg)
        self.n_delay = max(1, travel_frames)

        self.vc = child_speed
        self.fan = float(child_fan_deg)

        self.cP = color_parent
        self.cC = color_child
        self.aimed = aimed

        # “travel後に子弾を撃つべき座標”を積むキュー: (spawn_frame, x, y, base_angle_deg)
        self.queue = []

    def _base_angle(self, em, ctx):
        if self.aimed:
            px, py = ctx["player_pos"]
            dx, dy = (px - em.x), (py - em.y)
            return math.degrees(math.atan2(dy, dx))
        else:
            return 90.0  # 画面下向き

    def update_and_fire(self, em, ctx):
        # travel後の子弾スポーン処理
        while self.queue and self.queue[0][0] <= self.t:
            _, sx, sy, base_deg = self.queue.pop(0)
            for d in (-self.fan, +self.fan):
                a = deg2rad(base_deg + d)
                em.bullets.spawn(sx, sy, math.cos(a)*self.vc, math.sin(a)*self.vc, r=1, c=self.cC)

        # クールダウン中なら待つ
        if self.timer > 0:
            self.timer -= 1
            self.t += 1
            return

        # 新しい“2分岐セット”を撃つ
        base = self._base_angle(em, ctx)
        for sign in (-1, +1):
            ang = base + sign * self.off
            a = deg2rad(ang)
            # 親弾を発射（見た目の“直進”）
            em.bullets.spawn(em.x, em.y, math.cos(a)*self.v0, math.sin(a)*self.v0, r=1, c=self.cP)
            # travel_frames 後の位置を計算して、そこから子弾を左右に分岐
            sx = em.x + math.cos(a) * self.v0 * self.n_delay
            sy = em.y + math.sin(a) * self.v0 * self.n_delay
            self.queue.append((self.t + self.n_delay, sx, sy, ang))

        # 次のセットまで待つ
        self.timer = self.cooldown
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

        # --- ここから追記 ---
        if typ == "homing_laser":
            return HomingLaserApprox(
                base_spread_deg      = cfg.get("base_spread_deg", 120),
                repeats              = cfg.get("repeats", 8),
                cluster              = cfg.get("cluster", 9),
                interval_in_cluster  = cfg.get("interval_in_cluster", 1),
                wait_between         = cfg.get("wait_between", 10),
                slow_speed           = cfg.get("slow_speed", 2.0),
                slow_term            = cfg.get("slow_term", 30),
                coast_wait           = cfg.get("coast_wait", 100),
                fast_speed           = cfg.get("fast_speed", 5.0),
                fast_term            = cfg.get("fast_term", 100),
                aim_term             = cfg.get("aim_term", 60),
                aim_step_max_deg     = cfg.get("aim_step_max_deg", 6),
                seed                 = cfg.get("seed", 0),
            )
        if typ == "circle_fire":
            return CircleFireApprox(
                ring_count   = cfg.get("ring_count", 18),
                step_deg     = cfg.get("step_deg", 20),
                shell_speed  = cfg.get("shell_speed", 6.0),
                shell_delay  = cfg.get("shell_delay", 3),
                child_abs_deg= cfg.get("child_abs_deg", None),
                child_speed  = cfg.get("child_speed", 1.5),
                color_shell  = cfg.get("color_shell", 10),
                color_child  = cfg.get("color_child", 8),
                seed         = cfg.get("seed", 0),
            )

        if typ == "nway_aimed":
            return AimedNWay(
                bullet_speed = cfg.get("bullet_speed", 0.5),
                ways         = cfg.get("ways", 5),
                spread_deg   = cfg.get("spread_deg", 40),
                cooldown     = cfg.get("cooldown", 20),
                color        = cfg.get("color", 10),
            )
        
        if typ == "two_split":
            return TwoSplitFanApprox(
                initial_speed = cfg.get("initial_speed", 1.0),
                initial_offset_deg = cfg.get("initial_offset_deg", 8),
                travel_frames = cfg.get("travel_frames", 12),
                child_speed   = cfg.get("child_speed", 1.2),
                child_fan_deg = cfg.get("child_fan_deg", 30),
                cooldown      = cfg.get("cooldown", 45),
                color_parent  = cfg.get("color_parent", 11),
                color_child   = cfg.get("color_child", 14),
                aimed         = cfg.get("aimed", True),
                seed          = cfg.get("seed", 0),
            )
        
        raise ValueError(f"unknown pattern: {typ}")
