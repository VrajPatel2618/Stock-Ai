from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
import numpy as np
import datetime

from .models import WatchlistTicker, SentimentAnalysis, ScrapedPost, NewsArticle
from .services import get_stock_data, run_forecast, calculate_ranges


# ── AUTH ──────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '')
    if not username or not password:
        return Response({'error': 'Username and password required'}, status=400)
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists'}, status=409)
    user = User.objects.create_user(username=username, password=password)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key, 'user': {'id': user.id, 'username': user.username}}, status=201)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    from django.contrib.auth import authenticate
    username = request.data.get('username', '')
    password = request.data.get('password', '')
    user = authenticate(username=username, password=password)
    if not user:
        return Response({'error': 'Invalid credentials'}, status=401)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': token.key, 'user': {'id': user.id, 'username': user.username}})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    request.user.auth_token.delete()
    return Response({'message': 'Logged out'})


# ── HEALTH ────────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    return Response({'status': 'healthy', 'timestamp': datetime.datetime.now().isoformat()})


# ── STOCK DATA ────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def stock_detail(request, ticker):
    result = get_stock_data(ticker.upper())
    if not result:
        return Response({'error': f"Ticker '{ticker}' not found"}, status=404)
    stock, df, info = result
    current_price = float(info.get('currentPrice', df['Close'].iloc[-1]))
    prev_close = float(info.get('previousClose', df['Close'].iloc[-2] if len(df) > 1 else current_price))
    change = current_price - prev_close
    return Response({
        'ticker': ticker.upper(),
        'companyName': info.get('longName', info.get('shortName', ticker.upper())),
        'currentPrice': current_price,
        'previousClose': prev_close,
        'change': change,
        'changePercent': (change / prev_close * 100) if prev_close else 0,
        'currency': info.get('currency', 'USD'),
        'marketCap': info.get('marketCap', 0),
        'peRatio': info.get('trailingPE') or 0,
        'fiftyTwoWeekHigh': info.get('fiftyTwoWeekHigh', 0),
        'fiftyTwoWeekLow': info.get('fiftyTwoWeekLow', 0),
        'volume': info.get('volume', 0),
        'beta': info.get('beta') or 0,
        'dividendYield': info.get('dividendYield') or 0,
        'sector': info.get('sector', 'Unknown'),
        'industry': info.get('industry', 'Unknown'),
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def predict(request):
    ticker = request.data.get('ticker', '').upper()
    days = request.data.get('days', 365)
    if not ticker:
        return Response({'error': 'Ticker required'}, status=400)

    result = get_stock_data(ticker)
    if not result:
        return Response({'error': f"Ticker '{ticker}' not found"}, status=404)

    stock, df, info = result
    preds, current_price = run_forecast(df, days=days)
    ranges = calculate_ranges(current_price, preds)

    year_change = ranges['yearRange']['change']
    sentiment = 'bullish' if year_change > 10 else 'bearish' if year_change < -10 else 'neutral'
    volatility = float(np.std(preds[:30]) / np.mean(preds[:30]) * 100)
    confidence = max(50, min(95, 100 - volatility * 2))

    history_df = df.tail(90)
    historical = [
        {'date': d.strftime('%Y-%m-%d'), 'open': float(r['Open']), 'high': float(r['High']),
         'low': float(r['Low']), 'close': float(r['Close']), 'volume': int(r['Volume'])}
        for d, r in history_df.iterrows()
    ]

    return Response({
        'ticker': ticker,
        'predictions': preds.tolist()[:days],
        **ranges,
        'confidence': confidence,
        'sentiment': sentiment,
        'currentPrice': current_price,
        'historicalData': historical,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def commodity_detail(request, symbol):
    result = get_stock_data(symbol.upper())
    if not result:
        return Response({'error': f"Commodity '{symbol}' not found"}, status=404)
    stock, df, info = result
    current_price = float(info.get('currentPrice', df['Close'].iloc[-1]))
    prev_close = float(df['Close'].iloc[-2] if len(df) > 1 else current_price)
    change = current_price - prev_close
    return Response({
        'symbol': symbol.upper(),
        'name': info.get('longName', info.get('shortName', symbol.upper())),
        'currentPrice': current_price,
        'change': change,
        'changePercent': (change / prev_close * 100) if prev_close else 0,
        'currency': info.get('currency', 'USD'),
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def commodity_predict(request):
    symbol = request.data.get('symbol', '').upper()
    if not symbol:
        return Response({'error': 'Symbol required'}, status=400)
    result = get_stock_data(symbol)
    if not result:
        return Response({'error': f"Commodity '{symbol}' not found"}, status=404)
    stock, df, info = result
    preds, current_price = run_forecast(df, days=30)
    ranges = calculate_ranges(current_price, preds)
    history_df = df.tail(90)
    historical = [
        {'date': d.strftime('%Y-%m-%d'), 'open': float(r['Open']), 'high': float(r['High']),
         'low': float(r['Low']), 'close': float(r['Close'])}
        for d, r in history_df.iterrows()
    ]
    return Response({
        'symbol': symbol, 'currentPrice': current_price,
        'prediction30Day': float(preds[29]) if len(preds) > 29 else float(preds[-1]),
        'predictions': preds.tolist(), 'ranges': ranges, 'historicalData': historical,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def market_overview(request):
    indices = [
        ('^GSPC', 'S&P 500'), ('^IXIC', 'NASDAQ'), ('^DJI', 'Dow Jones'),
        ('BTC-USD', 'Bitcoin'), ('ETH-USD', 'Ethereum'),
    ]
    results = []
    for symbol, name in indices:
        try:
            result = get_stock_data(symbol)
            if result:
                _, df, info = result
                price = float(info.get('currentPrice', df['Close'].iloc[-1]))
                prev = float(df['Close'].iloc[-2] if len(df) > 1 else price)
                chg = (price - prev) / prev * 100 if prev else 0
                results.append({'symbol': symbol, 'name': name, 'price': price,
                                 'changePercent': chg, 'isPositive': chg >= 0})
        except Exception:
            pass
    return Response({'indices': results})


@api_view(['POST'])
@permission_classes([AllowAny])
def watchlist_prices(request):
    tickers = request.data.get('tickers', [])
    results = []
    for ticker in tickers:
        try:
            result = get_stock_data(ticker.upper())
            if result:
                _, df, info = result
                price = float(info.get('currentPrice', df['Close'].iloc[-1]))
                prev = float(info.get('previousClose', df['Close'].iloc[-2] if len(df) > 1 else price))
                change = price - prev
                chg_pct = (change / prev * 100) if prev else 0
                results.append({'ticker': ticker.upper(), 'price': price,
                                 'change': change, 'changePercent': chg_pct, 'isPositive': chg_pct >= 0})
        except Exception:
            pass
    return Response({'prices': results})


# ── WATCHLIST (auth required) ─────────────────────────────────────────────────

@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def watchlist(request):
    if request.method == 'GET':
        items = WatchlistTicker.objects.filter(user=request.user)
        return Response({'watchlist': [i.to_dict() for i in items]})

    ticker = request.data.get('ticker', '').upper()
    if not ticker:
        return Response({'error': 'Ticker required'}, status=400)

    if request.method == 'POST':
        obj, created = WatchlistTicker.objects.get_or_create(user=request.user, ticker=ticker)
        return Response({'message': f'{ticker} added to watchlist'}, status=201 if created else 200)

    if request.method == 'DELETE':
        WatchlistTicker.objects.filter(user=request.user, ticker=ticker).delete()
        return Response({'message': f'{ticker} removed from watchlist'})


# ── SENTIMENT & SOCIAL ────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def sentiment(request, ticker):
    ticker = ticker.upper()
    try:
        from scrapers.reddit_scraper import get_reddit_scraper
        from scrapers.forum_scraper import get_forum_scraper
        from scrapers.news_scraper import get_news_client
        from ai.sentiment_analyzer import get_sentiment_analyzer

        reddit_scraper = get_reddit_scraper()
        forum_scraper = get_forum_scraper()
        news_client = get_news_client()
        analyzer = get_sentiment_analyzer()

        reddit_posts = reddit_scraper.fetch_ticker_posts(ticker, limit=30)
        st_posts = forum_scraper.fetch_stocktwits(ticker, limit=30)
        news = news_client.search_stock_news(ticker, max_results=10)

        r_agg = analyzer.aggregate_sentiment(reddit_posts, sentiment_key='sentiment_score', weight_key='engagement_score')
        s_agg = analyzer.aggregate_sentiment(st_posts, sentiment_key='sentiment_score')
        n_agg = analyzer.aggregate_sentiment(news, sentiment_key='sentiment_score')

        total = r_agg['total_count'] + s_agg['total_count'] + n_agg['total_count']
        combined = (r_agg['weighted_sentiment'] * 0.4 + s_agg['avg_sentiment'] * 0.3 + n_agg['avg_sentiment'] * 0.3) if total > 0 else 0
        label = 'bullish' if combined > 0.3 else 'bearish' if combined < -0.3 else 'neutral'

        return Response({
            'ticker': ticker,
            'sentiment': {'overall': label, 'score': round(combined, 3),
                          'confidence': min(95, 50 + total * 2)},
            'sources': {
                'reddit': {'count': r_agg['total_count'], 'sentiment': round(r_agg['weighted_sentiment'], 3),
                           'bullish_pct': r_agg['bullish_pct'], 'bearish_pct': r_agg['bearish_pct']},
                'stocktwits': {'count': s_agg['total_count'], 'sentiment': round(s_agg['avg_sentiment'], 3),
                               'bullish_pct': s_agg['bullish_pct']},
                'news': {'count': n_agg['total_count'], 'sentiment': round(n_agg['avg_sentiment'], 3)},
            },
            'timestamp': datetime.datetime.now().isoformat(),
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def social_posts(request, ticker):
    ticker = ticker.upper()
    limit = int(request.query_params.get('limit', 20))
    source = request.query_params.get('source', 'all')
    try:
        from scrapers.reddit_scraper import get_reddit_scraper
        from scrapers.forum_scraper import get_forum_scraper

        posts = []
        if source in ['all', 'reddit']:
            scraper = get_reddit_scraper()
            for p in scraper.fetch_ticker_posts(ticker, limit=limit):
                posts.append({'id': p.get('id'), 'source': 'reddit', 'subreddit': p.get('subreddit'),
                               'title': p.get('title'), 'content': p.get('content', '')[:300],
                               'author': p.get('author'), 'url': p.get('url'),
                               'sentiment': p.get('sentiment_score'), 'engagement': p.get('engagement_score'),
                               'created_at': p.get('created_at').isoformat() if p.get('created_at') else None})
        if source in ['all', 'stocktwits']:
            scraper = get_forum_scraper()
            for p in scraper.fetch_stocktwits(ticker, limit=limit):
                posts.append({'id': p.get('id'), 'source': 'stocktwits',
                               'content': p.get('content', '')[:300], 'author': p.get('author'),
                               'url': p.get('url'), 'sentiment': p.get('sentiment_score'),
                               'engagement': p.get('engagement_score'),
                               'created_at': p.get('created_at').isoformat() if p.get('created_at') else None})
        posts.sort(key=lambda x: x.get('engagement') or 0, reverse=True)
        return Response({'ticker': ticker, 'posts': posts[:limit], 'total': len(posts),
                         'timestamp': datetime.datetime.now().isoformat()})
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def news(request, ticker):
    ticker = ticker.upper()
    limit = int(request.query_params.get('limit', 15))
    try:
        from scrapers.news_scraper import get_news_client
        client = get_news_client()
        articles = client.search_stock_news(ticker, max_results=limit)
        def safe_dt(val):
            if val is None: return None
            if hasattr(val, 'isoformat'): return val.isoformat()
            return str(val)
        return Response({
            'ticker': ticker,
            'articles': [{
                'title': a.get('title'),
                'summary': a.get('summary', '')[:500],
                'url': a.get('url'),
                'source': a.get('source'),
                'sentiment': round(float(a.get('sentiment_score') or 0), 3),
                'published_at': safe_dt(a.get('published_at')),
            } for a in articles],
            'total': len(articles),
            'timestamp': datetime.datetime.now().isoformat(),
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def chat(request):
    message = request.data.get('message', '')
    ticker = request.data.get('ticker', '')
    if not message:
        return Response({'error': 'Message required'}, status=400)
    try:
        from ai.ollama_client import get_ollama_analyzer
        analyzer = get_ollama_analyzer()
        context = f"ticker: {ticker.upper()}" if ticker else None
        reply = analyzer.chat(message, context=context)
        return Response({
            'response': reply,
            'model_used': analyzer.model,
            'ollama_available': analyzer.is_available(),
            'timestamp': datetime.datetime.now().isoformat(),
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def analyze_ticker(request, ticker):
    ticker = ticker.upper()
    try:
        from scrapers.reddit_scraper import get_reddit_scraper
        from scrapers.forum_scraper import get_forum_scraper
        from scrapers.news_scraper import get_news_client
        from ai.intelligence_aggregator import get_intelligence_aggregator

        aggregator = get_intelligence_aggregator()
        reddit_posts = get_reddit_scraper().fetch_ticker_posts(ticker, limit=30)
        st_posts = get_forum_scraper().fetch_stocktwits(ticker, limit=30)
        news_articles = get_news_client().search_stock_news(ticker, max_results=15)
        market_data = aggregator.get_market_data(ticker)

        analysis = aggregator.generate_full_analysis(
            ticker=ticker, reddit_posts=reddit_posts,
            stocktwits_posts=st_posts, news_articles=news_articles, market_data=market_data
        )

        ai = analysis.get('ai_analysis', {})
        SentimentAnalysis.objects.create(
            ticker=ticker,
            overall_sentiment=ai.get('overall_sentiment', 'neutral'),
            confidence_score=ai.get('confidence', 50),
            reasoning=ai.get('short_term_outlook', ''),
            key_points=ai.get('key_reasoning', []),
            risk_factors=ai.get('risk_factors', []),
            predicted_trend=ai.get('predicted_trend', ''),
            recommendation=ai.get('recommendation', ''),
            reddit_posts_count=len(reddit_posts),
            news_articles_count=len(news_articles),
        )
        return Response(analysis)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
