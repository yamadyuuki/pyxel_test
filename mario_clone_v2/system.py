#衝突判定や重力
import pyxel as px
from constants import TILE_SIZE, TILE_TO_TILETYPE, TILE_NONE, BLOCKING_TYPES, MAP_W, MAP_H, TILE_GEM

def clamp(v, lo, hi):
    return max(lo, min(v, hi))

def get_tile_type(x, y):
    """ワールド座標(x,y)にあるタイルタイプを返す"""
    tx = x // TILE_SIZE
    ty = y // TILE_SIZE
    tile = px.tilemaps[0].pget(tx, ty)  # (u, v) タプル
    return TILE_TO_TILETYPE.get(tile, TILE_NONE)

def set_tile_empty(x, y):
    """指定座標のタイルを空に設定"""
    tx = x // TILE_SIZE
    ty = y // TILE_SIZE
    px.tilemaps[0].pset(tx, ty, (0, 0))  # 空のタイルに設定

def is_block_at(x, y):
    """その座標にブロックタイルがあるか"""
    # 画面下は落下判定のためFalseに、上と左右はTrue
    if x < 0 or x >= MAP_W:
        return True
    if y < 0:
        return True
    if y >= MAP_H:
        return False  # 画面下は落下可能
    tile_type = get_tile_type(x, y)
    
    # 通常のブロック判定
    if tile_type in BLOCKING_TYPES:
        return True
    
    # 家の特別判定: 家は16x16ピクセル（2x2タイル）なので
    # 家タイルの左上から1タイル分の範囲も進入禁止とする
    # タイルマップ上の位置を計算
    tx, ty = x // TILE_SIZE, y // TILE_SIZE
    
    return False

def rect_hits_block(x, y, w, h):
    """矩形がブロックタイルに重なっているか（複数点チェック）"""
    ε = 0  # スキン幅（端ピッタリではなく内側で判定）

    # 上辺チェック（左・中央・右）
    if (
        is_block_at(x + ε,       y)
        or is_block_at(x + w // 2, y)
        or is_block_at(x + w - 1 - ε, y)
    ):
        return True

    # 下辺チェック（左・中央・右）
    if (
        is_block_at(x + ε,       y + h - 1)
        or is_block_at(x + w // 2, y + h - 1)
        or is_block_at(x + w - 1 - ε, y + h - 1)
    ):
        return True

    # 左辺チェック（上・中央・下）
    if (
        is_block_at(x, y + ε)
        or is_block_at(x, y + h // 2)
        or is_block_at(x, y + h - 1 - ε)
    ):
        return True

    # 右辺チェック（上・中央・下）
    if (
        is_block_at(x + w - 1, y + ε)
        or is_block_at(x + w - 1, y + h // 2)
        or is_block_at(x + w - 1, y + h - 1 - ε)
    ):
        return True

    return False

def _move_axis_pushback(x, y, w, h, delta, axis):
    """
    axis: 'x' or 'y'
    delta: 目標移動量（正負のfloat）
    1pxずつ進め、ブロックに当たったらそこで止める
    """
    if delta == 0:
        return x, y

    # 何pxぶん進めるか（小数でも天井切り上げで確実に回数を回す）
    steps = px.ceil(abs(delta))
    # 1ステップの符号（+1 or -1）
    step = 1 if delta > 0 else -1

    for _ in range(steps):
        nx, ny = x, y
        if axis == 'x':
            nx = x + step
        else:
            ny = y + step

        # マップ外に出ないようクランプ（上と左右のみ、下は落下判定のため制限なし）
        nx = clamp(nx, 0, MAP_W - w)
        ny = max(0, ny)  # 上だけ制限

        # 次の位置で衝突するか？
        if rect_hits_block(nx, ny, w, h):
            # ここでストップ（これ以上は進めない）
            break

        # 衝突しなければ1px進める
        x, y = nx, ny

    return x, y

def rect_move(x, y, w, h, dx, dy):
    """
    連続衝突検出（push-back）版の移動。
    まずY軸方向に1pxずつ進め、衝突したら止める。
    次にX軸方向も同様に進める。
    """
    # --- Y軸を先に処理 ---
    x, y = _move_axis_pushback(x, y, w, h, dy, axis='y')
    # --- X軸を次に処理 ---
    x, y = _move_axis_pushback(x, y, w, h, dx, axis='x')
    return x, y


# def check_item_collection(player):
#     """プレイヤーの周囲のアイテム収集判定"""
#     # プレイヤーの周囲8点をチェック
#     for i in [0, 7, 15]:  # 上端、中央、下端
#         for j in [0, 7, 15]:  # 左端、中央、右端
#             check_x = player.x + j
#             check_y = player.y + i
#             tile_type = get_tile_type(check_x, check_y)

#             # 宝石の場合
#             if tile_type == TILE_GEM:
#                 # 宝石を収集（タイルを空に設定）
#                 set_tile_empty(check_x, check_y)
#                 player.gems_collected += 1
#                 px.play(0,0)  # 効果音再生（チャンネル0、サウンド0）

def _tile_range_from_rect(x, y, w, h):
    """ピクセル矩形 -> タイル範囲（含む）を返す（tx0..tx1, ty0..ty1）"""
    tx0 = max(0, (x) // TILE_SIZE)
    ty0 = max(0, (y) // TILE_SIZE)
    tx1 = min((MAP_W - 1) // TILE_SIZE, (x + w - 1) // TILE_SIZE)
    ty1 = min((MAP_H - 1) // TILE_SIZE, (y + h - 1) // TILE_SIZE)
    return tx0, ty0, tx1, ty1

def iter_gem_tiles_in_rect(x, y, w, h):
    """矩形に重なるタイルのうち GEM のある (tx, ty) を列挙（副作用なし）"""
    tx0, ty0, tx1, ty1 = _tile_range_from_rect(x, y, w, h)
    for ty in range(ty0, ty1 + 1):
        for tx in range(tx0, tx1 + 1):
            u, v = px.tilemaps[0].pget(tx, ty)  
            tile_type = TILE_TO_TILETYPE.get((u, v), TILE_NONE)
            if tile_type == TILE_GEM:
                yield tx, ty

def collect_gems_in_rect(x, y, w, h):
    """
    矩形に重なる GEM タイルを収集して空にする。
    戻り値: 収集した数（音などの副作用は呼び出し側に任せる）
    """
    count = 0
    for tx, ty in iter_gem_tiles_in_rect(x, y, w, h):
        px.tilemaps[0].pset(tx, ty, (0, 0))  # 空タイルに
        count += 1
    return count