import datetime
import random


class SocialMediaScraper:
    """
    Simulates fetching real-time data from social media networks
    like Twitter, Instagram, and TikTok for a given ticker,
    as official APIs typically require paid enterprise developer keys.
    """

    def __init__(self):
        self.sources = ["Twitter", "Instagram", "TikTok"]

    def fetch_recent_mentions(self, ticker, limit=15):
        """Simulates fetching recent mentions of a stock ticker"""
        posts = []
        base_time = datetime.datetime.now()

        bullish_keywords = [
            "moon",
            "buy",
            "undervalued",
            "calls",
            "breakout",
            "bull",
            "growth",
        ]
        bearish_keywords = [
            "puts",
            "crash",
            "sell",
            "overvalued",
            "drop",
            "bear",
            "short",
        ]
        neutral_keywords = ["holding", "earnings", "volume", "trading", "watching"]

        for i in range(limit):
            source = random.choice(self.sources)
            time_offset = datetime.timedelta(minutes=random.randint(1, 120))

            # Randomly generate sentiment inclination
            sentiment_type = random.choice(["bullish", "bearish", "neutral", "bullish"])

            if sentiment_type == "bullish":
                words = random.sample(bullish_keywords, 2)
                content = f"Looking at {ticker} today! Definitely feeling like a {words[0]} coming. Time to {words[1]} 🚀"
                score = random.uniform(0.3, 0.9)
            elif sentiment_type == "bearish":
                words = random.sample(bearish_keywords, 2)
                content = f"{ticker} is looking weak. Might {words[0]} soon. Watch out for a {words[1]} 📉"
                score = random.uniform(-0.9, -0.3)
            else:
                words = random.sample(neutral_keywords, 2)
                content = f"Just {words[0]} {ticker} right now. Waiting on {words[1]}."
                score = random.uniform(-0.2, 0.2)

            posts.append(
                {
                    "id": f"{source.lower()}_{random.randint(10000, 99999)}",
                    "source": source,
                    "content": content,
                    "author": f"user_{random.randint(100, 999)}",
                    "url": f"https://{source.lower()}.com/post/{random.randint(10000, 99999)}",
                    "sentiment_score": score,
                    "engagement_score": random.randint(10, 5000),
                    "created_at": base_time - time_offset,
                }
            )

        return posts


def get_social_scraper():
    return SocialMediaScraper()
