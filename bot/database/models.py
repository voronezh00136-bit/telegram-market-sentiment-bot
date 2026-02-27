"""SQLAlchemy ORM models for logging user requests and signal history."""

from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class UserRequest(Base):
    """Records every user command invocation for audit and analytics."""

    __tablename__ = "user_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    username = Column(String(255))
    command = Column(String(100), nullable=False)
    ticker = Column(String(20))
    created_at = Column(DateTime, default=lambda: datetime.utcnow(), nullable=False)


class SignalHistory(Base):
    """Stores generated sentiment signals for backtesting and trend analysis."""

    __tablename__ = "signal_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    sentiment_label = Column(String(20), nullable=False)
    sentiment_score = Column(Float, nullable=False)
    headline = Column(Text)
    source_url = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.utcnow(), nullable=False)
