"""Entry point for the Market Sentiment Telegram Bot."""

import asyncio
import logging
import sys

from telegram.ext import Application, CommandHandler

from bot.config import Config
from bot.database.db import Database
from bot.handlers.commands import (
    alerts_handler,
    help_handler,
    risk_handler,
    sentiment_handler,
    start_handler,
    ticker_handler,
)
from bot.sentiment.analyzer import SentimentAnalyzer
from bot.sentiment.scraper import NewsScraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def main() -> None:
    config = Config.from_env()

    db = Database(config.db_url)
    await db.connect()

    app = Application.builder().token(config.telegram_token).build()

    app.bot_data["db"] = db
    app.bot_data["config"] = config
    app.bot_data["analyzer"] = SentimentAnalyzer(model=config.sentiment_model)
    app.bot_data["scraper"] = NewsScraper(api_key=config.news_api_key)

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("sentiment", sentiment_handler))
    app.add_handler(CommandHandler("ticker", ticker_handler))
    app.add_handler(CommandHandler("alerts", alerts_handler))
    app.add_handler(CommandHandler("risk", risk_handler))

    logger.info("Bot starting…")
    try:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        # Block until the process is interrupted (SIGINT / SIGTERM)
        await asyncio.Event().wait()
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
        await db.disconnect()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
