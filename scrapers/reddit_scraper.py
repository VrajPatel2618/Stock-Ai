"""
Reddit Scraper Module - No API Required
Scrapes stock discussions from Reddit using public JSON endpoints
"""

import requests
from bs4 import BeautifulSoup
import re
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import random


class RedditScraper:
    """Scrapes stock-related posts from Reddit without API keys"""

    # Subreddits to monitor for stock discussions
    SUBREDDITS = [
        "wallstreetbets",
        "stocks",
        "investing",
        "stockmarket",
        "options",
        "ValueInvesting",
        "dividends",
    ]

    # Reddit JSON endpoint (no auth required)
    REDDIT_BASE_URL = "https://www.reddit.com"

    # Regex pattern to find stock tickers (e.g., $AAPL, AAPL)
    TICKER_PATTERN = re.compile(r"\$([A-Z]{1,5})\b|\b([A-Z]{2,5})\b")

    # Common words to exclude from ticker detection
    EXCLUDED_WORDS = {
        "I",
        "A",
        "THE",
        "AND",
        "OR",
        "BUT",
        "FOR",
        "TO",
        "IN",
        "ON",
        "AT",
        "IT",
        "IS",
        "BE",
        "AS",
        "ARE",
        "WAS",
        "NOT",
        "ALL",
        "CAN",
        "HAS",
        "IF",
        "SO",
        "UP",
        "OUT",
        "NEW",
        "NOW",
        "JUST",
        "MORE",
        "SOME",
        "VERY",
        "WHEN",
        "WHO",
        "HOW",
        "ANY",
        "MY",
        "WE",
        "YOU",
        "HE",
        "SHE",
        "THEY",
        "THIS",
        "THAT",
        "WITH",
        "FROM",
        "HAVE",
        "BEEN",
        "WHAT",
        "WILL",
        "DD",
        "OP",
        "IMO",
        "TL",
        "DR",
        "TLDR",
        "CEO",
        "CFO",
        "IPO",
        "ETF",
        "USD",
        "USA",
        "UK",
        "EU",
        "THE",
        "AN",
        "OF",
        "BY",
        "AT",
        "EPS",
        "PE",
        "EDIT",
        "UPDATE",
        "YOLO",
        "FYI",
        "LOL",
        "LMAO",
        "HOLY",
        "WOW",
        "OMG",
        "PM",
        "AM",
        "US",
        "GDP",
        "SEC",
        "FDA",
        "WSB",
        "NYSE",
        "NASDAQ",
        "BUY",
        "SELL",
        "HOLD",
        "CALL",
        "PUT",
        "OTM",
        "ITM",
        "ATM",
        "DTE",
        "ATH",
        "EOD",
        "AH",
        "PM",
        "RH",
        "TD",
        "FOMO",
        "FUD",
        "HODL",
        "MOON",
    }

    # User agents to rotate
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]

    def __init__(self):
        """Initialize Reddit scraper"""
        self.session = requests.Session()
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        self._update_headers()

    def _update_headers(self):
        """Update session headers with random user agent"""
        self.session.headers.update(
            {
                "User-Agent": random.choice(self.USER_AGENTS),
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.9",
            }
        )

    def is_available(self) -> bool:
        """Always available since no API key needed"""
        return True

    def extract_tickers(self, text: str) -> List[str]:
        """Extract stock tickers from text"""
        if not text:
            return []

        # Find all potential tickers
        matches = self.TICKER_PATTERN.findall(text.upper())

        # Flatten matches (each match is a tuple from alternation)
        tickers = []
        for match in matches:
            ticker = match[0] if match[0] else match[1]
            if ticker and ticker not in self.EXCLUDED_WORDS and len(ticker) >= 2:
                tickers.append(ticker)

        return list(set(tickers))  # Remove duplicates

    def analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment of text using VADER"""
        if not text:
            return 0.0

        scores = self.sentiment_analyzer.polarity_scores(text)
        return scores["compound"]  # -1 to 1

    def _fetch_subreddit_json(
        self, subreddit: str, sort: str = "hot", limit: int = 25, after: str = None
    ) -> Optional[Dict]:
        """Fetch subreddit data using Reddit's JSON API (old.reddit.com is more permissive)"""
        try:
            # Use old.reddit.com which is less restrictive
            url = f"https://old.reddit.com/r/{subreddit}/{sort}.json"
            params = {"limit": limit, "raw_json": 1}
            if after:
                params["after"] = after

            # Update headers to look like a real browser
            headers = {
                "User-Agent": random.choice(self.USER_AGENTS),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Cache-Control": "max-age=0",
            }

            response = requests.get(url, params=params, headers=headers, timeout=15)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                print(f"Rate limited on r/{subreddit}, waiting...")
                time.sleep(5)
                return None
            elif response.status_code == 403:
                # Try alternative approach - scrape HTML
                return self._scrape_subreddit_html(subreddit, limit)
            else:
                print(f"Error fetching r/{subreddit}: Status {response.status_code}")
                return None

        except Exception as e:
            print(f"Error fetching r/{subreddit}: {e}")
            return None

    def _scrape_subreddit_html(self, subreddit: str, limit: int = 25) -> Optional[Dict]:
        """Fallback: Scrape Reddit HTML if JSON endpoint fails"""
        try:
            from bs4 import BeautifulSoup

            url = f"https://old.reddit.com/r/{subreddit}"
            headers = {
                "User-Agent": random.choice(self.USER_AGENTS),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }

            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.content, "lxml")
            posts = []

            # Find all posts on old reddit
            for thing in soup.find_all("div", {"class": "thing", "data-type": "link"})[
                :limit
            ]:
                try:
                    data = {
                        "id": thing.get("data-fullname", "").replace("t3_", ""),
                        "title": (
                            thing.find("a", {"class": "title"}).get_text()
                            if thing.find("a", {"class": "title"})
                            else ""
                        ),
                        "author": thing.get("data-author", "deleted"),
                        "score": int(thing.get("data-score", 0)),
                        "num_comments": 0,
                        "permalink": thing.get("data-permalink", ""),
                        "selftext": "",
                        "created_utc": time.time(),  # Approximate
                    }

                    # Try to get comment count
                    comments_elem = thing.find("a", {"class": "comments"})
                    if comments_elem:
                        comments_text = comments_elem.get_text()
                        import re

                        match = re.search(r"(\d+)", comments_text)
                        if match:
                            data["num_comments"] = int(match.group(1))

                    posts.append({"kind": "t3", "data": data})

                except Exception as e:
                    continue

            return {"data": {"children": posts}} if posts else None

        except Exception as e:
            print(f"HTML scrape failed for r/{subreddit}: {e}")
            return None

    def _search_subreddit_json(
        self, subreddit: str, query: str, limit: int = 25
    ) -> Optional[Dict]:
        """Search a subreddit using Reddit's JSON API"""
        try:
            url = f"{self.REDDIT_BASE_URL}/r/{subreddit}/search.json"
            params = {
                "q": query,
                "restrict_sr": "true",
                "sort": "relevance",
                "t": "week",
                "limit": limit,
                "raw_json": 1,
            }

            self._update_headers()
            response = self.session.get(url, params=params, timeout=15)

            if response.status_code == 200:
                return response.json()
            else:
                return None

        except Exception as e:
            print(f"Error searching r/{subreddit}: {e}")
            return None

    def _process_post(self, post_data: Dict, subreddit: str) -> Optional[Dict]:
        """Process a Reddit post from JSON data"""
        try:
            data = post_data.get("data", {})

            title = data.get("title", "")
            selftext = data.get("selftext", "")
            full_text = f"{title} {selftext}"

            # Extract tickers
            tickers = self.extract_tickers(full_text)

            # Calculate sentiment
            sentiment = self.analyze_sentiment(full_text)

            # Calculate engagement score
            score = data.get("score", 0)
            num_comments = data.get("num_comments", 0)
            engagement = score + (num_comments * 2)

            # Get creation time
            created_utc = data.get("created_utc", 0)
            created_at = (
                datetime.utcfromtimestamp(created_utc)
                if created_utc
                else datetime.utcnow()
            )

            return {
                "id": data.get("id", ""),
                "source": "reddit",
                "subreddit": subreddit,
                "title": title[:500],
                "content": selftext[:2000] if selftext else title,
                "author": data.get("author", "deleted"),
                "url": f"https://reddit.com{data.get('permalink', '')}",
                "tickers": tickers,
                "engagement_score": engagement,
                "sentiment_score": sentiment,
                "upvotes": score,
                "comments": num_comments,
                "created_at": created_at,
            }
        except Exception as e:
            print(f"Error processing post: {e}")
            return None

    def fetch_subreddit_posts(
        self, subreddit_name: str, limit: int = 25, sort: str = "hot"
    ) -> List[Dict]:
        """Fetch posts from a subreddit"""
        posts = []

        # Fetch main listing
        data = self._fetch_subreddit_json(subreddit_name, sort=sort, limit=limit)

        if data and "data" in data and "children" in data["data"]:
            for child in data["data"]["children"]:
                if child.get("kind") == "t3":  # t3 = link/post
                    post = self._process_post(child, subreddit_name)
                    if post:
                        posts.append(post)

        return posts

    def fetch_ticker_posts(self, ticker: str, limit: int = 50) -> List[Dict]:
        """Fetch posts mentioning a specific ticker"""
        posts = []
        ticker = ticker.upper()

        # Search queries
        queries = [f"${ticker}", ticker]

        for query in queries:
            for subreddit in self.SUBREDDITS[:4]:  # Top 4 subreddits
                try:
                    data = self._search_subreddit_json(subreddit, query, limit=15)

                    if data and "data" in data and "children" in data["data"]:
                        for child in data["data"]["children"]:
                            if child.get("kind") == "t3":
                                post = self._process_post(child, subreddit)
                                if post and ticker in post["tickers"]:
                                    # Check if not already added
                                    if not any(p["id"] == post["id"] for p in posts):
                                        posts.append(post)

                    time.sleep(1)  # Be nice to Reddit

                except Exception as e:
                    print(f"Error searching {subreddit} for {query}: {e}")
                    continue

        # Sort by engagement
        posts.sort(key=lambda x: x.get("engagement_score", 0), reverse=True)

        return posts[:limit]

    def scrape_all_subreddits(self, limit_per_sub: int = 20) -> List[Dict]:
        """Scrape all monitored subreddits"""
        all_posts = []

        for subreddit in self.SUBREDDITS:
            print(f"Scraping r/{subreddit}...")

            # Get hot posts
            hot_posts = self.fetch_subreddit_posts(
                subreddit, limit=limit_per_sub, sort="hot"
            )
            all_posts.extend(hot_posts)

            # Get new posts
            new_posts = self.fetch_subreddit_posts(
                subreddit, limit=limit_per_sub // 2, sort="new"
            )
            for post in new_posts:
                if not any(p["id"] == post["id"] for p in all_posts):
                    all_posts.append(post)

            time.sleep(2)  # Rate limiting

        # Filter to only posts with tickers
        all_posts = [p for p in all_posts if p.get("tickers")]

        print(f"Total posts scraped: {len(all_posts)}")
        return all_posts

    def get_trending_tickers(self, hours: int = 24) -> Dict[str, Dict]:
        """Get trending tickers based on mention frequency"""
        posts = self.scrape_all_subreddits(limit_per_sub=30)

        ticker_stats = {}
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        for post in posts:
            if post["created_at"] >= cutoff:
                for ticker in post["tickers"]:
                    if ticker not in ticker_stats:
                        ticker_stats[ticker] = {
                            "mentions": 0,
                            "total_engagement": 0,
                            "sentiments": [],
                            "posts": [],
                        }

                    ticker_stats[ticker]["mentions"] += 1
                    ticker_stats[ticker]["total_engagement"] += post["engagement_score"]
                    ticker_stats[ticker]["sentiments"].append(post["sentiment_score"])
                    ticker_stats[ticker]["posts"].append(post)

        # Calculate average sentiment
        for ticker, stats in ticker_stats.items():
            if stats["sentiments"]:
                stats["avg_sentiment"] = sum(stats["sentiments"]) / len(
                    stats["sentiments"]
                )
            else:
                stats["avg_sentiment"] = 0

        # Sort by mentions
        trending = dict(
            sorted(ticker_stats.items(), key=lambda x: x[1]["mentions"], reverse=True)
        )

        return trending


class MockRedditScraper:
    """Mock Reddit scraper for testing when scraping fails"""

    def __init__(self):
        self.sentiment_analyzer = SentimentIntensityAnalyzer()

    def is_available(self) -> bool:
        return True

    def fetch_ticker_posts(self, ticker: str, limit: int = 50) -> List[Dict]:
        """Return mock data for testing"""
        mock_posts = [
            {
                "id": f"mock_{ticker}_1",
                "source": "reddit",
                "subreddit": "wallstreetbets",
                "title": f"{ticker} looking bullish! Great earnings beat 🚀",
                "content": f"{ticker} just crushed earnings expectations. Revenue up 20%. This is going to moon!",
                "author": "diamond_hands_trader",
                "url": f"https://reddit.com/r/wallstreetbets/mock_{ticker}",
                "tickers": [ticker],
                "engagement_score": 1500,
                "sentiment_score": 0.85,
                "upvotes": 1200,
                "comments": 300,
                "created_at": datetime.utcnow() - timedelta(hours=2),
            },
            {
                "id": f"mock_{ticker}_2",
                "source": "reddit",
                "subreddit": "stocks",
                "title": f"DD on {ticker} - Why I think it's undervalued",
                "content": f"Did deep research on {ticker}. P/E ratio suggests undervaluation compared to sector. Long term hold.",
                "author": "value_investor_99",
                "url": f"https://reddit.com/r/stocks/mock_{ticker}",
                "tickers": [ticker],
                "engagement_score": 800,
                "sentiment_score": 0.65,
                "upvotes": 600,
                "comments": 200,
                "created_at": datetime.utcnow() - timedelta(hours=5),
            },
            {
                "id": f"mock_{ticker}_3",
                "source": "reddit",
                "subreddit": "investing",
                "title": f"Concerns about {ticker} valuation",
                "content": f"While {ticker} has potential, current valuation seems stretched. Proceed with caution.",
                "author": "cautious_carl",
                "url": f"https://reddit.com/r/investing/mock_{ticker}",
                "tickers": [ticker],
                "engagement_score": 400,
                "sentiment_score": -0.2,
                "upvotes": 300,
                "comments": 100,
                "created_at": datetime.utcnow() - timedelta(hours=8),
            },
            {
                "id": f"mock_{ticker}_4",
                "source": "reddit",
                "subreddit": "wallstreetbets",
                "title": f"{ticker} technical analysis - breakout incoming?",
                "content": f"Looking at the charts, {ticker} is forming a bullish flag pattern. Could see 10% move soon.",
                "author": "chart_master",
                "url": f"https://reddit.com/r/wallstreetbets/mock_{ticker}_4",
                "tickers": [ticker],
                "engagement_score": 650,
                "sentiment_score": 0.55,
                "upvotes": 500,
                "comments": 150,
                "created_at": datetime.utcnow() - timedelta(hours=12),
            },
        ]
        return mock_posts[:limit]

    def scrape_all_subreddits(self, limit_per_sub: int = 20) -> List[Dict]:
        """Return mock data"""
        return self.fetch_ticker_posts("AAPL", limit=limit_per_sub)

    def fetch_subreddit_posts(
        self, subreddit_name: str, limit: int = 25, sort: str = "hot"
    ) -> List[Dict]:
        return self.fetch_ticker_posts("AAPL", limit=limit)


def get_reddit_scraper():
    """Factory function to get appropriate scraper"""
    scraper = RedditScraper()

    # Test if we can connect
    try:
        # Quick test fetch
        test_data = scraper._fetch_subreddit_json("stocks", limit=1)
        if test_data:
            print("Reddit scraper initialized (no API key required)")
            return scraper
    except Exception as e:
        print(f"Reddit scraper test failed: {e}")

    print("Using mock Reddit scraper")
    return MockRedditScraper()


if __name__ == "__main__":
    # Test the scraper
    scraper = get_reddit_scraper()
    print(f"Scraper available: {scraper.is_available()}")

    print("\nFetching posts for AAPL...")
    posts = scraper.fetch_ticker_posts("AAPL", limit=10)

    print(f"\nFound {len(posts)} posts:")
    for post in posts[:5]:
        print(f"  - [{post['subreddit']}] {post['title'][:60]}...")
        print(
            f"    Sentiment: {post['sentiment_score']:.2f}, Engagement: {post['engagement_score']}"
        )
