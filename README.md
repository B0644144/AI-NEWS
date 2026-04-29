# AI 趨勢 Telegram Bot

這是一個可以在 Telegram 上查詢「近期 AI 趨勢科技新聞」的機器人。

## 功能
- `/start`：啟動機器人並顯示歡迎訊息
- `/trends`：抓取多個科技媒體 RSS，整理近 7 天 AI 相關趨勢新聞
- `/help`：查看指令說明

## 資料來源
目前預設抓取以下 RSS：
- OpenAI Blog
- MIT Technology Review（AI topic）
- The Verge（AI）
- VentureBeat（AI）

> 可依需求在 `bot.py` 的 `FEEDS` 清單中新增或替換來源。

## 安裝與執行

### 1) 建立 Telegram Bot Token
1. 在 Telegram 找 `@BotFather`
2. 輸入 `/newbot` 建立機器人
3. 取得 token（格式像 `123456:ABC-DEF...`）

### 2) 安裝依賴
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3) 設定環境變數
```bash
export TELEGRAM_BOT_TOKEN="你的token"
```

### 4) 啟動
```bash
python bot.py
```

## 設計說明
- 機器人使用 long polling 模式執行。
- `/trends` 會：
  1. 抓取 RSS 內容
  2. 過濾近 7 天
  3. 以 AI 關鍵字計分
  4. 依分數排序後回傳前 10 則

## 可擴充方向
- 加入更多新聞來源（如 Hugging Face、arXiv cs.AI）
- 將資料快取到 Redis，降低重複抓取
- 支援每日固定時間主動推播（JobQueue）
- 改用 LLM 摘要每則新聞重點
