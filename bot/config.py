"""Bot configuration loaded from environment variables."""

import os
from dataclasses import dataclass


@dataclass
class Config:
    """Holds all runtime configuration for the bot."""

    telegram_token: str
    db_url: str
    news_api_key: str = ""
    sentiment_model: str = "vader"

    @classmethod
    def from_env(cls) -> "Config":
        """Build a Config from environment variables.

        Required:
            TELEGRAM_BOT_TOKEN — token issued by @BotFather.

        Optional:
            DATABASE_URL      — SQLAlchemy async DSN (default: local PostgreSQL).
            NEWS_API_KEY      — NewsAPI.org key for extended coverage.
            SENTIMENT_MODEL   — "vader" (default) or "transformers".
        """
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required.")
        return cls(
            telegram_token=token,
            db_url=os.environ.get(
                "DATABASE_URL",
                "postgresql+asyncpg://marketbot:marketbot@localhost/marketbot",
            ),
            news_api_key=os.environ.get("NEWS_API_KEY", ""),
            sentiment_model=os.environ.get("SENTIMENT_MODEL", "vader"),
        )
