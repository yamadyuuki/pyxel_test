# -*- coding: utf-8 -*-
# 目的: yfinance でトヨタ(7203.T)の通年・四半期の売上高/営業利益を取得してprint表示
# 使い方: uv run python toyota_financials_demo.py

import yfinance as yf
import pandas as pd
import os
from dotenv import load_dotenv

# .env を読み込む
load_dotenv()

# 環境変数から APIキーを取得
EDINET_API_KEY = os.environ.get("EDINET_API_KEY")

if not EDINET_API_KEY:
    raise RuntimeError("EDINET_API_KEY が設定されていません (.env または環境変数を確認してください)")

TICKER = "7203.T"

# yfinanceの行ラベルは銘柄や年度で微妙に表記ゆれがあるため候補を広めに
REV_CANDIDATES = {
    "total revenue", "revenue", "operating revenue", "sales", "net sales"
}
OP_CANDIDATES = {
    "operating income", "operating profit", "operating income or loss"
}

def _pick_row(df: pd.DataFrame, candidates: set[str]) -> pd.Series | None:
    """
    DataFrame(行=科目, 列=期)から、候補に合う行を大文字小文字無視で1つ見つけて返す。
    見つからなければ None。
    """
    # 行名(科目名)を小文字化して探索
    idx_lower = {str(i).lower(): i for i in df.index}
    for want in candidates:
        if want in idx_lower:
            return df.loc[idx_lower[want]]
    # 近そうなラベルを緩く探索（部分一致）
    for i in df.index:
        low = str(i).lower()
        if any(w in low for w in candidates):
            return df.loc[i]
    return None

def _tidy_financials(fin_df: pd.DataFrame) -> pd.DataFrame:
    """
    yfinanceの financials / quarterly_financials (行=科目, 列=期) を
    列: period, revenue, operating_income の縦持ちに整形。
    """
    if fin_df is None or fin_df.empty:
        return pd.DataFrame(columns=["period", "revenue", "operating_income"])

    rev = _pick_row(fin_df, REV_CANDIDATES)
    op  = _pick_row(fin_df, OP_CANDIDATES)

    # 期(列)が DatetimeIndex のことが多いが、文字列のこともあるので一旦そのまま扱う
    periods = list(fin_df.columns)

    data = []
    for p in periods:
        rv = float(rev.get(p, float("nan"))) if rev is not None else float("nan")
        oi = float(op.get(p,  float("nan"))) if op  is not None else float("nan")
        data.append({"period": p, "revenue": rv, "operating_income": oi})

    # 期で昇順に並べ替え（Timestampならそのまま、strなら文字列ソート）
    df = pd.DataFrame(data)
    try:
        df["period_dt"] = pd.to_datetime(df["period"])
        df = df.sort_values("period_dt").drop(columns=["period_dt"])
    except Exception:
        df = df.sort_values("period")

    return df

def main():
    t = yf.Ticker(TICKER)

    # --- 通年（annual） ---
    fin_annual = t.financials              # 損益計算書（年次）
    df_annual = _tidy_financials(fin_annual)

    print("\n==== Annual (通年) 損益計算書 ====")
    if df_annual.empty:
        print("年次データが見つかりませんでした。")
    else:
        print(df_annual.to_string(index=False))

    # --- 四半期（quarterly） ---
    fin_q = t.quarterly_financials         # 損益計算書（四半期）
    df_q = _tidy_financials(fin_q)

    print("\n==== Quarterly (四半期) 損益計算書 ====")
    if df_q.empty:
        print("四半期データが見つかりませんでした。")
    else:
        print(df_q.to_string(index=False))

    # デバッグ用：実際にどんな行ラベルが来ているか確認したいとき
    print("\n[DEBUG] Annual 行ラベル一覧:", list(fin_annual.index) if fin_annual is not None else "N/A")
    print("[DEBUG] Quarterly 行ラベル一覧:", list(fin_q.index) if fin_q is not None else "N/A")

if __name__ == "__main__":
    main()
