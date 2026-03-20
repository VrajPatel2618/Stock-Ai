"""
Intelligence Aggregator Module
Combines data from all sources and produces unified analysis
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

from ai.sentiment_analyzer import SentimentAnalyzer
from ai.ollama_client import OllamaAnalyzer


class IntelligenceAggregator:
    """
    Aggregates data from multiple sources and produces comprehensive analysis
    """

    # Source weights for final sentiment calculation
    SOURCE_WEIGHTS = {"reddit": 0.30, "stocktwits": 0.20, "news": 0.35, "forums": 0.15}

    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()
        self.ollama = OllamaAnalyzer()

    def aggregate_social_data(
        self,
        reddit_posts: List[Dict],
        stocktwits_posts: List[Dict],
        forum_posts: List[Dict] = None,
    ) -> Dict:
        """
        Aggregate social media data from all sources

        Args:
            reddit_posts: Posts from Reddit
            stocktwits_posts: Messages from StockTwits
            forum_posts: Other forum posts
        """
        forum_posts = forum_posts or []

        # Calculate sentiment for each source
        reddit_agg = self.sentiment_analyzer.aggregate_sentiment(
            reddit_posts, sentiment_key="sentiment_score", weight_key="engagement_score"
        )

        stocktwits_agg = self.sentiment_analyzer.aggregate_sentiment(
            stocktwits_posts,
            sentiment_key="sentiment_score",
            weight_key="engagement_score",
        )

        forum_agg = self.sentiment_analyzer.aggregate_sentiment(
            forum_posts, sentiment_key="sentiment_score"
        )

        # Time-weighted sentiment
        reddit_time_weighted = self.sentiment_analyzer.time_weighted_sentiment(
            reddit_posts, decay_hours=24
        )
        stocktwits_time_weighted = self.sentiment_analyzer.time_weighted_sentiment(
            stocktwits_posts, decay_hours=12
        )

        # Detect sentiment shifts
        reddit_trend = self.sentiment_analyzer.detect_sentiment_shift(reddit_posts)

        # Combined weighted sentiment
        total_weight = 0
        weighted_sum = 0

        if reddit_agg["total_count"] > 0:
            weighted_sum += (
                reddit_agg["weighted_sentiment"] * self.SOURCE_WEIGHTS["reddit"]
            )
            total_weight += self.SOURCE_WEIGHTS["reddit"]

        if stocktwits_agg["total_count"] > 0:
            weighted_sum += (
                stocktwits_agg["weighted_sentiment"] * self.SOURCE_WEIGHTS["stocktwits"]
            )
            total_weight += self.SOURCE_WEIGHTS["stocktwits"]

        if forum_agg["total_count"] > 0:
            weighted_sum += (
                forum_agg["weighted_sentiment"] * self.SOURCE_WEIGHTS["forums"]
            )
            total_weight += self.SOURCE_WEIGHTS["forums"]

        combined_sentiment = weighted_sum / total_weight if total_weight > 0 else 0

        return {
            "combined_sentiment": round(combined_sentiment, 3),
            "reddit": {
                **reddit_agg,
                "time_weighted": round(reddit_time_weighted, 3),
                "trend": reddit_trend,
            },
            "stocktwits": {
                **stocktwits_agg,
                "time_weighted": round(stocktwits_time_weighted, 3),
            },
            "forums": forum_agg,
            "total_posts": (
                reddit_agg["total_count"]
                + stocktwits_agg["total_count"]
                + forum_agg["total_count"]
            ),
            "aggregated_at": datetime.utcnow().isoformat(),
        }

    def aggregate_news_data(self, news_articles: List[Dict]) -> Dict:
        """
        Aggregate news article data
        """
        if not news_articles:
            return {
                "avg_sentiment": 0,
                "article_count": 0,
                "sources": [],
                "top_articles": [],
            }

        sentiments = [
            a.get("sentiment_score", 0)
            for a in news_articles
            if a.get("sentiment_score") is not None
        ]
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0

        # Count by source
        sources = {}
        for article in news_articles:
            source = article.get("source", "Unknown")
            sources[source] = sources.get(source, 0) + 1

        # Get top articles by relevance
        top_articles = sorted(
            news_articles,
            key=lambda x: (
                x.get("relevance_score", 0),
                abs(x.get("sentiment_score", 0)),
            ),
            reverse=True,
        )[:5]

        return {
            "avg_sentiment": round(avg_sentiment, 3),
            "article_count": len(news_articles),
            "sources": sources,
            "top_articles": [
                {
                    "title": a.get("title", ""),
                    "source": a.get("source", ""),
                    "sentiment": a.get("sentiment_score", 0),
                    "url": a.get("url", ""),
                }
                for a in top_articles
            ],
            "sentiment_label": self.sentiment_analyzer.get_sentiment_label(
                avg_sentiment
            ),
        }

    def get_market_data(self, ticker: str) -> Dict:
        """
        Get current market data for a ticker using yfinance
        """
        try:
            import yfinance as yf

            stock = yf.Ticker(ticker)
            hist = stock.history(period="5d")

            if hist.empty:
                return {
                    "price": 0,
                    "change_percent": 0,
                    "volume": 0,
                    "error": "No data",
                }

            current_price = hist["Close"].iloc[-1]
            prev_close = hist["Close"].iloc[-2] if len(hist) > 1 else current_price
            change_percent = ((current_price - prev_close) / prev_close) * 100
            volume = hist["Volume"].iloc[-1]

            return {
                "price": round(current_price, 2),
                "change_percent": round(change_percent, 2),
                "volume": int(volume),
                "prev_close": round(prev_close, 2),
                "high": round(hist["High"].iloc[-1], 2),
                "low": round(hist["Low"].iloc[-1], 2),
            }
        except Exception as e:
            print(f"Error fetching market data: {e}")
            return {"price": 0, "change_percent": 0, "volume": 0, "error": str(e)}

    def generate_full_analysis(
        self,
        ticker: str,
        reddit_posts: List[Dict],
        stocktwits_posts: List[Dict],
        news_articles: List[Dict],
        forum_posts: List[Dict] = None,
        market_data: Dict = None,
    ) -> Dict:
        """
        Generate comprehensive analysis combining all sources

        Args:
            ticker: Stock ticker symbol
            reddit_posts: Reddit posts
            stocktwits_posts: StockTwits messages
            news_articles: News articles
            forum_posts: Other forum posts
            market_data: Optional pre-fetched market data
        """
        forum_posts = forum_posts or []

        # Get market data if not provided
        if market_data is None:
            market_data = self.get_market_data(ticker)

        # Aggregate social data
        social_summary = self.aggregate_social_data(
            reddit_posts, stocktwits_posts, forum_posts
        )

        # Aggregate news data
        news_summary = self.aggregate_news_data(news_articles)

        # Prepare data for Ollama
        ollama_social_data = {
            "reddit_count": social_summary["reddit"]["total_count"],
            "reddit_sentiment": social_summary["reddit"]["weighted_sentiment"],
            "stocktwits_count": social_summary["stocktwits"]["total_count"],
            "stocktwits_sentiment": social_summary["stocktwits"]["weighted_sentiment"],
            "reddit_posts": reddit_posts[:10],  # Top 10 for context
        }

        # Get AI analysis
        ai_analysis = self.ollama.analyze_ticker(
            ticker=ticker,
            market_data=market_data,
            social_data=ollama_social_data,
            news_data=news_articles[:10],
        )

        # Calculate final sentiment (combine AI and rule-based)
        combined_social_news = (
            (
                social_summary["combined_sentiment"] * 0.5
                + news_summary["avg_sentiment"] * 0.5
            )
            if news_summary["article_count"] > 0
            else social_summary["combined_sentiment"]
        )

        # Determine overall sentiment label
        if combined_social_news > 0.3:
            sentiment_label = "bullish"
        elif combined_social_news < -0.3:
            sentiment_label = "bearish"
        else:
            sentiment_label = "neutral"

        return {
            "ticker": ticker.upper(),
            "generated_at": datetime.utcnow().isoformat(),
            # Market data
            "market": market_data,
            # Aggregated sentiment
            "sentiment": {
                "overall": sentiment_label,
                "score": round(combined_social_news, 3),
                "social_score": round(social_summary["combined_sentiment"], 3),
                "news_score": round(news_summary["avg_sentiment"], 3),
            },
            # Source breakdowns
            "sources": {
                "reddit": {
                    "count": social_summary["reddit"]["total_count"],
                    "sentiment": social_summary["reddit"]["weighted_sentiment"],
                    "bullish_pct": social_summary["reddit"]["bullish_pct"],
                    "trend": social_summary["reddit"]["trend"],
                },
                "stocktwits": {
                    "count": social_summary["stocktwits"]["total_count"],
                    "sentiment": social_summary["stocktwits"]["weighted_sentiment"],
                    "bullish_pct": social_summary["stocktwits"]["bullish_pct"],
                },
                "news": {
                    "count": news_summary["article_count"],
                    "sentiment": news_summary["avg_sentiment"],
                    "sources": list(news_summary["sources"].keys()),
                },
            },
            # AI analysis
            "ai_analysis": {
                "overall_sentiment": ai_analysis.get(
                    "overall_sentiment", sentiment_label
                ),
                "confidence": ai_analysis.get("confidence_score", 50),
                "key_reasoning": ai_analysis.get("key_reasoning", []),
                "risk_factors": ai_analysis.get("risk_factors", []),
                "predicted_trend": ai_analysis.get("predicted_trend", "sideways"),
                "recommendation": ai_analysis.get("recommendation", "hold"),
                "short_term_outlook": ai_analysis.get("short_term_outlook", ""),
                "model_used": ai_analysis.get("model_used", "unknown"),
            },
            # Top content
            "top_discussions": [
                {
                    "source": p.get("source", "reddit"),
                    "title": p.get("title", p.get("content", "")[:100]),
                    "sentiment": p.get("sentiment_score", 0),
                    "engagement": p.get("engagement_score", 0),
                    "url": p.get("url", ""),
                }
                for p in sorted(
                    reddit_posts + stocktwits_posts,
                    key=lambda x: x.get("engagement_score", 0),
                    reverse=True,
                )[:5]
            ],
            "top_news": news_summary["top_articles"],
            # Data quality
            "data_quality": {
                "total_social_posts": social_summary["total_posts"],
                "total_news_articles": news_summary["article_count"],
                "ai_available": self.ollama.is_available(),
                "confidence_level": (
                    "high"
                    if social_summary["total_posts"] > 20
                    else "medium" if social_summary["total_posts"] > 5 else "low"
                ),
            },
        }

    def get_quick_sentiment(
        self, ticker: str, reddit_posts: List[Dict], stocktwits_posts: List[Dict]
    ) -> Dict:
        """
        Quick sentiment calculation without AI analysis
        """
        social_summary = self.aggregate_social_data(reddit_posts, stocktwits_posts, [])

        sentiment = social_summary["combined_sentiment"]

        if sentiment > 0.3:
            label = "bullish"
        elif sentiment < -0.3:
            label = "bearish"
        else:
            label = "neutral"

        return {
            "ticker": ticker.upper(),
            "sentiment": label,
            "score": round(sentiment, 3),
            "total_posts": social_summary["total_posts"],
            "reddit_sentiment": social_summary["reddit"]["weighted_sentiment"],
            "stocktwits_sentiment": social_summary["stocktwits"]["weighted_sentiment"],
            "reddit_trend": social_summary["reddit"]["trend"]["trend"],
            "timestamp": datetime.utcnow().isoformat(),
        }


def get_intelligence_aggregator():
    """Factory function"""
    return IntelligenceAggregator()


if __name__ == "__main__":
    aggregator = get_intelligence_aggregator()

    # Test with mock data
    reddit_posts = [
        {
            "title": "AAPL earnings beat!",
            "sentiment_score": 0.8,
            "engagement_score": 100,
            "source": "reddit",
            "created_at": datetime.utcnow(),
        },
        {
            "title": "Bullish on Apple",
            "sentiment_score": 0.6,
            "engagement_score": 50,
            "source": "reddit",
            "created_at": datetime.utcnow() - timedelta(hours=2),
        },
    ]

    stocktwits_posts = [
        {
            "content": "$AAPL to the moon!",
            "sentiment_score": 0.9,
            "engagement_score": 40,
            "source": "stocktwits",
        },
        {
            "content": "Be careful, resistance ahead",
            "sentiment_score": -0.2,
            "engagement_score": 20,
            "source": "stocktwits",
        },
    ]

    news_articles = [
        {
            "title": "Apple Reports Strong Earnings",
            "sentiment_score": 0.7,
            "source": "Reuters",
            "url": "#",
        },
        {
            "title": "Analysts Upgrade Apple",
            "sentiment_score": 0.8,
            "source": "Bloomberg",
            "url": "#",
        },
    ]

    print("Generating full analysis for AAPL...")
    analysis = aggregator.generate_full_analysis(
        ticker="AAPL",
        reddit_posts=reddit_posts,
        stocktwits_posts=stocktwits_posts,
        news_articles=news_articles,
    )

    print("\n" + "=" * 50)
    print("ANALYSIS RESULTS")
    print("=" * 50)
    print(f"\nTicker: {analysis['ticker']}")
    print(
        f"Overall Sentiment: {analysis['sentiment']['overall']} ({analysis['sentiment']['score']:.2f})"
    )
    print(f"\nAI Analysis:")
    print(f"  Confidence: {analysis['ai_analysis']['confidence']}%")
    print(f"  Recommendation: {analysis['ai_analysis']['recommendation']}")
    print(f"  Predicted Trend: {analysis['ai_analysis']['predicted_trend']}")
