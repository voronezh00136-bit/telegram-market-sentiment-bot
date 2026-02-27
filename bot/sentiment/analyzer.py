"""Sentiment analysis pipeline using VADER (NLTK) with optional Transformers backend."""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """Analyzes financial text sentiment.

    Uses VADER (lexicon-based, no model download at inference time) by default.
    Set *model* to ``"transformers"`` to enable a Hugging Face pipeline instead
    (requires a compatible model to be available on disk or via the Hub).
    """

    POSITIVE_THRESHOLD = 0.05
    NEGATIVE_THRESHOLD = -0.05

    def __init__(self, model: str = "vader") -> None:
        self.model = model
        self._vader: Optional[object] = None
        self._transformer_pipeline: Optional[object] = None

    # ------------------------------------------------------------------
    # Internal loaders (lazy, thread-safe for single-thread async usage)
    # ------------------------------------------------------------------

    def _load_vader(self) -> object:
        if self._vader is None:
            import nltk
            nltk.download("vader_lexicon", quiet=True)
            from nltk.sentiment.vader import SentimentIntensityAnalyzer
            self._vader = SentimentIntensityAnalyzer()
        return self._vader

    def _load_transformer(self) -> object:
        if self._transformer_pipeline is None:
            from transformers import pipeline  # type: ignore[import]
            self._transformer_pipeline = pipeline(
                "text-classification",
                model="ProsusAI/finbert",
                truncation=True,
            )
        return self._transformer_pipeline

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(self, text: str) -> dict:
        """Synchronously analyze *text* and return a sentiment result dict.

        Returns a dict with keys:
            label   — "POSITIVE", "NEGATIVE", or "NEUTRAL"
            score   — compound score in [-1, 1]
            positive, negative, neutral — component proportions
        """
        if self.model == "transformers":
            try:
                return self._analyze_transformer(text)
            except Exception as exc:
                logger.warning("Transformers backend failed (%s); falling back to VADER.", exc)
        return self._analyze_vader(text)

    def _analyze_vader(self, text: str) -> dict:
        analyzer = self._load_vader()
        scores = analyzer.polarity_scores(text)
        compound = scores["compound"]
        if compound >= self.POSITIVE_THRESHOLD:
            label = "POSITIVE"
        elif compound <= self.NEGATIVE_THRESHOLD:
            label = "NEGATIVE"
        else:
            label = "NEUTRAL"
        return {
            "label": label,
            "score": round(compound, 4),
            "positive": round(scores["pos"], 4),
            "negative": round(scores["neg"], 4),
            "neutral": round(scores["neu"], 4),
        }

    def _analyze_transformer(self, text: str) -> dict:
        pipe = self._load_transformer()
        # Truncate to avoid token-length errors
        result = pipe(text[:512])[0]
        raw_label = result["label"].upper()
        # FinBERT returns "positive"/"negative"/"neutral"
        label_map = {"POSITIVE": "POSITIVE", "NEGATIVE": "NEGATIVE", "NEUTRAL": "NEUTRAL"}
        label = label_map.get(raw_label, "NEUTRAL")
        raw_score = result["score"]
        signed_score = raw_score if label == "POSITIVE" else (-raw_score if label == "NEGATIVE" else 0.0)
        return {
            "label": label,
            "score": round(signed_score, 4),
            "positive": raw_score if label == "POSITIVE" else 0.0,
            "negative": raw_score if label == "NEGATIVE" else 0.0,
            "neutral": raw_score if label == "NEUTRAL" else 0.0,
        }

    async def analyze_async(self, text: str) -> dict:
        """Async wrapper — runs :meth:`analyze` in a thread pool executor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.analyze, text)

    async def analyze_batch(self, texts: list) -> list:
        """Analyze a list of texts concurrently and return results in the same order."""
        tasks = [self.analyze_async(t) for t in texts]
        return list(await asyncio.gather(*tasks))

    def aggregate_scores(self, results: list) -> dict:
        """Aggregate a list of per-article results into a single summary dict.

        Returns a dict with keys:
            label, score, positive, negative, neutral (counts), total
        """
        if not results:
            return {
                "label": "NEUTRAL",
                "score": 0.0,
                "positive": 0,
                "negative": 0,
                "neutral": 0,
                "total": 0,
            }
        avg_score = sum(r["score"] for r in results) / len(results)
        positive_count = sum(1 for r in results if r["label"] == "POSITIVE")
        negative_count = sum(1 for r in results if r["label"] == "NEGATIVE")
        neutral_count = sum(1 for r in results if r["label"] == "NEUTRAL")
        if avg_score >= self.POSITIVE_THRESHOLD:
            label = "POSITIVE"
        elif avg_score <= self.NEGATIVE_THRESHOLD:
            label = "NEGATIVE"
        else:
            label = "NEUTRAL"
        return {
            "label": label,
            "score": round(avg_score, 4),
            "positive": positive_count,
            "negative": negative_count,
            "neutral": neutral_count,
            "total": len(results),
        }
