import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import List

import feedparser
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# RSS feeds from major tech publications (AI-related)
FEEDS = [
    "https://openai.com/blog/rss.xml",
    "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
    "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
    "https://venturebeat.com/category/ai/feed/",
]

KEYWORDS = {
    "model", "llm", "agent", "inference", "ai", "artificial intelligence",
    "openai", "anthropic", "google", "gemini", "meta", "nvidia", "chip",
    "robot", "multimodal", "rag", "fine-tuning", "safety", "alignment",
}


def score_entry(title: str, summary: str) -> int:
    text = f"{title} {summary}".lower()
    return sum(1 for kw in KEYWORDS if kw in text)


def fetch_ai_trends(limit: int = 10) -> List[str]:
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    items = []

    for url in FEEDS:
        feed = feedparser.parse(url)
        for e in feed.entries:
            title = getattr(e, "title", "(No title)")
            summary = getattr(e, "summary", "")
            link = getattr(e, "link", "")

            published_parsed = getattr(e, "published_parsed", None)
            if published_parsed:
                published = datetime(*published_parsed[:6], tzinfo=timezone.utc)
                if published < week_ago:
                    continue
            score = score_entry(title, summary)
            if score == 0:
                continue
            items.append((score, title, link))

    # higher score first, then title
    items.sort(key=lambda x: (-x[0], x[1]))
    top = items[:limit]

    if not top:
        return ["目前沒有抓到近期 AI 熱門資訊，請稍後再試。"]

    results = ["🤖 本週 AI 趨勢科技重點："]
    for idx, (score, title, link) in enumerate(top, start=1):
        results.append(f"{idx}. {title}\n{link}")
    return results


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "你好！我是 AI 趨勢 Telegram Bot。\n"
        "輸入 /trends 可查看近期 AI 趨勢科技新聞。"
    )


async def trends(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("正在整理最新 AI 趨勢，請稍候...")
    lines = await asyncio.to_thread(fetch_ai_trends, 10)
    await update.message.reply_text("\n\n".join(lines), disable_web_page_preview=True)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "可用指令：\n"
        "/start - 啟動機器人\n"
        "/trends - 查詢近期 AI 趨勢科技\n"
        "/help - 顯示說明"
    )


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("請先設定環境變數 TELEGRAM_BOT_TOKEN")

    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("trends", trends))
    app.add_handler(CommandHandler("help", help_cmd))

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
