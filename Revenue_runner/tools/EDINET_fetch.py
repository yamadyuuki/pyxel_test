# edinet_fetch_toyota_asr.py
import os, io, zipfile, datetime as dt
import requests
from tqdm import tqdm
from dotenv import load_dotenv   # ←追加

# .env を読み込む
load_dotenv()
# 1件だけ試す
MAX_DOCS = 1
API_KEY = os.environ.get("EDINET_API_KEY")  # .env またはユーザー環境変数から取得
BASE = "https://api.edinet-fsa.go.jp/api/v2"


EDINET_CODE_TOYOTA = "E02144"  # トヨタ自動車
SAVE_DIR = "downloads_edinet_toyota_asr"
os.makedirs(SAVE_DIR, exist_ok=True)

def list_documents(date_str: str, api_key: str):
    url = f"{BASE}/documents.json"
    params = {"date": date_str, "type": "2", "Subscription-Key": api_key}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def download_document(doc_id: str, kind: int, api_key: str) -> bytes:
    # kind: 1=本文/XBRL ZIP, 2=PDF, 5=CSV（仕様書のtype定義）
    url = f"{BASE}/documents/{doc_id}"
    params = {"type": str(kind), "Subscription-Key": api_key}
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    return r.content

def main():
    assert API_KEY, "環境変数 EDINET_API_KEY を設定してください。"

    # EDINETの閲覧可能期間は有報で最大10年なので、今日から過去10年分だけ走査
    today = dt.date.today()
    start = today - dt.timedelta(days=365*10 + 30)  # 余裕を持って10年＋α
    # EDINETは「日付ごと」に一覧を取得する設計
    dates = [start + dt.timedelta(days=i) for i in range((today - start).days + 1)]

    found = []
    for d in tqdm(dates, desc="Listing"):
        try:
            js = list_documents(d.strftime("%Y-%m-%d"), API_KEY)
            results = js.get("results", [])
            for item in results:
                # filerEdinetCode / docID / docDescription などが入っている
                if item.get("issuerEdinetCode") != EDINET_CODE_TOYOTA:
                    continue
                #desc = (item.get("docDescription") or "")
                if item.get("docTypeCode") in ("120", "130"):
                    found.append(item)
        except Exception:
            # ネットワーク断などはスキップ
            continue

    # 重複排除＆新しい順に
    unique = {it["docID"]: it for it in found}
    docs = sorted(unique.values(), key=lambda x: x.get("submitDateTime",""), reverse=True)

    print(f"ヒット数: {len(docs)} 件")
    for it in docs:
        print(it.get("docID"), it.get("submitDateTime"), it.get("docDescription"))

    # ダウンロード（XBRL一式ZIP＝type=1）を全部保存
    for it in tqdm(docs, desc="Downloading ZIP"):
        doc_id = it["docID"]
        try:
            content = download_document(doc_id, kind=1, api_key=API_KEY)
            # ZIPの中身をそのまま保存（後で解析しやすい構成に解凍してもOK）
            out = os.path.join(SAVE_DIR, f"{doc_id}.zip")
            with open(out, "wb") as f:
                f.write(content)
        except Exception as e:
            print("DL失敗:", doc_id, e)

if __name__ == "__main__":
    main()
