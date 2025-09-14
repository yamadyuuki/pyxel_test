# -*- coding: utf-8 -*-
"""
EDINET 有価証券報告書 XBRL 収集（複数企業・複数年対応 / 期末ハードコード無し）
- 期間内の日付を走査し、指定した複数の EDINET コードの「有価証券報告書/訂正有報」を抽出
- ZIPは保存せず、XBRL/PublicDoc/ 内の *asr*（本文）.xbrl を抽出
- 期末日は XBRLファイル名の "_YYYY-MM-DD_" から動的取得（企業ごとの期末差に自然対応）
- 保存先: OUT_ROOT/<EDINET>/<yyyy_mm_dd>/<filename>.xbrl
- 処理インデックス index.csv を OUT_ROOT に追記出力
"""

from __future__ import annotations

import os
import re
import csv
import json
import time
import zipfile
from io import BytesIO
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Iterable

import requests
from dotenv import load_dotenv

# =========================
# 設定
# =========================

load_dotenv()
EDINET_API_KEY = os.getenv("EDINET_API_KEY", "").strip()

# 収集対象の企業（EDINETコードを複数指定OK）
EDINET_CODES: List[str] = [
    "E02144",  # トヨタ
    # "E00000",  # ほかの企業コードを追加
]

# 対象フォーム：有価証券報告書(030000) と 訂正有報(030001)
TARGET_FORMS = {
    ("010", "030000"),  # 有報
    ("010", "030001"),  # 訂正有報
}

# 期間（例：過去10年などに調整可）
DATE_FROM = datetime(2020, 6, 1)
DATE_TO   = datetime(2025, 6, 30)

# 保存ルート（<EDINET>/<yyyy_mm_dd>/ に落とす）
OUT_ROOT = os.path.join("downloads_edinet")

# レート制御
REQUEST_INTERVAL_SEC = 0.4

# 抽出方針：PublicDoc配下の asr（本文）.xbrl のみ保存
ONLY_ASR = True

# インデックスCSV
INDEX_CSV = os.path.join(OUT_ROOT, "index.csv")


# =========================
# EDINET API
# =========================
LIST_URL = "https://api.edinet-fsa.go.jp/api/v2/documents.json"
DOC_URL  = "https://api.edinet-fsa.go.jp/api/v2/documents/{docID}"  # ?type=1 でZIP

def _require_api_key() -> None:
    if not EDINET_API_KEY:
        raise RuntimeError("EDINET_API_KEY が未設定です。環境変数または .env に設定してください。")

def list_docs_one_day(d: datetime) -> Dict[str, Any]:
    params = {"date": d.strftime("%Y-%m-%d"), "type": 2, "Subscription-Key": EDINET_API_KEY}
    r = requests.get(LIST_URL, params=params, timeout=60)
    r.raise_for_status()
    return r.json()

def _code_in_targets(row: Dict[str, Any], codes: Iterable[str]) -> Optional[str]:
    """該当企業ならその EDINETコードを返す（edinetCode or issuerEdinetCode を採用）"""
    ec = row.get("edinetCode")
    iec = row.get("issuerEdinetCode")
    if ec in codes:
        return ec
    if iec in codes:
        return iec
    return None

def pick_target_docs(json_obj: Any, codes: Iterable[str]) -> List[Tuple[str, Dict[str, Any], str]]:
    """その日の一覧から、対象企業かつ TARGET_FORMS に一致する全件を返す
    Returns: [(doc_id, meta_row, matched_edinet_code), ...]
    """
    res: List[Tuple[str, Dict[str, Any], str]] = []
    docs = json_obj.get("results", []) if isinstance(json_obj, dict) else []
    for row in docs:
        matched_code = _code_in_targets(row, codes)
        if not matched_code:
            continue
        if (row.get("ordinanceCode"), row.get("formCode")) in TARGET_FORMS:
            doc_id = row.get("docID")
            if doc_id:
                res.append((doc_id, row, matched_code))
    return res

def download_zip(doc_id: str) -> bytes:
    url = DOC_URL.format(docID=doc_id)
    params = {"type": 1, "Subscription-Key": EDINET_API_KEY}
    r = requests.get(url, params=params, timeout=120)
    r.raise_for_status()
    return r.content


# =========================
# XBRL 抽出
# =========================

# 例: jpcrp030000-asr-001_E02144-000_2025-03-31_01_2025-06-18.xbrl
_PERIOD_IN_NAME = re.compile(r"_(\d{4}-\d{2}-\d{2})_")

def extract_period_end_from_name(xbrl_name: str) -> Optional[str]:
    m = _PERIOD_IN_NAME.search(xbrl_name)
    return m.group(1) if m else None

def extract_publicdoc_xbrl(content_zip: bytes) -> List[Tuple[str, bytes]]:
    """
    ZIP から PublicDoc/*.xbrl をすべて取り出す（メモリ）
    Returns: [(basename, file_bytes), ...]
    """
    out: List[Tuple[str, bytes]] = []
    with zipfile.ZipFile(BytesIO(content_zip)) as z:
        candidates = [n for n in z.namelist() if "XBRL/PublicDoc/" in n and n.lower().endswith(".xbrl")]
        if ONLY_ASR:
            # asr 本文を優先的に採用
            candidates = [n for n in candidates if "asr" in os.path.basename(n).lower()]
        # 名前順で安定化
        candidates.sort()
        for name in candidates:
            data = z.read(name)
            out.append((os.path.basename(name), data))
    return out


# =========================
# インデックス管理
# =========================

def ensure_index_csv(path: str) -> None:
    if os.path.exists(path):
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["edinet_code", "doc_id", "submit_date", "form_code", "doc_description", "period_end", "saved_path"])

def append_index_row(path: str, row: List[str]) -> None:
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(row)


# =========================
# メイン
# =========================

def main() -> None:
    _require_api_key()
    if not EDINET_CODES:
        raise RuntimeError("EDINET_CODES が空です。対象企業の EDINET コードを設定してください。")

    ensure_index_csv(INDEX_CSV)

    days = (DATE_TO - DATE_FROM).days + 1
    seen_doc_ids: set[str] = set()

    print(f"[SCAN] {DATE_FROM:%Y-%m-%d} 〜 {DATE_TO:%Y-%m-%d} / 企業数={len(EDINET_CODES)}")

    for i in range(days):
        d = DATE_FROM + timedelta(days=i)

        # 1) 一覧取得
        try:
            js = list_docs_one_day(d)
        except Exception as e:
            print(f"[ERR] 一覧取得失敗 {d:%Y-%m-%d}: {e}")
            time.sleep(REQUEST_INTERVAL_SEC)
            continue

        # 2) 対象 doc をすべて拾う
        targets = pick_target_docs(js, EDINET_CODES)
        if not targets:
            # print(f"[..] {d:%Y-%m-%d} 該当なし")
            time.sleep(REQUEST_INTERVAL_SEC)
            continue

        for doc_id, meta, edinet in targets:
            if doc_id in seen_doc_ids:
                continue
            seen_doc_ids.add(doc_id)

            desc = (meta or {}).get("docDescription", "")
            form_code = (meta or {}).get("formCode", "")
            submit_dt = (meta or {}).get("submitDateTime")  # 'YYYY-MM-DD HH:MM'
            try:
                submit_date = datetime.strptime((submit_dt or "").split()[0], "%Y-%m-%d")
            except Exception:
                submit_date = d  # 保険

            print(f"[HIT] {submit_date:%Y-%m-%d} {edinet} docID={doc_id} {desc} form={form_code}")

            # 3) ZIP 取得
            try:
                zbytes = download_zip(doc_id)
            except Exception as e:
                print(f"[ERR] ZIP取得失敗 docID={doc_id}: {e}")
                time.sleep(REQUEST_INTERVAL_SEC)
                continue

            # 4) PublicDoc/*.xbrl を抽出（メモリ）
            pairs = extract_publicdoc_xbrl(zbytes)
            if not pairs:
                print(f"[WARN] PublicDoc の .xbrl が見つからない docID={doc_id}")
                time.sleep(REQUEST_INTERVAL_SEC)
                continue

            # 5) 保存（企業/提出日ディレクトリ）
            day_dir = os.path.join(OUT_ROOT, edinet, submit_date.strftime("%Y_%m_%d"))
            os.makedirs(day_dir, exist_ok=True)

            # meta（docID単位で保存）
            meta_path = os.path.join(day_dir, f"meta_{doc_id}.json")
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)

            saved_files = []
            for fname, data in pairs:
                out_path = os.path.join(day_dir, fname)
                with open(out_path, "wb") as wf:
                    wf.write(data)
                saved_files.append(out_path)

                # インデックスCSV追記（period_end はファイル名から動的抽出）
                period_end = extract_period_end_from_name(fname) or ""
                append_index_row(
                    INDEX_CSV,
                    [
                        edinet,
                        doc_id,
                        submit_date.strftime("%Y-%m-%d"),
                        str(form_code),
                        str(desc),
                        period_end,
                        os.path.abspath(out_path),
                    ],
                )

            print(f"[SAVE] {edinet} {submit_date:%Y-%m-%d} -> {len(saved_files)} file(s)")
            time.sleep(REQUEST_INTERVAL_SEC)

        time.sleep(REQUEST_INTERVAL_SEC)

    print(f"[DONE] 期間={DATE_FROM:%Y-%m-%d}〜{DATE_TO:%Y-%m-%d} の収集完了。")
    print(f"保存先: {os.path.abspath(OUT_ROOT)}")
    print(f"インデックス: {os.path.abspath(INDEX_CSV)}")


if __name__ == "__main__":
    main()
