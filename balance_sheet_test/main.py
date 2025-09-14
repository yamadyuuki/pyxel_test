# -*- coding: utf-8 -*-
# main.py

import random
from typing import List, Optional

import pyxel
from data.snap_multi import DATA

W, H = 256, 240

STATE_TITLE = 0
STATE_PLAYING = 1
STATE_RESULT = 2

CHOICE_KEYS = ["A", "B", "C", "D"]


def _fmt_money(v: Optional[float]) -> str:
    if v is None:
        return "-"
    n = float(v)
    if abs(n) >= 1e12:
        return f"{n/1e12:.2f}T"
    if abs(n) >= 1e8:
        return f"{n/1e8:.1f}B"
    return f"{n:.0f}"


def _scale(value: float, max_value: float, max_len: int) -> int:
    if max_value <= 0:
        return 0
    ratio = max(0.0, min(1.0, value / max_value))
    return int(ratio * max_len)


class Question:
    def __init__(self, idx: int, snap, pool: List):
        self.idx = idx
        self.snap = snap
        others = random.sample([x for x in pool if x is not snap], k=3)
        self.choices = [snap.company] + [o.company for o in others]
        random.shuffle(self.choices)
        self.correct_idx = self.choices.index(snap.company)

    @property
    def title(self) -> str:
        return f"Q{self.idx+1:02d}  Date: {self.snap.date}"


class App:
    def __init__(self):
        pyxel.init(W, H, title="BS/PL Quiz")
        pyxel.mouse(True)

        self.questions: List[Question] = [Question(i, d, DATA) for i, d in enumerate(DATA)]

        self.state = STATE_TITLE
        self.title_sel = 0
        self.title_scroll = 0
        self.title_rows = 10

        self.cur_q: Optional[Question] = None
        self.sel = 0
        self.is_correct = False

        pyxel.run(self.update, self.draw)

    # ---------------- Common ----------------
    def update(self):
        if self.state == STATE_TITLE:
            self.update_title()
        elif self.state == STATE_PLAYING:
            self.update_playing()
        elif self.state == STATE_RESULT:
            self.update_result()

    def draw(self):
        pyxel.cls(0)
        if self.state == STATE_TITLE:
            self.draw_title()
        elif self.state == STATE_PLAYING:
            self.draw_playing()
        elif self.state == STATE_RESULT:
            self.draw_result()

    # ---------------- Title ----------------
    def update_title(self):
        n = len(self.questions)
        if pyxel.btnp(pyxel.KEY_UP):
            self.title_sel = (self.title_sel - 1) % n
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.title_sel = (self.title_sel + 1) % n

        if self.title_sel < self.title_scroll:
            self.title_scroll = self.title_sel
        elif self.title_sel >= self.title_scroll + self.title_rows:
            self.title_scroll = self.title_sel - self.title_rows + 1

        if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_RETURN):
            self.cur_q = self.questions[self.title_sel]
            self.sel = 0
            self.state = STATE_PLAYING

    def draw_title(self):
        pyxel.text(8, 6, "BS/PL Quiz  -  Select a question and press [SPACE]/[ENTER]", 7)
        pyxel.line(8, 14, W - 8, 14, 5)

        y0 = 22
        for i in range(self.title_rows):
            idx = self.title_scroll + i
            if idx >= len(self.questions):
                break
            y = y0 + i * 16
            q = self.questions[idx]
            if idx == self.title_sel:
                pyxel.rect(6, y - 3, W - 12, 14, 1)
            pyxel.text(10, y, f"Question {q.idx+1}", 10 if idx == self.title_sel else 7)

        pyxel.text(8, H - 10, f"Total {len(self.questions)} questions / Use ↑↓ to navigate", 6)

    # ---------------- Playing ----------------
    def update_playing(self):
        if not self.cur_q:
            self.state = STATE_TITLE
            return

        if pyxel.btnp(pyxel.KEY_UP):
            self.sel = (self.sel - 1) % 4
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.sel = (self.sel + 1) % 4

        if pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.KEY_SPACE):
            self.is_correct = (self.sel == self.cur_q.correct_idx)
            self.state = STATE_RESULT

        if pyxel.btnp(pyxel.KEY_BACKSPACE) or pyxel.btnp(pyxel.KEY_ESCAPE):
            self.state = STATE_TITLE

    def draw_playing(self):
        q = self.cur_q
        assert q is not None
        s = q.snap

        # ---- Get values ----
        assets = max(0.0, float(s.assets or 0.0))
        liab = max(0.0, float(s.liabilities or 0.0))
        equity = max(0.0, float(s.equity_gross or 0.0))
        rev = float(s.revenue or 0.0)
        op = float(s.operating_income or 0.0)

        # ---- Unify scale (same pixels/amount for BS and PL) ----
        # Support negative OP with absolute value comparison (common 0 axis)
        unified_max = max(assets, liab + equity, abs(rev), abs(op), 1.0)

        # ---- Coordinate system: Align x-axis (base) ----
        margin_left = 8
        margin_right = 8
        top = 24
        base_y = H - 60  # Common base for all figures
        area_h = base_y - top  # Usable height

        # Left: Diagram layout
        #   [Assets] | [Liabilities/Equity]
        #   Assets are filled on the left, Liabilities/Equity are stacked on the right
        col_w = 54
        gap = 0

        # --- Left column: Assets ---
        a_h = _scale(assets, unified_max, area_h)
        ax = margin_left
        aw = col_w
        ay = base_y - a_h
        # Frame (red) + Fill (light red)
        pyxel.rectb(ax, top, aw, area_h, 8)      # Frame=Red
        pyxel.rect(ax + 1, ay, aw - 2, a_h, 9)   # Content=Light red (9)

        # --- Right column: Liabilities/Equity ---
        bx = ax + aw - 1
        bw = col_w
        # Frame (blue)
        pyxel.rectb(bx, top, bw, area_h, 12)
        # Total height of the right column is conceptually the same as Assets, stacked to match assets visually
        # However, since unified_max is used for scaling, the pitch will be the same as the bar graph
        l_h = _scale(liab, unified_max, area_h)
        e_h = _scale(equity, unified_max, area_h)
        # Top = Liabilities (green), Bottom = Equity (light blue)
        pyxel.rect(bx + 1, top + 1, bw - 2, l_h, 11)                 # Liabilities (top)
        pyxel.rect(bx + 1, top + 1 + l_h, bw - 2, e_h, 6)            # Equity (bottom) = Light blue (6)
        # If there is a margin, leave it as is (proof of unified scale)

        # Labels
        pyxel.text(ax, top - 10, "Assets", 8)
        pyxel.text(bx, top - 10, "L/SE", 8)
        pyxel.text(
            margin_left,
            base_y + 2,
            f"A:{_fmt_money(assets)}  L:{_fmt_money(liab)}  E:{_fmt_money(equity)}",
            6,
        )

        # Right: PL (Revenue / Operating Income)
        chart_x = bx + bw + 22
        bar_w = 26
        bar_gap = 18

        # Share x-axis (white line at the bottom) for all figures
        pyxel.line(margin_left, base_y, W - margin_right, base_y, 7)

        # Revenue (light blue=12)
        r_h = _scale(abs(rev), unified_max, area_h)
        pyxel.rect(chart_x, base_y - r_h, bar_w, r_h, 12)
        pyxel.text(chart_x - 2, base_y + 2, "Revenue", 6)
        pyxel.text(chart_x - 2, top - 10, _fmt_money(rev), 7)

        # Operating Income (black=10(yellow), red=2)
        o_h = _scale(abs(op), unified_max, area_h)
        o_color = 10 if op >= 0 else 2
        ox = chart_x + bar_w + bar_gap
        pyxel.rect(ox, base_y - o_h, bar_w, o_h, o_color)
        pyxel.text(ox + 2, base_y + 2, "OP", 6)
        pyxel.text(ox - 2, top - 10, _fmt_money(op), 7)

        # Choices
        self._draw_choices(q, chart_x)

        # Header
        pyxel.text(8, 6, f"Q{q.idx+1:02d}  Date: {s.date}", 7)
        pyxel.text(W - 120, 6, "[↑/↓]Select  [ENTER/SPACE]Confirm  [ESC]Back", 5)

    def _draw_choices(self, q: Question, chart_x: int):
        pyxel.line(8, H - 52, W - 8, H - 52, 5)
        x = 12
        y = H -48
        for i, name in enumerate(q.choices):
            yy = y + i * 12
            if i == self.sel:
                pyxel.rect(x - 2, yy - 2, W - 24 - 8, 12, 1)
            label = f"{CHOICE_KEYS[i]}. {name}"
            pyxel.text(x, yy, label, 10 if i == self.sel else 7)

    # ---------------- Result ----------------
    def update_result(self):
        if pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.KEY_SPACE):
            self.state = STATE_TITLE

    def draw_result(self):
        assert self.cur_q is not None
        q = self.cur_q
        s = q.snap
        pyxel.cls(0)
        msg = "Correct!" if self.is_correct else "Incorrect..."
        pyxel.text(W // 2 - 16, 60, msg, 10 if self.is_correct else 8)
        pyxel.text(12, 86, f"Answer: {s.company}", 7)
        pyxel.text(12, 100, f"Date: {s.date}", 6)
        pyxel.text(12, 114, f"A:{_fmt_money(s.assets)}  L:{_fmt_money(s.liabilities)}  E:{_fmt_money(s.equity_gross)}", 6)
        pyxel.text(12, 128, f"Rev:{_fmt_money(s.revenue)}  OP:{_fmt_money(s.operating_income)}", 6)
        pyxel.text(W // 2 - 64, 170, "[ENTER/SPACE] to Title", 5)


if __name__ == "__main__":
    App()
