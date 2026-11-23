"""從證交所抓最新收盤點數，補進兩個 CSV：

- taiex_total_return_daily.csv：發行量加權股價報酬指數（還原除權息）
  https://www.twse.com.tw/zh/indices/taiex/mfi94u.html
- taiex_price_daily.csv：發行量加權股價指數（一般大盤，不含息）
  https://www.twse.com.tw/zh/indices/taiex/mi-5min-hist.html

API 一次回傳一整個月，所以從 CSV 最後一天所在的月份抓到這個月。
CSV 不存在時從 2003-01 開始回補（和報酬指數同一個起點）。
只用標準函式庫，GitHub Actions 和本機都能直接跑：python update.py
"""
import csv
import datetime as dt
import json
import os
import ssl
import time
import urllib.request

# (CSV 檔, 欄位名稱, API, 收盤價在 data 每列的第幾欄)
SOURCES = [
    ("taiex_total_return_daily.csv", "發行量加權股價報酬指數",
     "https://www.twse.com.tw/rwd/zh/TAIEX/MFI94U?date={:%Y%m%d}&response=json", 1),
    ("taiex_price_daily.csv", "發行量加權股價指數",
     "https://www.twse.com.tw/rwd/zh/TAIEX/MI_5MINS_HIST?date={:%Y%m%d}&response=json", 4),
]
FIRST_MONTH = dt.date(2003, 1, 1)
TAIPEI = dt.timezone(dt.timedelta(hours=8))
# 證交所憑證缺 Subject Key Identifier，Python 3.13+ 的嚴格模式會拒絕；仍驗證憑證，只關掉嚴格檢查
SSL_CTX = ssl.create_default_context()
SSL_CTX.verify_flags &= ~ssl.VERIFY_X509_STRICT


def fetch_month(api, col, first_day):
    time.sleep(3)  # 證交所連續請求太快會暫時封鎖 IP
    req = urllib.request.Request(api.format(first_day), headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30, context=SSL_CTX) as r:
        js = json.load(r)
    if js.get("stat") != "OK":  # 該月還沒有資料時 stat 不是 OK
        return {}
    out = {}
    for row in js["data"]:
        y, m, d = (int(x) for x in row[0].strip().split("/"))
        out[dt.date(y + 1911, m, d).isoformat()] = row[col].replace(",", "")
    return out


def update(csv_path, header, api, col):
    rows = {}
    if os.path.exists(csv_path):
        with open(csv_path, encoding="utf-8-sig", newline="") as f:
            rows = {r[0]: r[1] for r in list(csv.reader(f))[1:] if r}

    month = dt.date.fromisoformat(max(rows)).replace(day=1) if rows else FIRST_MONTH
    today = dt.datetime.now(TAIPEI).date()

    added = []
    while month <= today:
        for day, value in fetch_month(api, col, month).items():
            if day not in rows:
                added.append(day)
            rows[day] = value
        month = (month + dt.timedelta(days=32)).replace(day=1)

    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["日期", header])
        w.writerows(sorted(rows.items()))

    shown = ", ".join(sorted(added)) if len(added) <= 10 else f"{min(added)} ~ {max(added)}"
    print(f"{csv_path}：新增 {len(added)} 天：{shown or '無'}（最後一天 {max(rows)}）")


def main():
    for source in SOURCES:
        update(*source)


if __name__ == "__main__":
    main()
