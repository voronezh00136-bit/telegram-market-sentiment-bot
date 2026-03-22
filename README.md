# 📡 telegram-market-sentiment-bot

> NLP-powered Telegram bot for real-time market sentiment analysis and automated alerts.

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)
![NLP](https://img.shields.io/badge/NLP-FF6F61?style=for-the-badge&logo=openai&logoColor=white)
![License](https://img.shields.io/github/license/voronezh00136-bit/telegram-market-sentiment-bot?style=for-the-badge)

---

## 📌 About

A Telegram bot that uses Natural Language Processing (NLP) to analyze market sentiment from news feeds, social media, and financial data sources in real-time — then sends automated alerts to users based on configurable thresholds.

## ✨ Features

- 📰 Real-time news and social media sentiment scraping
- 🤖 NLP-based sentiment classification (Bullish / Bearish / Neutral)
- 🔔 Automated Telegram alerts with custom thresholds
- 📊 Market sentiment dashboard via bot commands
- 📈 Historical sentiment tracking and trend analysis
- ⚙️ Per-user customizable watchlists and alert settings

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Bot Framework | python-telegram-bot |
| NLP Engine | spaCy / Transformers (BERT) |
| Data Sources | NewsAPI, Reddit API, Twitter API |
| Scheduling | APScheduler |
| Storage | SQLite / PostgreSQL |

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/voronezh00136-bit/telegram-market-sentiment-bot.git
cd telegram-market-sentiment-bot

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your Telegram Bot Token and API keys

# Run the bot
python bot.py
```

## 🤖 Bot Commands

| Command | Description |
|---------|-------------|
| /start | Initialize the bot |
| /sentiment TICKER | Get current sentiment for a ticker |
| /alerts | Manage your alert settings |
| /watchlist | View/edit your watchlist |
| /report | Get a full market sentiment report |

---

## 👤 Author

**Aleksandr Gvozdkov** — [@voronezh00136-bit](https://github.com/voronezh00136-bit)
