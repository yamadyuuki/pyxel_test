

SPEED = 1.5

TILE_SIZE = 8

TILE_NONE = 0
TILE_GEM = 1
TILE_WEED = 2
TILE_GROUND = 3

TILE_TO_TILETYPE = {
    (1, 0): TILE_GEM,
    (0, 1): TILE_WEED,
    (1, 1): TILE_GROUND,
}

BLOCKING_TYPES = {TILE_WEED, TILE_GROUND}  # 進入禁止タイル

MAP_W = 512   #　マップ幅(単位:ピクセル)
MAP_H = 256   #　マップ高さ(単位:ピクセル)


# ===== ここから追加 =====
GRAVITY = 0.4          # 重力の強さ（落下の加速）
JUMP_POWER = 4       # ジャンプ初速（上向きはマイナスにするので使う時は -JUMP_POWER）
MAX_FALL_SPEED = 10.0  # 落下の終端速度（速くなりすぎ防止）
AIR_CONTROL = 1.0      # 空中での左右操作の効き具合（1.0なら地上と同じ）
# ===== 追加ここまで =====

COYOTE_FRAMES = 6     # コヨーテタイム（接地後もジャンプできる猶予時間、単位:フレーム）

JUMP_BUFFER_FRAMES = 10 # ジャンプバッファ（ジャンプ入力を先行して受け付ける猶予時間、単位:フレーム）