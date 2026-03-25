"""
Telegram Market Sentiment Bot
NLP-powered bot for real-time market sentiment analysis and automated alerts.
Author: Aleksandr Gvozdkov
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

from sentiment_analyzer import SentimentAnalyzer
from news_fetcher import NewsFetcher
from alert_manager import AlertManager

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize components
analyzer = SentimentAnalyzer()
news_fetcher = NewsFetcher()
alert_manager = AlertManager()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message when /start is issued."""
    user = update.effective_user
    welcome_text = (
        f"👋 Welcome {user.first_name}!\n\n"
        "📡 *Telegram Market Sentiment Bot*\n\n"
        "I analyze real-time market sentiment from news and social media "
        "to keep you informed about market movements.\n\n"
        "*Available commands:*\n"
        "/sentiment <TICKER> — Get sentiment for a ticker\n"
        "/alerts — Manage alert settings\n"
        "/watchlist — View/edit your watchlist\n"
        "/report — Full market sentiment report\n"
        "/help — Show this message"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')


async def sentiment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get market sentiment for a given ticker."""
    if not context.args:
        await update.message.reply_text("Usage: /sentiment <TICKER>\nExample: /sentiment AAPL")
        return
    
    ticker = context.args[0].upper()
    await update.message.reply_text(f"⏳ Analyzing sentiment for {ticker}...")
    
    # Fetch recent news
    articles = await news_fetcher.fetch(ticker, limit=20)
    
    if not articles:
        await update.message.reply_text(f"❌ No recent news found for {ticker}")
        return
    
    # Analyze sentiment
    result = analyzer.analyze(articles)
    
    # Format response
    emoji = "📈" if result['sentiment'] == 'Bullish' else "📉" if result['sentiment'] == 'Bearish' else "➡️"
    response = (
        f"{emoji} *{ticker} Sentiment Analysis*\n"
        f"{'─' * 30}\n"
        f"🎯 Overall: *{result['sentiment']}*\n"
        f"📊 Score: {result['score']:.2f}\n"
        f"📰 Articles analyzed: {result['count']}\n"
        f"🕐 Updated: {datetime.now().strftime('%H:%M UTC')}\n\n"
        f"*Sentiment Breakdown:*\n"
        f"  🟢 Bullish: {result['bullish_pct']:.0f}%\n"
        f"  🔴 Bearish: {result['bearish_pct']:.0f}%\n"
        f"  ⚪ Neutral: {result['neutral_pct']:.0f}%"
    )
    
    keyboard = [[
        InlineKeyboardButton("📊 Full Report", callback_data=f"report_{ticker}"),
        InlineKeyboardButton("🔔 Set Alert", callback_data=f"alert_{ticker}")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(response, parse_mode='Markdown', reply_markup=reply_markup)


async def alerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manage alert settings."""
    user_id = update.effective_user.id
    user_alerts = alert_manager.get_alerts(user_id)
    
    if not user_alerts:
        response = "🔔 *Alert Settings*\n\nYou have no active alerts.\nUse /sentiment <TICKER> and click 'Set Alert' to add one."
    else:
        response = "🔔 *Your Active Alerts:*\n\n"
        for ticker, threshold in user_alerts.items():
            response += f"  • {ticker}: threshold {threshold:+.0%}\n"
    
    await update.message.reply_text(response, parse_mode='Markdown')


async def watchlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """View and edit watchlist."""
    user_id = update.effective_user.id
    watchlist = alert_manager.get_watchlist(user_id)
    
    if not watchlist:
        response = "📋 *Your Watchlist*\n\nYour watchlist is empty.\nAdd tickers: /watchlist add AAPL TSLA MSFT"
    else:
        tickers_str = ", ".join(watchlist)
        response = f"📋 *Your Watchlist:*\n{tickers_str}"
    
    await update.message.reply_text(response, parse_mode='Markdown')


async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate full market sentiment report."""
    await update.message.reply_text("⏳ Generating market report...")
    
    report = await news_fetcher.get_market_overview()
    response = (
        "📊 *Market Sentiment Report*\n"
        f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}\n"
        f"{'─' * 30}\n"
    )
    
    for sector, data in report.items():
        emoji = "📈" if data['sentiment'] == 'Bullish' else "📉" if data['sentiment'] == 'Bearish' else "➡️"
        response += f"{emoji} {sector}: {data['sentiment']} ({data['score']:+.2f})\n"
    
    await update.message.reply_text(response, parse_mode='Markdown')


def main() -> None:
    """Start the bot."""
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")
    
    app = Application.builder().token(token).build()
    
    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("sentiment", sentiment))
    app.add_handler(CommandHandler("alerts", alerts_command))
    app.add_handler(CommandHandler("watchlist", watchlist_command))
    app.add_handler(CommandHandler("report", report_command))
    
    logger.info("Bot started successfully")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
