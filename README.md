<!-- 這份說了算：這個專案怎麼運作、怎麼部署。和別份講的不一樣時，以這份為準 -->
# 台灣加權報酬指數 App

手機點開就能看「台灣發行量加權股價報酬指數」（還原除權息）的每月曲線。
每個點顯示當月月底的收盤點數，以及從你選的起點算起漲了幾倍。

## 檔案在做什麼

| 檔案 | 用途 |
|---|---|
| `index.html` | 網頁本體。曲線、起點選單、對數／一般刻度切換、每月資料表 |
| `taiex_total_return_daily.csv` | 每天的收盤點數，2003-01-02 起。**資料只有這一份** |
| `update.py` | 去證交所抓最新點數，補進 CSV。只用 Python 內建套件 |
| `.github/workflows/update.yml` | 排程：每個平日台北 15:00 自動跑 `update.py` |
| `manifest.webmanifest`、`icon*` | 讓手機可以「加到主畫面」，看起來像 App |

## 倍數怎麼算

- 每月的點 = 該月**最後一個交易日**的收盤點數。
- 倍數 = 該月月底點數 ÷ 起點月份**第一個交易日**的收盤點數。
- 例：起點選 2003 年 1 月，基準是 2003-01-02 的 4,524.92 點。

## 自動更新

- GitHub Actions（GitHub 免費的雲端排程）在週一到週五 UTC 07:00 跑，也就是台北 15:00。
- 國定假日沒開盤也會跑，只是抓不到新資料，就不會 commit。
- GitHub 排程常常晚 5～30 分鐘才開始，這是正常的。
- 想立刻更新：到 GitHub repo 的 Actions 頁，點「每日更新報酬指數」→「Run workflow」。
- 本機手動更新：`python update.py`

資料來源：[臺灣證券交易所 發行量加權股價報酬指數](https://www.twse.com.tw/zh/indices/taiex/mfi94u.html)
（API：`https://www.twse.com.tw/rwd/zh/TAIEX/MFI94U?date=YYYYMMDD&response=json`，一次回傳一整個月）

## 本機預覽

網頁要透過伺服器開，直接雙擊 `index.html` 會讀不到 CSV：

```bash
python -m http.server 8765
```

然後開 http://localhost:8765
