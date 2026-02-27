"""Unit tests for the sentiment analysis pipeline."""

import pytest

from bot.sentiment.analyzer import SentimentAnalyzer


@pytest.fixture
def analyzer():
    return SentimentAnalyzer(model="vader")


# ---------------------------------------------------------------------------
# Synchronous analysis
# ---------------------------------------------------------------------------


def test_positive_sentiment(analyzer):
    result = analyzer.analyze(
        "The stock market surged to record highs! Investors are thrilled with exceptional gains."
    )
    assert result["label"] == "POSITIVE"
    assert result["score"] > 0


def test_negative_sentiment(analyzer):
    result = analyzer.analyze(
        "Market crash! Stocks plummet amid fears of recession and economic collapse."
    )
    assert result["label"] == "NEGATIVE"
    assert result["score"] < 0


def test_neutral_sentiment(analyzer):
    result = analyzer.analyze("The market closed on Wednesday.")
    assert result["label"] == "NEUTRAL"


def test_result_keys(analyzer):
    result = analyzer.analyze("Some financial news text.")
    assert set(result.keys()) == {"label", "score", "positive", "negative", "neutral"}


def test_score_in_range(analyzer):
    result = analyzer.analyze("Great earnings results exceeded all expectations!")
    assert -1.0 <= result["score"] <= 1.0


def test_label_values(analyzer):
    for text in [
        "Incredible bull run, best quarter ever!",
        "Devastating losses, portfolio destroyed.",
        "Markets were flat.",
    ]:
        result = analyzer.analyze(text)
        assert result["label"] in ("POSITIVE", "NEGATIVE", "NEUTRAL")


# ---------------------------------------------------------------------------
# Async analysis
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_analyze_async(analyzer):
    result = await analyzer.analyze_async(
        "Strong quarterly results boost investor confidence."
    )
    assert result["label"] in ("POSITIVE", "NEGATIVE", "NEUTRAL")


@pytest.mark.asyncio
async def test_analyze_batch_returns_correct_count(analyzer):
    texts = [
        "Record highs for S&P 500 as bulls dominate.",
        "Stocks fall sharply on disappointing earnings.",
        "The Fed held rates steady at its latest meeting.",
    ]
    results = await analyzer.analyze_batch(texts)
    assert len(results) == 3


@pytest.mark.asyncio
async def test_analyze_batch_first_positive(analyzer):
    texts = ["Stocks rally strongly, investors celebrate huge gains."]
    results = await analyzer.analyze_batch(texts)
    assert results[0]["label"] == "POSITIVE"


@pytest.mark.asyncio
async def test_analyze_batch_second_negative(analyzer):
    texts = ["Stocks plummet on devastating recession fears and massive losses."]
    results = await analyzer.analyze_batch(texts)
    assert results[0]["label"] == "NEGATIVE"


# ---------------------------------------------------------------------------
# Score aggregation
# ---------------------------------------------------------------------------


def test_aggregate_positive_majority(analyzer):
    results = [
        {"label": "POSITIVE", "score": 0.6},
        {"label": "POSITIVE", "score": 0.4},
        {"label": "NEUTRAL", "score": 0.0},
    ]
    summary = analyzer.aggregate_scores(results)
    assert summary["label"] == "POSITIVE"
    assert summary["positive"] == 2
    assert summary["total"] == 3


def test_aggregate_negative_majority(analyzer):
    results = [
        {"label": "NEGATIVE", "score": -0.5},
        {"label": "NEGATIVE", "score": -0.3},
    ]
    summary = analyzer.aggregate_scores(results)
    assert summary["label"] == "NEGATIVE"
    assert summary["negative"] == 2


def test_aggregate_empty(analyzer):
    summary = analyzer.aggregate_scores([])
    assert summary["label"] == "NEUTRAL"
    assert summary["score"] == 0.0
    assert summary["total"] == 0


def test_aggregate_all_keys_present(analyzer):
    results = [{"label": "POSITIVE", "score": 0.3}]
    summary = analyzer.aggregate_scores(results)
    assert set(summary.keys()) == {
        "label", "score", "positive", "negative", "neutral", "total"
    }


# ---------------------------------------------------------------------------
# Transformers fallback
# ---------------------------------------------------------------------------


def test_transformers_fallback_to_vader(analyzer, monkeypatch):
    """If the Transformers backend fails, the analyzer falls back to VADER."""
    analyzer.model = "transformers"

    def _bad_load(_self):
        raise ImportError("transformers not installed")

    monkeypatch.setattr(SentimentAnalyzer, "_load_transformer", _bad_load)
    result = analyzer.analyze("Markets are rallying strongly today.")
    assert result["label"] in ("POSITIVE", "NEGATIVE", "NEUTRAL")
