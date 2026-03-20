"""
Sentiment Analyzer Module
Pre-processes text and calculates sentiment scores using VADER
"""

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import re


class SentimentAnalyzer:
    """
    Analyzes sentiment from text using VADER
    Optimized for financial and social media content
    """

    # Financial-specific word adjustments
    FINANCIAL_LEXICON = {
        # Bullish words
        "bullish": 2.5,
        "moon": 2.0,
        "rocket": 1.8,
        "🚀": 2.0,
        "buy": 1.5,
        "long": 1.2,
        "calls": 1.3,
        "breakout": 1.8,
        "undervalued": 1.5,
        "squeeze": 1.5,
        "diamond hands": 2.0,
        "hodl": 1.5,
        "tendies": 1.5,
        "green": 1.0,
        "pump": 1.2,
        "gain": 1.3,
        "profit": 1.5,
        "beat": 1.5,
        "upgrade": 1.8,
        "outperform": 1.5,
        "strong buy": 2.5,
        # Bearish words
        "bearish": -2.5,
        "dump": -2.0,
        "crash": -2.5,
        "sell": -1.5,
        "short": -1.2,
        "puts": -1.3,
        "overvalued": -1.5,
        "bag holder": -2.0,
        "red": -1.0,
        "loss": -1.5,
        "miss": -1.5,
        "downgrade": -1.8,
        "underperform": -1.5,
        "strong sell": -2.5,
        "tank": -2.0,
        "plunge": -2.0,
        "fear": -1.5,
        "recession": -2.0,
        "bankruptcy": -3.0,
    }

    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()

        # Update VADER lexicon with financial terms
        for word, score in self.FINANCIAL_LEXICON.items():
            self.analyzer.lexicon[word] = score

    def analyze_text(self, text: str) -> Dict:
        """
        Analyze sentiment of a single text

        Returns:
            Dict with compound, positive, negative, neutral scores
        """
        if not text:
            return {"compound": 0, "pos": 0, "neg": 0, "neu": 1.0}

        # Clean text
        text = self._clean_text(text)

        # Get VADER scores
        scores = self.analyzer.polarity_scores(text)

        # Add label
        compound = scores["compound"]
        if compound >= 0.3:
            scores["label"] = "bullish"
        elif compound <= -0.3:
            scores["label"] = "bearish"
        else:
            scores["label"] = "neutral"

        return scores

    def _clean_text(self, text: str) -> str:
        """Clean and preprocess text"""
        # Remove URLs
        text = re.sub(r"http\S+|www\S+", "", text)

        # Remove excessive whitespace
        text = " ".join(text.split())

        # Keep emojis (VADER handles them)
        # Keep cashtags and hashtags

        return text

    def analyze_batch(self, texts: List[str]) -> List[Dict]:
        """Analyze multiple texts"""
        return [self.analyze_text(text) for text in texts]

    def aggregate_sentiment(
        self,
        items: List[Dict],
        sentiment_key: str = "sentiment_score",
        weight_key: Optional[str] = None,
    ) -> Dict:
        """
        Aggregate sentiment from multiple items

        Args:
            items: List of dicts with sentiment scores
            sentiment_key: Key for sentiment value in each dict
            weight_key: Optional key for weighting (e.g., engagement_score)
        """
        if not items:
            return {
                "avg_sentiment": 0,
                "weighted_sentiment": 0,
                "bullish_count": 0,
                "bearish_count": 0,
                "neutral_count": 0,
                "total_count": 0,
                "bullish_pct": 0,
                "bearish_pct": 0,
                "neutral_pct": 100,
            }

        sentiments = []
        weights = []
        bullish = 0
        bearish = 0
        neutral = 0

        for item in items:
            score = item.get(sentiment_key)
            if score is not None:
                sentiments.append(score)

                if weight_key and item.get(weight_key):
                    weights.append(item.get(weight_key, 1))
                else:
                    weights.append(1)

                if score > 0.2:
                    bullish += 1
                elif score < -0.2:
                    bearish += 1
                else:
                    neutral += 1

        if not sentiments:
            return {
                "avg_sentiment": 0,
                "weighted_sentiment": 0,
                "bullish_count": 0,
                "bearish_count": 0,
                "neutral_count": 0,
                "total_count": 0,
                "bullish_pct": 0,
                "bearish_pct": 0,
                "neutral_pct": 100,
            }

        avg_sentiment = sum(sentiments) / len(sentiments)

        # Weighted average
        total_weight = sum(weights)
        weighted_sentiment = (
            sum(s * w for s, w in zip(sentiments, weights)) / total_weight
            if total_weight > 0
            else avg_sentiment
        )

        total = len(sentiments)

        return {
            "avg_sentiment": round(avg_sentiment, 3),
            "weighted_sentiment": round(weighted_sentiment, 3),
            "bullish_count": bullish,
            "bearish_count": bearish,
            "neutral_count": neutral,
            "total_count": total,
            "bullish_pct": round(bullish / total * 100, 1),
            "bearish_pct": round(bearish / total * 100, 1),
            "neutral_pct": round(neutral / total * 100, 1),
        }

    def time_weighted_sentiment(
        self,
        items: List[Dict],
        sentiment_key: str = "sentiment_score",
        time_key: str = "created_at",
        decay_hours: int = 24,
    ) -> float:
        """
        Calculate time-weighted sentiment (more recent = higher weight)

        Args:
            items: List of dicts with sentiment and timestamp
            sentiment_key: Key for sentiment value
            time_key: Key for timestamp
            decay_hours: Hours after which weight decays to 50%
        """
        if not items:
            return 0.0

        now = datetime.utcnow()
        weighted_sum = 0.0
        weight_sum = 0.0

        for item in items:
            score = item.get(sentiment_key)
            timestamp = item.get(time_key)

            if score is None:
                continue

            # Calculate time-based weight
            if isinstance(timestamp, datetime):
                hours_ago = (now - timestamp).total_seconds() / 3600
            else:
                hours_ago = 12  # Default to 12 hours if unknown

            # Exponential decay
            weight = 0.5 ** (hours_ago / decay_hours)

            weighted_sum += score * weight
            weight_sum += weight

        return weighted_sum / weight_sum if weight_sum > 0 else 0.0

    def detect_sentiment_shift(
        self,
        items: List[Dict],
        sentiment_key: str = "sentiment_score",
        time_key: str = "created_at",
    ) -> Dict:
        """
        Detect if sentiment is shifting over time

        Returns:
            Dict with trend direction and magnitude
        """
        if len(items) < 4:
            return {"trend": "insufficient_data", "magnitude": 0}

        # Sort by time
        sorted_items = sorted(
            [i for i in items if i.get(time_key)],
            key=lambda x: x.get(time_key, datetime.min),
        )

        if len(sorted_items) < 4:
            return {"trend": "insufficient_data", "magnitude": 0}

        # Split into older half and newer half
        mid = len(sorted_items) // 2
        older = sorted_items[:mid]
        newer = sorted_items[mid:]

        older_sentiments = [
            i.get(sentiment_key, 0) for i in older if i.get(sentiment_key) is not None
        ]
        newer_sentiments = [
            i.get(sentiment_key, 0) for i in newer if i.get(sentiment_key) is not None
        ]

        if not older_sentiments or not newer_sentiments:
            return {"trend": "insufficient_data", "magnitude": 0}

        older_avg = sum(older_sentiments) / len(older_sentiments)
        newer_avg = sum(newer_sentiments) / len(newer_sentiments)

        change = newer_avg - older_avg

        if change > 0.15:
            trend = "improving"
        elif change < -0.15:
            trend = "declining"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "magnitude": round(change, 3),
            "older_avg": round(older_avg, 3),
            "newer_avg": round(newer_avg, 3),
        }

    def get_sentiment_label(self, score: float) -> str:
        """Convert numeric score to label"""
        if score >= 0.5:
            return "very_bullish"
        elif score >= 0.2:
            return "bullish"
        elif score <= -0.5:
            return "very_bearish"
        elif score <= -0.2:
            return "bearish"
        else:
            return "neutral"

    def analyze_with_context(self, text: str, ticker: str) -> Dict:
        """
        Analyze text with ticker context
        Boosts relevance if ticker is mentioned
        """
        scores = self.analyze_text(text)

        # Check if ticker is mentioned
        ticker_upper = ticker.upper()
        text_upper = text.upper()

        if ticker_upper in text_upper or f"${ticker_upper}" in text_upper:
            scores["ticker_mentioned"] = True
            scores["relevance"] = 1.0
        else:
            scores["ticker_mentioned"] = False
            scores["relevance"] = 0.5

        return scores


def get_sentiment_analyzer():
    """Factory function"""
    return SentimentAnalyzer()


if __name__ == "__main__":
    analyzer = get_sentiment_analyzer()

    # Test cases
    test_texts = [
        "AAPL is looking bullish! Earnings beat expectations 🚀",
        "I'm bearish on this stock. The valuation is way too high.",
        "Just holding my position. Not sure which way it goes.",
        "$TSLA to the moon! Diamond hands! 💎🙌",
        "Company might go bankrupt. Selling everything.",
    ]

    print("Testing Sentiment Analysis:")
    print("=" * 50)

    for text in test_texts:
        result = analyzer.analyze_text(text)
        print(f"\nText: {text[:50]}...")
        print(f"Score: {result['compound']:.2f} ({result['label']})")

    # Test aggregation
    items = [
        {"sentiment_score": 0.8, "engagement_score": 100},
        {"sentiment_score": 0.5, "engagement_score": 50},
        {"sentiment_score": -0.3, "engagement_score": 200},
        {"sentiment_score": 0.6, "engagement_score": 75},
    ]

    agg = analyzer.aggregate_sentiment(items, weight_key="engagement_score")
    print(f"\nAggregated Sentiment:")
    print(f"  Average: {agg['avg_sentiment']:.2f}")
    print(f"  Weighted: {agg['weighted_sentiment']:.2f}")
    print(f"  Bullish: {agg['bullish_pct']}%, Bearish: {agg['bearish_pct']}%")
