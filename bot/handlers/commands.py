"""Telegram command handlers for the Market Sentiment Bot."""

import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot.database.models import SignalHistory, UserRequest
from bot.sentiment.analyzer import SentimentAnalyzer
from bot.sentiment.scraper import NewsScraper

logger = logging.getLogger(__name__)

_SENTIMENT_EMOJI = {
    "POSITIVE": "📈",
    "NEGATIVE": "📉",
    "NEUTRAL": "➡️",
}

_RISK_LEVELS = ("conservative", "moderate", "aggressive")

_RISK_DESCRIPTIONS = {
    "conservative": "Low-volatility signals only. Alerts when |score| > 0.5.",
    "moderate": "Balanced alerts. Triggers when |score| > 0.25.",
    "aggressive": "All signals broadcast. Triggers when |score| > 0.05.",
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _log_request(
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    username: str,
    command: str,
    ticker: str = None,
) -> None:
    """Persist a user command invocation to the database (best-effort)."""
    db = context.bot_data.get("db")
    if db is None:
        return
    try:
        async with db.get_session() as session:
            session.add(
                UserRequest(
                    user_id=user_id,
                    username=username,
                    command=command,
                    ticker=ticker,
                )
            )
            await session.commit()
    except Exception as exc:
        logger.warning("Failed to log request: %s", exc)


def _get_analyzer(context: ContextTypes.DEFAULT_TYPE) -> SentimentAnalyzer:
    return context.bot_data.get("analyzer") or SentimentAnalyzer()


def _get_scraper(context: ContextTypes.DEFAULT_TYPE) -> NewsScraper:
    return context.bot_data.get("scraper") or NewsScraper()


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start — send welcome message."""
    user = update.effective_user
    await _log_request(context, user.id, user.username or "", "start")
    await update.message.reply_text(
        f"👋 Hello, {user.first_name}!\n\n"
        "I'm the *Market Sentiment Bot* — your real-time financial news analyzer.\n\n"
        "I scrape the latest financial headlines, apply NLP sentiment scoring, "
        "and alert you when market momentum shifts.\n\n"
        "Use /help to see available commands.",
        parse_mode=ParseMode.MARKDOWN,
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help — list all commands."""
    await update.message.reply_text(
        "*📊 Market Sentiment Bot — Commands*\n\n"
        "/sentiment `TICKER` — Aggregated sentiment for a ticker\n"
        "/ticker `TICKER` — Headline-level sentiment breakdown\n"
        "/alerts `on|off` — Enable/disable real-time alerts\n"
        "/risk `conservative|moderate|aggressive` — Set risk profile\n"
        "/start — Welcome message\n"
        "/help — Show this help text",
        parse_mode=ParseMode.MARKDOWN,
    )


async def sentiment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /sentiment TICKER — return aggregated NLP sentiment score."""
    user = update.effective_user
    args = context.args
    if not args:
        await update.message.reply_text(
            "⚠️ Please provide a ticker symbol.\nExample: `/sentiment AAPL`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    ticker = args[0].upper()
    await _log_request(context, user.id, user.username or "", "sentiment", ticker)
    await update.message.reply_text(
        f"🔍 Analyzing sentiment for *{ticker}*…",
        parse_mode=ParseMode.MARKDOWN,
    )

    scraper = _get_scraper(context)
    analyzer = _get_analyzer(context)
    articles = await scraper.get_news_for_ticker(ticker)

    if not articles:
        await update.message.reply_text(
            f"⚠️ No recent news found for *{ticker}*. Try a different ticker.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    results = await analyzer.analyze_batch([a["text"] for a in articles])
    summary = analyzer.aggregate_scores(results)
    emoji = _SENTIMENT_EMOJI.get(summary["label"], "➡️")

    db = context.bot_data.get("db")
    if db and articles:
        try:
            async with db.get_session() as session:
                session.add(
                    SignalHistory(
                        ticker=ticker,
                        sentiment_label=summary["label"],
                        sentiment_score=summary["score"],
                        headline=articles[0]["title"],
                        source_url=articles[0]["link"],
                    )
                )
                await session.commit()
        except Exception as exc:
            logger.warning("Failed to save signal: %s", exc)

    await update.message.reply_text(
        f"*{ticker} Sentiment Report* {emoji}\n\n"
        f"• Overall: *{summary['label']}* (score: `{summary['score']:+.4f}`)\n"
        f"• Articles analyzed: `{summary['total']}`\n"
        f"• 📈 Positive: `{summary['positive']}` | "
        f"📉 Negative: `{summary['negative']}` | "
        f"➡️ Neutral: `{summary['neutral']}`\n\n"
        "_Powered by VADER NLP_",
        parse_mode=ParseMode.MARKDOWN,
    )


async def ticker_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /ticker TICKER — headline-level sentiment breakdown."""
    user = update.effective_user
    args = context.args
    if not args:
        await update.message.reply_text(
            "⚠️ Please provide a ticker symbol.\nExample: `/ticker TSLA`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    ticker = args[0].upper()
    await _log_request(context, user.id, user.username or "", "ticker", ticker)
    await update.message.reply_text(
        f"📰 Fetching headlines for *{ticker}*…",
        parse_mode=ParseMode.MARKDOWN,
    )

    scraper = _get_scraper(context)
    analyzer = _get_analyzer(context)
    articles = await scraper.get_news_for_ticker(ticker, limit=5)

    if not articles:
        await update.message.reply_text(
            f"⚠️ No recent news found for *{ticker}*.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    results = await analyzer.analyze_batch([a["text"] for a in articles])
    lines = [f"*{ticker} — Headline Sentiment*\n"]
    for i, (article, result) in enumerate(zip(articles, results), 1):
        emoji = _SENTIMENT_EMOJI.get(result["label"], "➡️")
        title = article["title"][:80] + ("…" if len(article["title"]) > 80 else "")
        lines.append(
            f"{i}. {emoji} `{result['label']}` ({result['score']:+.3f})\n_{title}_"
        )

    await update.message.reply_text(
        "\n\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )


async def alerts_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /alerts on|off — toggle real-time sentiment alerts."""
    user = update.effective_user
    args = context.args
    if not args or args[0].lower() not in ("on", "off"):
        await update.message.reply_text(
            "⚠️ Usage: `/alerts on` or `/alerts off`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    state = args[0].lower()
    await _log_request(context, user.id, user.username or "", f"alerts_{state}")
    context.user_data["alerts"] = state == "on"

    if state == "on":
        await update.message.reply_text(
            "🔔 *Alerts enabled!* You will receive sentiment signals when "
            "significant momentum shifts are detected.",
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        await update.message.reply_text(
            "🔕 *Alerts disabled.* Use `/alerts on` to re-enable.",
            parse_mode=ParseMode.MARKDOWN,
        )


async def risk_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /risk LEVEL — configure the user's risk/alert sensitivity profile."""
    user = update.effective_user
    args = context.args
    if not args or args[0].lower() not in _RISK_LEVELS:
        levels = " | ".join(f"`{lvl}`" for lvl in _RISK_LEVELS)
        await update.message.reply_text(
            f"⚠️ Usage: `/risk {levels}`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    level = args[0].lower()
    await _log_request(context, user.id, user.username or "", "risk")
    context.user_data["risk_level"] = level

    await update.message.reply_text(
        f"⚙️ Risk profile set to *{level.capitalize()}*.\n\n_{_RISK_DESCRIPTIONS[level]}_",
        parse_mode=ParseMode.MARKDOWN,
    )
