"""
News Search Client
Fetches latest news using DuckDuckGo search (no API key required)
"""

from duckduckgo_search import DDGS
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import time
import re


class NewsSearchClient:
    """Search and fetch news articles using DuckDuckGo"""

    def __init__(self):
        self.sentiment_analyzer = SentimentIntensityAnalyzer()

    def search_news(
        self, query: str, max_results: int = 20, timelimit: str = "w"
    ) -> List[Dict]:
        """
        Search for news articles

        Args:
            query: Search query
            max_results: Maximum number of results
            timelimit: Time filter - 'd' (day), 'w' (week), 'm' (month)
        """
        articles = []

        try:
            with DDGS() as ddgs:
                results = ddgs.news(query, max_results=max_results, timelimit=timelimit)

                for result in results:
                    article = self._process_result(result, query)
                    if article:
                        articles.append(article)

        except Exception as e:
            print(f"Error searching news: {e}")

        return articles

    def _process_result(self, result: Dict, query: str) -> Optional[Dict]:
        """Process a search result into structured data"""
        try:
            title = result.get("title", "")
            body = result.get("body", "")
            url = result.get("url", "")
            source = result.get("source", "Unknown")
            date_str = result.get("date", "")

            # Parse date
            published_at = None
            if date_str:
                try:
                    published_at = datetime.fromisoformat(
                        date_str.replace("Z", "+00:00")
                    )
                except:
                    published_at = datetime.utcnow()

            # Analyze sentiment
            full_text = f"{title} {body}"
            sentiment = self.sentiment_analyzer.polarity_scores(full_text)["compound"]

            # Calculate relevance (simple keyword matching)
            query_words = query.lower().split()
            text_lower = full_text.lower()
            matches = sum(1 for word in query_words if word in text_lower)
            relevance = matches / len(query_words) if query_words else 0

            return {
                "title": title,
                "summary": body[:500] if body else "",
                "url": url,
                "source": source,
                "published_at": published_at,
                "sentiment_score": sentiment,
                "relevance_score": relevance,
                "fetched_at": datetime.utcnow(),
            }
        except Exception as e:
            print(f"Error processing result: {e}")
            return None

    def search_stock_news(
        self, ticker: str, company_name: Optional[str] = None, max_results: int = 15
    ) -> List[Dict]:
        """
        Search for stock-specific news

        Args:
            ticker: Stock ticker symbol
            company_name: Optional company name for better results
            max_results: Maximum results to return
        """
        all_articles = []

        # Build search queries
        queries = [
            f"{ticker} stock news",
            f"{ticker} stock analysis",
            f"{ticker} earnings",
        ]

        if company_name:
            queries.append(f"{company_name} stock")
            queries.append(f"{company_name} investor news")

        # Execute searches
        for query in queries:
            articles = self.search_news(
                query, max_results=max_results // 3, timelimit="w"
            )

            for article in articles:
                article["ticker"] = ticker.upper()
                article["query"] = query

                # Check if article is already in list (by URL)
                if not any(a["url"] == article["url"] for a in all_articles):
                    all_articles.append(article)

            time.sleep(0.5)  # Rate limiting

        # Sort by relevance and recency
        all_articles.sort(
            key=lambda x: (
                x.get("relevance_score", 0),
                (
                    x.get("published_at", datetime.min)
                    if x.get("published_at")
                    else datetime.min
                ),
            ),
            reverse=True,
        )

        return all_articles[:max_results]

    def search_market_news(self, max_results: int = 20) -> List[Dict]:
        """Get general market news"""
        queries = [
            "stock market news today",
            "S&P 500 market update",
            "Wall Street trading news",
        ]

        all_articles = []

        for query in queries:
            articles = self.search_news(
                query, max_results=max_results // 3, timelimit="d"
            )
            for article in articles:
                article["category"] = "market"
                if not any(a["url"] == article["url"] for a in all_articles):
                    all_articles.append(article)
            time.sleep(0.5)

        return all_articles[:max_results]

    def general_search(self, query: str, max_results: int = 10) -> List[Dict]:
        """
        Perform a general web search

        Args:
            query: Search query
            max_results: Maximum results
        """
        results = []

        try:
            with DDGS() as ddgs:
                search_results = ddgs.text(query, max_results=max_results)

                for result in search_results:
                    results.append(
                        {
                            "title": result.get("title", ""),
                            "body": result.get("body", ""),
                            "url": result.get("href", ""),
                            "fetched_at": datetime.utcnow(),
                        }
                    )

        except Exception as e:
            print(f"Error in general search: {e}")

        return results


class MockNewsSearchClient:
    """Mock news client for testing"""

    def __init__(self):
        self.sentiment_analyzer = SentimentIntensityAnalyzer()

    def search_stock_news(
        self, ticker: str, company_name: Optional[str] = None, max_results: int = 15
    ) -> List[Dict]:
        """Return mock news data"""
        mock_articles = [
            {
                "ticker": ticker,
                "title": f"{ticker} Reports Strong Q4 Earnings, Beats Expectations",
                "summary": f"{ticker} announced quarterly earnings that exceeded analyst expectations, with revenue growth of 15% year-over-year.",
                "url": f"https://example.com/news/{ticker}-earnings",
                "source": "Financial Times",
                "published_at": datetime.utcnow() - timedelta(hours=3),
                "sentiment_score": 0.75,
                "relevance_score": 0.95,
                "fetched_at": datetime.utcnow(),
            },
            {
                "ticker": ticker,
                "title": f"Analysts Upgrade {ticker} to Buy Rating",
                "summary": f"Multiple Wall Street analysts have upgraded {ticker} following positive earnings report and strong guidance.",
                "url": f"https://example.com/news/{ticker}-upgrade",
                "source": "MarketWatch",
                "published_at": datetime.utcnow() - timedelta(hours=8),
                "sentiment_score": 0.82,
                "relevance_score": 0.90,
                "fetched_at": datetime.utcnow(),
            },
            {
                "ticker": ticker,
                "title": f"{ticker} Faces Regulatory Scrutiny in Key Market",
                "summary": f"Regulators are examining {ticker}'s operations, which could impact future growth prospects.",
                "url": f"https://example.com/news/{ticker}-regulation",
                "source": "Reuters",
                "published_at": datetime.utcnow() - timedelta(hours=12),
                "sentiment_score": -0.35,
                "relevance_score": 0.85,
                "fetched_at": datetime.utcnow(),
            },
        ]
        return mock_articles[:max_results]

    def search_news(
        self, query: str, max_results: int = 20, timelimit: str = "w"
    ) -> List[Dict]:
        return self.search_stock_news("AAPL", max_results=max_results)

    def search_market_news(self, max_results: int = 20) -> List[Dict]:
        return [
            {
                "title": "S&P 500 Reaches New All-Time High",
                "summary": "Major indices continue their rally as economic data shows resilience.",
                "url": "https://example.com/market-news",
                "source": "Bloomberg",
                "category": "market",
                "published_at": datetime.utcnow() - timedelta(hours=2),
                "sentiment_score": 0.6,
                "relevance_score": 1.0,
                "fetched_at": datetime.utcnow(),
            }
        ]


import os
try:
    from googleapiclient.discovery import build as _google_build
except ImportError:
    _google_build = None


class GoogleNewsSearchClient(NewsSearchClient):
    """Search and fetch news articles using Google Custom Search API"""

    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.cse_id = os.getenv("GOOGLE_CSE_ID")
        if not self.api_key or not self.cse_id:
            raise ValueError(
                "Google API credentials missing. Set GOOGLE_API_KEY and GOOGLE_CSE_ID in .env"
            )
        if _google_build is None:
            raise ImportError("google-api-python-client is not installed. Run: pip install google-api-python-client")
        self.service = _google_build("customsearch", "v1", developerKey=self.api_key)

    def search_news(
        self, query: str, max_results: int = 10, timelimit: str = "w"
    ) -> List[Dict]:
        articles = []
        try:
            res = (
                self.service.cse()
                .list(q=query, cx=self.cse_id, num=min(max_results, 10))
                .execute()
            )

            for item in res.get("items", []):
                article = self._process_google_result(item, query)
                if article:
                    articles.append(article)
        except Exception as e:
            print(f"Error searching Google News: {e}")

        return articles

    def _process_google_result(self, item: Dict, query: str) -> Optional[Dict]:
        try:
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            url = item.get("link", "")
            source = item.get("displayLink", "Google Search")

            full_text = f"{title} {snippet}"
            sentiment = self.sentiment_analyzer.polarity_scores(full_text)["compound"]

            return {
                "title": title,
                "summary": snippet[:500] if snippet else "",
                "url": url,
                "source": source,
                "published_at": datetime.utcnow(),
                "sentiment_score": sentiment,
                "relevance_score": 0.8,
                "fetched_at": datetime.utcnow(),
            }
        except Exception as e:
            print(f"Error processing Google result: {e}")
            return None


def get_news_client():
    """Factory function to get news client"""
    try:
        client = NewsSearchClient()
        return client
    except Exception as e:
        print(f"News search not available: {e}")
        return MockNewsSearchClient()


if __name__ == "__main__":
    client = get_news_client()

    print("Searching for AAPL news...")
    articles = client.search_stock_news("AAPL", "Apple Inc", max_results=5)

    print(f"\nFound {len(articles)} articles:")
    for article in articles:
        print(f"  - {article['title'][:60]}...")
        print(
            f"    Source: {article['source']}, Sentiment: {article.get('sentiment_score', 0):.2f}"
        )
