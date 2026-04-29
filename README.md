# AI 趨勢 Telegram Bot（MCP Skills + 排程）

## 新功能
- `/digest --schedule 07:30`：每天固定時間自動執行摘要流程（UTC）。
- `/digest --unschedule`：取消目前 chat 的排程。
- 排程持久化：Bot 重啟後會自動恢復已設定排程。
- Mail skill 支援 HTML 晨報模板（更像電子報），並對內容做 HTML escape。
- Notion skill 會自動偵測資料庫的 title 欄位（不再固定 `Name`），且新增重試機制。
- 趨勢排序加入去重、來源權重、時效權重與關鍵字權重回饋。

## 指令
- `/trends`
- `/digest`
- `/digest mail`
- `/digest notion obsidian`
- `/digest --schedule 07:30`
- `/digest --schedule 07:30 mail`（排程只寄信）
- `/digest --unschedule`

## Skills
- `mail`：寄送純文字 + HTML 郵件
- `notion`：寫入 Notion database page（自動對應 title 欄位）
- `obsidian`：輸出 markdown 到 vault

## 環境變數
### 必填
- `TELEGRAM_BOT_TOKEN`

### Mail
- `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD`
- `MAIL_FROM` / `MAIL_TO`

### Notion
- `NOTION_TOKEN`
- `NOTION_DATABASE_ID`

### Obsidian
- `OBSIDIAN_VAULT_PATH`

### 選填（資料持久化）
- `BOT_DATA_DIR`（預設 `.bot_data`）

## 啟動
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python bot.py
```
