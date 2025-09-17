# ui.py
import pyxel
from typing import Optional, List, Tuple

class PatternMenu:
    def __init__(self, x: int, y: int, w: int, h: int, items: List[str]):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.items = list(items)
        self.sel = 0
        self.scroll = 0
        self.row_h = 10           # 行高を少し広めに
        self.margin = 4
        self.title_h = 10
        self.hover_idx: Optional[int] = None
        self._pressing = False    # ボタン押下中
        # --- スクロールバー用 ---
        self._dragging_bar = False
        self._drag_offset = 0     # バー内で掴んだYオフセット
        self._bar_rect: Tuple[int, int, int, int] = (0, 0, 0, 0)  # (x,y,w,h) キャッシュ

    # ====== 内部ユーティリティ ======
    def _content_top(self) -> int:
        return self.y + self.margin + self.title_h

    def _visible_rows(self) -> int:
        return max(1, (self.h - self.margin * 2 - self.title_h) // self.row_h)

    def _index_at(self, mx: int, my: int) -> Optional[int]:
        start_y = self._content_top()
        end_y = self.y + self.h - self.margin
        if not (self.x <= mx < self.x + self.w and start_y <= my < end_y):
            return None
        idx = (my - start_y) // self.row_h + self.scroll
        return idx if 0 <= idx < len(self.items) else None

    def _calc_bar(self) -> Tuple[int, int, int, int]:
        """スクロールバー矩形 (x, y, w, h) を返す"""
        vis = self._visible_rows()
        if len(self.items) <= vis:
            return (0, 0, 0, 0)  # バー不要
        track_x = self.x + self.w - 5
        track_y = self.y + self.title_h + 5
        track_h = self.h - self.title_h - 10
        # バーの高さは可視率に応じて
        bar_h = max(8, int(vis / len(self.items) * track_h))
        # スクロール位置を0..1に正規化
        max_scroll = max(1, len(self.items) - vis)
        t = min(max(0, self.scroll), max_scroll) / max_scroll
        bar_y = track_y + int((track_h - bar_h) * t)
        return (track_x, bar_y, 3, bar_h)

    def _scroll_to_bar(self, my: int):
        """バーのドラッグ位置からscrollを再計算"""
        vis = self._visible_rows()
        if len(self.items) <= vis:
            return
        # トラック情報
        track_y = self.y + self.title_h + 5
        track_h = self.h - self.title_h - 10
        bar_x, bar_y, bar_w, bar_h = self._bar_rect
        # 掴んだ位置を維持しつつ、新しいbar_yを決定
        new_bar_y = my - self._drag_offset
        # トラック内にクランプ
        new_bar_y = max(track_y, min(track_y + track_h - bar_h, new_bar_y))
        # 0..1 の比率に戻す
        ratio = (new_bar_y - track_y) / max(1, (track_h - bar_h))
        max_scroll = max(1, len(self.items) - vis)
        self.scroll = int(ratio * max_scroll)

    def _page(self, delta_rows: int):
        vis = self._visible_rows()
        self.scroll = max(0, min(max(0, len(self.items) - vis), self.scroll + delta_rows))

    # ====== 入力 ======
    def handle_input(self) -> Optional[str]:
        mx, my = pyxel.mouse_x, pyxel.mouse_y
        left_now = pyxel.btn(pyxel.MOUSE_BUTTON_LEFT)
        left_down = pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT)   # 押した瞬間
        left_up   = (not left_now) and pyxel.btnr(pyxel.MOUSE_BUTTON_LEFT) if hasattr(pyxel, "btnr") else (not left_now)

        vis = self._visible_rows()

        # ホバー行（スクロールバー掴み中は更新しない）
        if not self._dragging_bar:
            self.hover_idx = self._index_at(mx, my)

        # スクロールバー矩形の計算（描画と入力の両方で使う）
        self._bar_rect = self._calc_bar()
        bar_x, bar_y, bar_w, bar_h = self._bar_rect
        bar_hit = (bar_w > 0 and bar_x <= mx < bar_x + bar_w and bar_y <= my < bar_y + bar_h)

        # --- 左クリック開始：バーを掴む or 行を押す ---
        if left_down:
            if bar_hit:
                # バーをドラッグ開始
                self._dragging_bar = True
                self._drag_offset = my - bar_y
            else:
                # リスト側を押した（ページ送り or 行押下）
                idx = self._index_at(mx, my)
                if idx is None:
                    # トラック領域（バー以外の右端）をクリック → ページスクロール
                    if bar_w > 0 and (bar_x - 10) <= mx < (bar_x + bar_w + 10):
                        self._page(vis if my > bar_y else -vis)
                else:
                    self._pressing = True
                    self.hover_idx = idx  # 明示的に更新

        # --- ドラッグ中：バーを移動 ---
        if self._dragging_bar and left_now:
            self._scroll_to_bar(my)

        # --- 左クリック終了：確定処理 or ドラッグ解除 ---
        decided: Optional[str] = None
        if not left_now:
            if self._dragging_bar:
                self._dragging_bar = False
            elif self._pressing:
                # 押していた行で指を離したら決定
                idx = self._index_at(mx, my)
                if idx is not None and idx == self.hover_idx:
                    self.sel = idx
                    decided = self.items[self.sel]
            self._pressing = False

        return decided

    # ====== 描画 ======
    def draw(self, title: str = "PATTERNS"):
        # パネル背景・枠
        pyxel.rect(self.x, self.y, self.w, self.h, 1)
        pyxel.rectb(self.x, self.y, self.w, self.h, 5)
        pyxel.text(self.x + self.margin, self.y + 2, title, 10)

        start_y = self._content_top()
        vis = self._visible_rows()

        # 現在のスクロール位置に基づいて、見える範囲だけ描画（仮想化）
        for i in range(vis):
            idx = self.scroll + i
            if idx >= len(self.items):
                break
            y = start_y + i * self.row_h
            name = self.items[idx]
            hovered  = (idx == self.hover_idx) and not self._dragging_bar
            pressed  = hovered and self._pressing
            selected = (idx == self.sel)

            # ボタン矩形
            btn_x = self.x + 2
            btn_w = self.w - 8   # 右端のスクロールトラック分ちょい余白
            btn_y = y + (1 if pressed else 0)
            btn_h = self.row_h - 1

            # 配色
            if pressed:
                bg = 13
            elif hovered:
                bg = 6
            elif selected:
                bg = 11
            else:
                bg = 1

            border = 5 if not pressed else 0

            pyxel.rect(btn_x, btn_y, btn_w, btn_h, bg)
            pyxel.rectb(btn_x, btn_y, btn_w, btn_h, border)
            pyxel.text(btn_x + 4 + (1 if pressed else 0), y + 1 + (1 if pressed else 0),
                       name, 0 if (hovered or selected) else 7)

        # スクロールトラック＆バー
        # トラック
        track_x = self.x + self.w - 5
        track_y = self.y + self.title_h + 5
        track_h = self.h - self.title_h - 10
        if track_h > 0:
            pyxel.rect(track_x, track_y, 3, track_h, 0)
            # バー
            bar_x, bar_y, bar_w, bar_h = self._bar_rect
            if bar_w > 0:
                pyxel.rect(bar_x, bar_y, bar_w, bar_h, 12 if not self._dragging_bar else 7)
