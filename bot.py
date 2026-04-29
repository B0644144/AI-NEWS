import asyncio
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import feedparser
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from mcp_router import run_skills_concurrently

FEEDS = [
    "https://openai.com/blog/rss.xml",
    "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
    "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
    "https://venturebeat.com/category/ai/feed/",
]
KEYWORDS = {
    "model", "llm", "agent", "inference", "ai", "artificial intelligence", "openai", "anthropic", "google",
    "gemini", "meta", "nvidia", "chip", "robot", "multimodal", "rag", "fine-tuning", "safety", "alignment",
}
SCHEDULER = AsyncIOScheduler(timezone="UTC")


@dataclass
class TrendItem:
    title: str
    link: str
    summary: str
    source: str
    published: Optional[datetime]
    score: int


def strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text or "")).strip()


def score_entry(title: str, summary: str) -> int:
    text = f"{title} {summary}".lower()
    return sum(1 for kw in KEYWORDS if kw in text)


def summarize_text(text: str, max_sentences: int = 3) -> str:
    cleaned = strip_html(text)
    sentences = re.split(r"(?<=[。！？.!?])\s+", cleaned)
    picked = [s.strip() for s in sentences if len(s.strip()) > 25][:max_sentences]
    return " ".join(picked) if picked else cleaned[:220] + ("..." if len(cleaned) > 220 else "")


def fetch_ai_trends(limit: int = 10) -> List[TrendItem]:
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    items: List[TrendItem] = []
    for url in FEEDS:
        feed = feedparser.parse(url)
        source = getattr(feed.feed, "title", url)
        for e in feed.entries:
            title, raw_summary, link = getattr(e, "title", "(No title)"), getattr(e, "summary", ""), getattr(e, "link", "")
            published, published_parsed = None, getattr(e, "published_parsed", None)
            if published_parsed:
                published = datetime(*published_parsed[:6], tzinfo=timezone.utc)
                if published < week_ago:
                    continue
            score = score_entry(title, raw_summary)
            if score > 0:
                items.append(TrendItem(title, link, summarize_text(raw_summary), source, published, score))
    return sorted(items, key=lambda x: (-x.score, x.title))[:limit]


def format_digest_markdown(items: List[TrendItem]) -> str:
    lines = [f"# AI 趨勢摘要 ({datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')})", ""]
    for idx, item in enumerate(items, start=1):
        published = item.published.strftime("%Y-%m-%d") if item.published else "未知日期"
        lines += [f"## {idx}. {item.title}", f"- 來源：{item.source}", f"- 日期：{published}", f"- 連結：{item.link}", f"- 摘要：{item.summary}", ""]
    return "\n".join(lines)


async def run_digest_pipeline(targets: List[str]) -> str:
    items = await asyncio.to_thread(fetch_ai_trends, 8)
    if not items:
        return "目前沒有可摘要的文章。"
    markdown = format_digest_markdown(items)
    title = datetime.now(timezone.utc).strftime("AI 趨勢摘要 %Y-%m-%d")
    results = await run_skills_concurrently(targets, title, markdown)
    return "✅ 多工流程完成\n" + "\n".join(f"- {r}" for r in results) + "\n\n---\n" + markdown[:2600]


async def scheduled_digest_job(chat_id: int, app: Application, targets: List[str]):
    msg = await run_digest_pipeline(targets)
    await app.bot.send_message(chat_id=chat_id, text=msg, disable_web_page_preview=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("/trends 看趨勢\n/digest [mail notion obsidian]\n/digest --schedule 07:30")


async def trends(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    items = await asyncio.to_thread(fetch_ai_trends, 10)
    if not items:
        await update.message.reply_text("目前沒有抓到近期 AI 熱門資訊，請稍後再試。")
        return
    text = "🤖 本週 AI 趨勢科技重點：\n\n" + "\n\n".join([f"{i}. {it.title}\n{it.link}" for i, it in enumerate(items, 1)])
    await update.message.reply_text(text, disable_web_page_preview=True)


async def digest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = [a.lower() for a in context.args]
    if "--schedule" in args:
        idx = args.index("--schedule")
        if idx + 1 >= len(args):
            await update.message.reply_text("請提供時間，格式：/digest --schedule 07:30")
            return
        hhmm = args[idx + 1]
        if not re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", hhmm):
            await update.message.reply_text("時間格式錯誤，請用 HH:MM，例如 07:30")
            return
        h, m = map(int, hhmm.split(":"))
        targets = [a for a in args if a not in ["--schedule", hhmm]] or ["mail", "notion", "obsidian"]
        job_id = f"digest-{update.effective_chat.id}"
        if SCHEDULER.get_job(job_id):
            SCHEDULER.remove_job(job_id)
        SCHEDULER.add_job(scheduled_digest_job, "cron", id=job_id, hour=h, minute=m, args=[update.effective_chat.id, context.application, targets])
        await update.message.reply_text(f"已排程每日 {hhmm} (UTC) 自動寄送 digest，skills: {', '.join(targets)}")
        return

    targets = args or ["mail", "notion", "obsidian"]
    await update.message.reply_text(f"開始摘要並執行 skills: {', '.join(targets)}")
    await update.message.reply_text(await run_digest_pipeline(targets), disable_web_page_preview=True)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("/digest --schedule 07:30 每天排程\n/digest mail 只寄信\n/digest notion obsidian 指定 skills")


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("請先設定環境變數 TELEGRAM_BOT_TOKEN")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("trends", trends))
    app.add_handler(CommandHandler("digest", digest))
    app.add_handler(CommandHandler("help", help_cmd))
    if not SCHEDULER.running:
        SCHEDULER.start()
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
