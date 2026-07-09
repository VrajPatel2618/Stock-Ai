from django.db import models
from django.contrib.auth.models import User


class WatchlistTicker(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlist')
    ticker = models.CharField(max_length=10)
    added_at = models.DateTimeField(auto_now_add=True)
    last_analyzed = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'ticker')

    def to_dict(self):
        return {
            'id': self.id,
            'ticker': self.ticker,
            'added_at': self.added_at.isoformat(),
            'last_analyzed': self.last_analyzed.isoformat() if self.last_analyzed else None,
        }


class PortfolioHolding(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portfolio')
    ticker = models.CharField(max_length=20)
    shares = models.FloatField()
    avg_price = models.FloatField()
    currency = models.CharField(max_length=5, default='USD')
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'ticker')

    def to_dict(self):
        return {
            'id': self.id,
            'ticker': self.ticker,
            'shares': self.shares,
            'avg_price': self.avg_price,
            'currency': self.currency,
            'added_at': self.added_at.isoformat(),
        }


class ScrapedPost(models.Model):
    SOURCE_CHOICES = [('reddit', 'Reddit'), ('stocktwits', 'StockTwits')]
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES)
    ticker = models.CharField(max_length=10, db_index=True)
    title = models.CharField(max_length=500, blank=True)
    content = models.TextField()
    author = models.CharField(max_length=100, blank=True)
    url = models.URLField(max_length=500, blank=True)
    engagement_score = models.FloatField(default=0)
    sentiment_score = models.FloatField(null=True, blank=True)
    subreddit = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField()
    scraped_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['ticker', 'created_at'])]

    def to_dict(self):
        return {
            'id': self.id, 'source': self.source, 'ticker': self.ticker,
            'title': self.title, 'content': self.content[:500],
            'author': self.author, 'url': self.url,
            'engagement_score': self.engagement_score,
            'sentiment_score': self.sentiment_score,
            'subreddit': self.subreddit,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class NewsArticle(models.Model):
    ticker = models.CharField(max_length=10, db_index=True)
    title = models.CharField(max_length=500)
    summary = models.TextField(blank=True)
    url = models.URLField(max_length=500, unique=True)
    source = models.CharField(max_length=100, blank=True)
    sentiment_score = models.FloatField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['ticker', 'published_at'])]

    def to_dict(self):
        return {
            'id': self.id, 'ticker': self.ticker, 'title': self.title,
            'summary': self.summary, 'url': self.url, 'source': self.source,
            'sentiment_score': self.sentiment_score,
            'published_at': self.published_at.isoformat() if self.published_at else None,
        }


class SentimentAnalysis(models.Model):
    SENTIMENT_CHOICES = [('bullish', 'Bullish'), ('bearish', 'Bearish'), ('neutral', 'Neutral')]
    ticker = models.CharField(max_length=10, db_index=True)
    overall_sentiment = models.CharField(max_length=20, choices=SENTIMENT_CHOICES)
    confidence_score = models.FloatField()
    reasoning = models.TextField(blank=True)
    key_points = models.JSONField(default=list)
    risk_factors = models.JSONField(default=list)
    predicted_trend = models.CharField(max_length=20, blank=True)
    recommendation = models.CharField(max_length=20, blank=True)
    reddit_posts_count = models.IntegerField(default=0)
    news_articles_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['ticker', 'created_at'])]

    def to_dict(self):
        return {
            'id': self.id, 'ticker': self.ticker,
            'overall_sentiment': self.overall_sentiment,
            'confidence_score': self.confidence_score,
            'reasoning': self.reasoning,
            'key_points': self.key_points,
            'risk_factors': self.risk_factors,
            'predicted_trend': self.predicted_trend,
            'recommendation': self.recommendation,
            'reddit_posts_count': self.reddit_posts_count,
            'news_articles_count': self.news_articles_count,
            'created_at': self.created_at.isoformat(),
        }

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    virtual_balance = models.FloatField(default=100000.0)  # Start with $100k
    
    def to_dict(self):
        return {
            'virtual_balance': self.virtual_balance
        }

class TradeHistory(models.Model):
    TRADE_CHOICES = [('BUY', 'Buy'), ('SELL', 'Sell')]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trades')
    ticker = models.CharField(max_length=20)
    action = models.CharField(max_length=4, choices=TRADE_CHOICES)
    shares = models.FloatField()
    price = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'ticker': self.ticker,
            'action': self.action,
            'shares': self.shares,
            'price': self.price,
            'total': self.shares * self.price,
            'timestamp': self.timestamp.isoformat()
        }
