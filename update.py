"""從證交所抓「發行量加權股價報酬指數」最新收盤點數，補進 taiex_total_return_daily.csv。

資料來源：https://www.twse.com.tw/zh/indices/taiex/mfi94u.html
API 一次回傳一整個月，所以從 CSV 最後一天所在的月份抓到這個月。
只用標準函式庫，GitHub Actions 和本機都能直接跑：python update.py
"""
import csv
import datetime as dt
import json
import ssl
import urllib.request

CSV_PATH = "taiex_total_return_daily.csv"
HEADER = ["日期", "發行量加權股價報酬指數"]
API = "https://www.twse.com.tw/rwd/zh/TAIEX/MFI94U?date={:%Y%m%d}&response=json"
TAIPEI = dt.timezone(dt.timedelta(hours=8))
# 證交所憑證缺 Subject Key Identifier，Python 3.13+ 的嚴格模式會拒絕；仍驗證憑證，只關掉嚴格檢查
SSL_CTX = ssl.create_default_context()
SSL_CTX.verify_flags &= ~ssl.VERIFY_X509_STRICT


def fetch_month(first_day):
    req = urllib.request.Request(API.format(first_day), headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30, context=SSL_CTX) as r:
        js = json.load(r)
    if js.get("stat") != "OK":  # 該月還沒有資料時 stat 不是 OK
        return {}
    out = {}
    for roc_date, value in js["data"]:
        y, m, d = (int(x) for x in roc_date.split("/"))
        out[dt.date(y + 1911, m, d).isoformat()] = value.replace(",", "")
    return out


def main():
    with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
        rows = {r[0]: r[1] for r in list(csv.reader(f))[1:] if r}

    last = dt.date.fromisoformat(max(rows))
    today = dt.datetime.now(TAIPEI).date()

    month = last.replace(day=1)
    added = []
    while month <= today:
        for day, value in fetch_month(month).items():
            if day not in rows:
                added.append(day)
            rows[day] = value
        month = (month + dt.timedelta(days=32)).replace(day=1)

    with open(CSV_PATH, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(HEADER)
        w.writerows(sorted(rows.items()))

    print(f"新增 {len(added)} 天：{', '.join(sorted(added)) or '無'}（最後一天 {max(rows)}）")


if __name__ == "__main__":
    main()
