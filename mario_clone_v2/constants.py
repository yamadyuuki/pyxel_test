

SPEED = 1.5            # 移動速度（ピクセル/フレーム）

TILE_SIZE = 8

TILE_NONE = 0
TILE_GEM = 1
TILE_WEED = 2
TILE_GROUND = 3
TILE_PLATFORM = 4

TILE_TO_TILETYPE = {
    (1, 0): TILE_GEM,
    (0, 1): TILE_WEED,
    (1, 1): TILE_GROUND,
    (2, 2): TILE_PLATFORM,
}

BLOCKING_TYPES = {TILE_WEED, TILE_GROUND, TILE_PLATFORM}  # 進入禁止タイル

MAP_W = 1024   #　マップ幅(単位:ピクセル)
MAP_H = 256   #　マップ高さ(単位:ピクセル)


# ===== ここから追加 =====
GRAVITY = 0.4          # 重力の強さ（落下の加速）
JUMP_POWER = 4       # ジャンプ初速（上向きはマイナスにするので使う時は -JUMP_POWER）
MAX_FALL_SPEED = 10.0  # 落下の終端速度（速くなりすぎ防止）
AIR_CONTROL = 1.0      # 空中での左右操作の効き具合（1.0なら地上と同じ）
# ===== 追加ここまで =====

COYOTE_FRAMES = 6     # コヨーテタイム（接地後もジャンプできる猶予時間、単位:フレーム）

JUMP_BUFFER_FRAMES = 12 # ジャンプバッファ（ジャンプ入力を先行して受け付ける猶予時間、単位:フレーム）

ENEMY_IMG = 0       # イメージバンク番号（Pyxelエディタで作った画像バンク）
ENEMY_U = 0         # スプライト左上のx座標（ピクセル単位）
ENEMY_V = 16        # スプライト左上のy座標（ピクセル単位）
ENEMY_W = 16        # 幅（ピクセル）
ENEMY_H = 16        # 高さ（ピクセル）
ENEMY_COLKEY = 0    # 透明色のキー（背景色のインデックス）
ENEMY_SPAWN_Y = MAP_H - 40 # 敵の初期Y座標

ENEMY_SPAWN_POSITIONS = [
       (100, ENEMY_SPAWN_Y),
       (150, ENEMY_SPAWN_Y),
       (200, ENEMY_SPAWN_Y),
   ]