"""
Forum Scraper Module
Scrapes stock discussions from financial forums like StockTwits
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import time
import re


class ForumScraper:
    """Scrapes stock discussions from financial forums"""

    STOCKTWITS_API = "https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json"

    def __init__(self):
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

    def fetch_stocktwits(self, ticker: str, limit: int = 30) -> List[Dict]:
        """
        Fetch messages from StockTwits API

        Args:
            ticker: Stock ticker symbol
            limit: Maximum messages to fetch
        """
        messages = []

        try:
            url = self.STOCKTWITS_API.format(ticker=ticker.upper())
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if "messages" in data:
                    for msg in data["messages"][:limit]:
                        processed = self._process_stocktwits_message(msg, ticker)
                        if processed:
                            messages.append(processed)
            else:
                print(f"StockTwits API returned {response.status_code}")

        except Exception as e:
            print(f"Error fetching StockTwits: {e}")

        return messages

    def _process_stocktwits_message(self, msg: Dict, ticker: str) -> Optional[Dict]:
        """Process a StockTwits message"""
        try:
            body = msg.get("body", "")

            # Get sentiment from StockTwits if available
            st_sentiment = msg.get("entities", {}).get("sentiment", {})
            if st_sentiment:
                sentiment_label = st_sentiment.get("basic", "Neutral")
                if sentiment_label == "Bullish":
                    sentiment = 0.7
                elif sentiment_label == "Bearish":
                    sentiment = -0.7
                else:
                    sentiment = 0.0
            else:
                # Fallback to VADER
                sentiment = self.sentiment_analyzer.polarity_scores(body)["compound"]

            # Parse timestamp
            created_at = datetime.utcnow()
            if "created_at" in msg:
                try:
                    created_at = datetime.strptime(
                        msg["created_at"], "%Y-%m-%dT%H:%M:%SZ"
                    )
                except:
                    pass

            # Get user info
            user = msg.get("user", {})

            return {
                "id": f"st_{msg.get('id', '')}",
                "source": "stocktwits",
                "ticker": ticker.upper(),
                "title": None,
                "content": body,
                "author": user.get("username", "anonymous"),
                "url": f"https://stocktwits.com/{user.get('username', '')}/message/{msg.get('id', '')}",
                "engagement_score": msg.get("likes", {}).get("total", 0),
                "sentiment_score": sentiment,
                "followers": user.get("followers", 0),
                "created_at": created_at,
            }
        except Exception as e:
            print(f"Error processing StockTwits message: {e}")
            return None

    def scrape_yahoo_discussions(self, ticker: str) -> List[Dict]:
        """
        Scrape Yahoo Finance discussions (limited - most are behind login)
        """
        discussions = []

        try:
            url = f"https://finance.yahoo.com/quote/{ticker}/community"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "lxml")

                # Yahoo Finance structure changes frequently
                # This is a best-effort scrape
                comments = soup.find_all("div", {"class": re.compile("comment")})

                for i, comment in enumerate(comments[:20]):
                    try:
                        text = comment.get_text(strip=True)
                        if text and len(text) > 20:
                            sentiment = self.sentiment_analyzer.polarity_scores(text)[
                                "compound"
                            ]

                            discussions.append(
                                {
                                    "id": f"yahoo_{ticker}_{i}",
                                    "source": "yahoo_finance",
                                    "ticker": ticker.upper(),
                                    "title": None,
                                    "content": text[:1000],
                                    "author": "yahoo_user",
                                    "url": url,
                                    "engagement_score": 0,
                                    "sentiment_score": sentiment,
                                    "created_at": datetime.utcnow(),
                                }
                            )
                    except:
                        continue

        except Exception as e:
            print(f"Error scraping Yahoo discussions: {e}")

        return discussions

    def fetch_all_forums(self, ticker: str, limit: int = 50) -> List[Dict]:
        """
        Fetch from all available forums

        Args:
            ticker: Stock ticker
            limit: Max total results
        """
        all_posts = []

        # StockTwits (most reliable)
        st_posts = self.fetch_stocktwits(ticker, limit=limit)
        all_posts.extend(st_posts)

        # Yahoo Finance (limited)
        # yahoo_posts = self.scrape_yahoo_discussions(ticker)
        # all_posts.extend(yahoo_posts)

        return all_posts[:limit]

    def get_sentiment_summary(self, posts: List[Dict]) -> Dict:
        """Calculate sentiment summary from posts"""
        if not posts:
            return {
                "count": 0,
                "avg_sentiment": 0,
                "bullish_pct": 0,
                "bearish_pct": 0,
                "neutral_pct": 100,
            }

        sentiments = [
            p["sentiment_score"] for p in posts if p.get("sentiment_score") is not None
        ]

        if not sentiments:
            return {
                "count": len(posts),
                "avg_sentiment": 0,
                "bullish_pct": 0,
                "bearish_pct": 0,
                "neutral_pct": 100,
            }

        avg_sentiment = sum(sentiments) / len(sentiments)

        bullish = sum(1 for s in sentiments if s > 0.2)
        bearish = sum(1 for s in sentiments if s < -0.2)
        neutral = len(sentiments) - bullish - bearish

        total = len(sentiments)

        return {
            "count": len(posts),
            "avg_sentiment": avg_sentiment,
            "bullish_pct": round(bullish / total * 100, 1),
            "bearish_pct": round(bearish / total * 100, 1),
            "neutral_pct": round(neutral / total * 100, 1),
        }


class MockForumScraper:
    """Mock forum scraper for testing"""

    def __init__(self):
        self.sentiment_analyzer = SentimentIntensityAnalyzer()

    def fetch_stocktwits(self, ticker: str, limit: int = 30) -> List[Dict]:
        return self.fetch_all_forums(ticker, limit)

    def fetch_all_forums(self, ticker: str, limit: int = 50) -> List[Dict]:
        """Return mock forum data"""
        mock_posts = [
            {
                "id": f"mock_st_{ticker}_1",
                "source": "stocktwits",
                "ticker": ticker.upper(),
                "title": None,
                "content": f"${ticker} looking strong! Breakout imminent 🚀",
                "author": "bull_trader",
                "url": f"https://stocktwits.com/mock/{ticker}",
                "engagement_score": 45,
                "sentiment_score": 0.8,
                "created_at": datetime.utcnow() - timedelta(minutes=30),
            },
            {
                "id": f"mock_st_{ticker}_2",
                "source": "stocktwits",
                "ticker": ticker.upper(),
                "title": None,
                "content": f"${ticker} holding support well. Accumulating here.",
                "author": "value_investor",
                "url": f"https://stocktwits.com/mock/{ticker}",
                "engagement_score": 32,
                "sentiment_score": 0.5,
                "created_at": datetime.utcnow() - timedelta(hours=1),
            },
            {
                "id": f"mock_st_{ticker}_3",
                "source": "stocktwits",
                "ticker": ticker.upper(),
                "title": None,
                "content": f"Be careful with ${ticker}, overbought on daily chart.",
                "author": "cautious_trader",
                "url": f"https://stocktwits.com/mock/{ticker}",
                "engagement_score": 28,
                "sentiment_score": -0.3,
                "created_at": datetime.utcnow() - timedelta(hours=2),
            },
        ]
        return mock_posts[:limit]

    def get_sentiment_summary(self, posts: List[Dict]) -> Dict:
        """Calculate sentiment summary from posts"""
        if not posts:
            return {
                "count": 0,
                "avg_sentiment": 0,
                "bullish_pct": 0,
                "bearish_pct": 0,
                "neutral_pct": 100,
            }

        sentiments = [p["sentiment_score"] for p in posts]
        return {
            "count": len(posts),
            "avg_sentiment": sum(sentiments) / len(sentiments),
            "bullish_pct": 60,
            "bearish_pct": 20,
            "neutral_pct": 20,
        }


def get_forum_scraper():
    """Factory function to get forum scraper"""
    try:
        scraper = ForumScraper()
        return scraper
    except Exception as e:
        print(f"Forum scraper error: {e}")
        return MockForumScraper()


if __name__ == "__main__":
    scraper = get_forum_scraper()

    print("Fetching StockTwits for AAPL...")
    posts = scraper.fetch_stocktwits("AAPL", limit=10)

    print(f"\nFound {len(posts)} posts:")
    for post in posts[:3]:
        print(f"  - {post['content'][:60]}...")
        print(f"    Sentiment: {post['sentiment_score']:.2f}")

    summary = scraper.get_sentiment_summary(posts)
    print(f"\nSentiment Summary: {summary}")
