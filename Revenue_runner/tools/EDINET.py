# edinet_min_loop_toyota.py
import os
import sys
import time
import json
import zipfile
from io import BytesIO
from datetime import date, timedelta
from dotenv import load_dotenv   # ←追加

# .env を読み込む
load_dotenv()

import requests

# --- 設定（必要に応じて編集） ---
EDINET_CODE = "E02144"  # トヨタ
DATE_FROM   = date(2025, 6, 15)  # 例：有報提出（2025-06-18）前後をカバー
DATE_TO     = date(2025, 6, 30)

# .envを使う場合（任意）
try:
    from dotenv import load_dotenv  # pip install python-dotenv
    load_dotenv()
except Exception:
    pass

API_KEY = os.environ.get("EDINET_API_KEY")  # 環境変数で設定
if not API_KEY:
    sys.exit("環境変数 EDINET_API_KEY が未設定です。")

# ヘッダ方式が推奨（Ocp-Apim-Subscription-Key）
HEADERS = {"Ocp-Apim-Subscription-Key": API_KEY, "User-Agent": "edinet-min/0.1"}

# 有報/半期（訂正含む）だけに絞るフィルタ
# ordinanceCode=010（企業内容等の開示に関する内閣府令）
# formCode: 030000=有価証券報告書, 030001=訂正有報, 050000=半期報告書, 050001=訂正半期
TARGET_FORMS = {
    ("010", "030000"),
    ("010", "030001"),
    ("010", "050000"),
    ("010", "050001"),
}

LIST_URL = "https://api.edinet-fsa.go.jp/api/v2/documents.json"
GET_URL  = "https://api.edinet-fsa.go.jp/api/v2/documents/{docID}"

def list_docs_one_day(d: date):
    r = requests.get(
        LIST_URL,
        params={"date": d.strftime("%Y-%m-%d"), "type": 2, "Subscription-Key": API_KEY},
        headers=HEADERS,
        timeout=20,
    )
    r.raise_for_status()
    js = r.json()
    meta = js.get("metadata", {})
    rs   = meta.get("resultset", {}) if isinstance(meta, dict) else {}
    print(f"[META] {d} count={rs.get('count')} status={meta.get('status')} msg={meta.get('message')}")
    return js

def debug_dump_for_day(js, d):
    # その日の一覧から E02144 を素通し（formCodeはまだ絞らない）
    hits = []
    for row in js.get("results", []):
        if row.get("edinetCode") == EDINET_CODE or row.get("issuerEdinetCode") == EDINET_CODE:
            hits.append({
                "docID": row.get("docID"),
                "ordinanceCode": row.get("ordinanceCode"),
                "formCode": row.get("formCode"),
                "docTypeCode": row.get("docTypeCode"),
                "submitDateTime": row.get("submitDateTime"),
                "docDescription": row.get("docDescription"),
            })
    print(f"[SCAN] {d} E02144 hits={len(hits)}")
    for h in hits[:5]:
        print(" ", h)
    return hits

def pick_first_doc(json_obj):
    docs = json_obj.get("results", []) if isinstance(json_obj, dict) else []
    for row in docs:
        edc  = row.get("edinetCode")
        iss  = row.get("issuerEdinetCode")
        if not (edc == EDINET_CODE or iss == EDINET_CODE):
            continue
        key = (row.get("ordinanceCode"), row.get("formCode"))
        if key in {
            ("010","030000"),  # 有報
            ("010","030001"),  # 訂正有報
            ("010","050000"),  # 半期
            ("010","050001"),  # 訂正半期
        }:
            return row.get("docID"), row
    return None, None

def download_zip(doc_id: str) -> bytes:
    """書類取得API: type=1(ZIP) を取得"""
    url = GET_URL.format(docID=doc_id)
    for attempt in range(5):
        try:
            r = requests.get(url, params={"type": 1, "Subscription-Key": API_KEY}, headers=HEADERS, timeout=60)
            if r.status_code == 429:
                time.sleep(1.5 * (attempt + 1))
                continue
            r.raise_for_status()
            return r.content
        except requests.RequestException:
            if attempt == 4:
                raise
            time.sleep(1.5 * (attempt + 1))
    return b""

def main():
    days = (DATE_TO - DATE_FROM).days + 1
    found = None
    found_meta = None

    for i in range(days):
        d = DATE_FROM + timedelta(days=i)
        js = list_docs_one_day(d)             # ここで [META] ログが出ます
        # （デバッグ用）必要なら素通しダンプ:
        # debug_dump_for_day(js, d)
        doc_id, meta = pick_first_doc(js)
        if doc_id:
            found = doc_id
            found_meta = meta
            print(f"[HIT] {d} {meta.get('docDescription')} docID={doc_id}")
            break
        else:
            print(f"[..]  {d} 該当なし")

    if not found:
        print("期間内に該当書類が見つかりませんでした。")
        return

    content = download_zip(found)
    out_dir = os.path.join("downloads_edinet", EDINET_CODE, found)
    os.makedirs(out_dir, exist_ok=True)
    # meta.json も残すと再現性◎
    with open(os.path.join(out_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(found_meta, f, ensure_ascii=False, indent=2)
    with open(os.path.join(out_dir, f"{found}.zip"), "wb") as f:
        f.write(content)
    print("保存先：", out_dir)

if __name__ == "__main__":
    main()
