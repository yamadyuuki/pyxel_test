# tools/data_fetch.py
# coding: utf-8
from __future__ import annotations
import time, random, requests
import yfinance as yf
import pandas as pd
from tools.ticker_list import TICKER_LIST
from pathlib import Path
from typing import Optional, Dict, Any, Iterable

# 相対インポート（パッケージにするため __init__.py を用意しておく）
from core.models import FinancialSnapshot

RATE_LIMIT_SEC = 1.0      # 1銘柄ごとに最低1秒待つ
JITTER_SEC = 0.5          # + 最大0.5秒のランダム待機

# ---------- ラベル候補（yfinanceの行ラベルの揺れを吸収） ----------
ASSETS_CANDIDATES = [
    "Total Assets", "TotalAssets",
]
LIABS_CANDIDATES = [
    "Total Liabilities Net Minority Interest",
    "TotalLiabilitiesNetMinorityInterest",
    "Total Liabilities",
]
# ★ 非支配株主持分を含む資本合計（最優先）
EQUITY_GROSS_CANDIDATES = [
    "Total Equity Gross Minority Interest",
    "TotalEquityGrossMinorityInterest",
    "Total Equity", "TotalEquity",
]
REVENUE_CANDIDATES = [
    "Total Revenue", "Operating Revenue", "Revenue",
    "TotalRevenue", "OperatingRevenue",
]
OPERATING_INCOME_CANDIDATES = [
    "Operating Income", "OperatingIncome", "EBIT", "Ebit",
]

def _polite_sleep():
    time.sleep(RATE_LIMIT_SEC + random.uniform(0, JITTER_SEC))

# 追加: シンプルなリトライ（指数バックオフ）
def _retry(call, attempts: int = 3, base_wait: float = 1.5):
    """
    call: 引数なしの関数（例: lambda: fetch_financial_snapshot(sym, quarterly, session=session)）
    attempts: 再試行回数
    base_wait: 初回待機（次回は倍々に）
    """
    wait = base_wait
    last_err = None
    for i in range(attempts):
        try:
            return call()
        except Exception as e:
            last_err = e
            if i == attempts - 1:
                raise
            time.sleep(wait)
            wait *= 2
    raise last_err

# ---------- ヘルパー ----------
def _pick_first_existing(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    """候補ラベルのうち、最初に df.index に存在するものの名前を返す。見つからなければ None。"""
    for name in candidates:
        if name in df.index:
            return name
    return None

def _safe_get(df: pd.DataFrame, lbl: Optional[str], col) -> Optional[float]:
    """df.loc[lbl, col] を安全に取得して float に変換。lbl=None や NaN のときは None。"""
    if lbl is None:
        return None
    val = df.loc[lbl, col]
    if pd.isna(val):
        return None
    return float(val)

# ---------- 直近期末の財務スナップショット（辞書） ----------
def latest_financials(ticker_symbol: str, quarterly: bool = False):
    """
    指定ティッカーの『直近期末』の財務スナップショットを返す（BS/ISの両方）。
    quarterly=False: 年次 / True: 四半期
    """
    t = yf.Ticker(ticker_symbol)

    # --- Balance Sheet ---
    bs = t.quarterly_balance_sheet if quarterly else t.balance_sheet
    if bs is None or bs.empty:
        raise ValueError("バランスシートが取得できませんでした。銘柄や期間をご確認ください。")
    bs_col = bs.columns[0]  # 直近期末（新しい順）

    a_lbl = _pick_first_existing(bs, ASSETS_CANDIDATES)
    l_lbl = _pick_first_existing(bs, LIABS_CANDIDATES)
    e_lbl = _pick_first_existing(bs, EQUITY_GROSS_CANDIDATES)

    assets = _safe_get(bs, a_lbl, bs_col)
    liabilities = _safe_get(bs, l_lbl, bs_col)
    equity_gross = _safe_get(bs, e_lbl, bs_col)

    # フォールバック：資本合計（非支配株主持分込み）が取れない場合は A - L で計算
    if equity_gross is None and (assets is not None and liabilities is not None):
        equity_gross = assets - liabilities
        e_lbl = "Computed: Assets - Liabilities"

    # --- Income Statement ---
    is_df = t.quarterly_financials if quarterly else t.financials
    if is_df is None or is_df.empty:
        raise ValueError("損益計算書が取得できませんでした。銘柄や期間をご確認ください。")
    is_col = is_df.columns[0]  # 直近期末

    r_lbl = _pick_first_existing(is_df, REVENUE_CANDIDATES)
    oi_lbl = _pick_first_existing(is_df, OPERATING_INCOME_CANDIDATES)

    revenue = _safe_get(is_df, r_lbl, is_col)
    operating_income = _safe_get(is_df, oi_lbl, is_col)

    return {
        "period": {"bs": bs_col, "is": is_col},
        "values": {
            "assets": assets,
            "liabilities": liabilities,
            "equity_gross": equity_gross,
            "revenue": revenue,
            "operating_income": operating_income,
        },
        "labels": {
            "assets": a_lbl,
            "liabilities": l_lbl,
            "equity_gross": e_lbl,
            "revenue": r_lbl,
            "operating_income": oi_lbl,
        },
    }

# ---------- dataclass で欲しい場合の薄いラッパー ----------
def fetch_financial_snapshot(ticker_symbol: str, quarterly: bool = False) -> FinancialSnapshot:
    """
    latest_financials() を呼んで、FinancialSnapshot に詰め替えて返す。
    """
    d = latest_financials(ticker_symbol, quarterly=quarterly)

    #会社名
    t = yf.Ticker(ticker_symbol)
    company_name = t.info.get("longName") or t.info.get("shortName") or ticker_symbol

    # ここでは BS 側の期末日を採用（ISでもOK）
    period = d["period"]["bs"]
    # pandas.Timestamp → 'YYYY-MM-DD' の文字列へ（Timestampでない場合はそのままstr）
    if hasattr(period, "date"):
        date_str = str(period.date())
    else:
        date_str = str(period)

    v = d["values"]
    return FinancialSnapshot(
        company=company_name,
        date=date_str,
        assets=v["assets"],
        liabilities=v["liabilities"],
        equity_gross=v["equity_gross"],
        revenue=v["revenue"],
        operating_income=v["operating_income"],
    )

def fetch_multiple_snapshots(symbols: list[str], quarterly: bool = False) -> list[FinancialSnapshot]:
    snaps: list[FinancialSnapshot] = []

    # 追加: 1つのセッションを共有

    for sym in symbols:
        try:
            # 追加: リトライつきで取得
            snap = _retry(lambda: fetch_financial_snapshot(sym, quarterly=quarterly),
                          attempts=3, base_wait=1.5)
            snaps.append(snap)
        except Exception as e:
            print(f"[WARN] {sym} の取得に失敗: {e}")
        finally:
            # 追加: 各銘柄の間で“礼儀正しく”ウェイト
            _polite_sleep()

    return snaps


# ---------- dataclass を .py に保存（import 可能にする） ----------
def save_snapshot_as_py(snapshot: FinancialSnapshot, out_file: str | Path, var_name: str = "DATA") -> Path:
    """
    1件の FinancialSnapshot を import 可能な .py として保存。
    例: from balance_sheet_test.data.snap_7203 import DATA
    """
    out_path = Path(out_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    source = f'''# auto-generated
from core.models import FinancialSnapshot

{var_name} = FinancialSnapshot(
    company={snapshot.company!r},
    date={snapshot.date!r},
    assets={snapshot.assets!r},
    liabilities={snapshot.liabilities!r},
    equity_gross={snapshot.equity_gross!r},
    revenue={snapshot.revenue!r},
    operating_income={snapshot.operating_income!r},
)
'''
    out_path.write_text(source, encoding="utf-8")
    return out_path

def save_snapshots_as_py(snapshots: Iterable[FinancialSnapshot], out_file: str | Path, var_name: str = "DATA") -> Path:
    """
    複数件を List[FinancialSnapshot] として .py 保存。
    """
    out_path = Path(out_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    items = []
    for s in snapshots:
        items.append(
            f"FinancialSnapshot(company={s.company!r}, date={s.date!r}, assets={s.assets!r}, "
            f"liabilities={s.liabilities!r}, equity_gross={s.equity_gross!r}, "
            f"revenue={s.revenue!r}, operating_income={s.operating_income!r})"
        )
    body = ",\n    ".join(items)

    source = f'''# auto-generated
from core.models import FinancialSnapshot

{var_name} = [
    {body}
]
'''
    out_path.write_text(source, encoding="utf-8")
    return out_path

# --- 動作確認 ---
if __name__ == "__main__":
    syms = TICKER_LIST  # トヨタ、ソニー、ソフトバンク
    snaps = fetch_multiple_snapshots(syms, quarterly=False)

    for s in snaps:
        print(s)

    # まとめて保存したい場合
    save_to = Path(__file__).resolve().parents[1] / "data" / "snap_multi.py"
    save_snapshots_as_py(snaps, save_to)
    print(f"saved: {save_to}")