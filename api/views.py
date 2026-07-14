from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
import numpy as np
import datetime

from .models import WatchlistTicker, SentimentAnalysis, ScrapedPost, NewsArticle, PortfolioHolding
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
    preds, current_price, feature_importance = run_forecast(df, days=days)
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
        'ticker': ticker, 'predictions': preds.tolist()[:days],
        **ranges, 'confidence': confidence, 'sentiment': sentiment,
        'currentPrice': current_price, 'historicalData': historical,
        'featureImportance': feature_importance,
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def backtest(request):
    ticker = request.data.get('ticker', '').upper()
    if not ticker:
        return Response({'error': 'Ticker required'}, status=400)
    
    result = get_stock_data(ticker)
    if not result:
        return Response({'error': f"Ticker '{ticker}' not found"}, status=404)
    
    stock, df, info = result
    
    try:
        from .services import run_backtest
        backtest_result = run_backtest(df, days_back=30, forecast_window=30)
        
        if not backtest_result:
            return Response({'error': 'Not enough historical data for backtesting (requires at least ~560 days).'}, status=400)
            
        return Response({
            'ticker': ticker,
            **backtest_result
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return Response({'error': str(e)}, status=500)



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
        'currentPrice': current_price, 'change': change,
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
    preds, current_price, _ = run_forecast(df, days=30)
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


# ── WATCHLIST ─────────────────────────────────────────────────────────────────

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


# ── PORTFOLIO ─────────────────────────────────────────────────────────────────
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from .models import UserProfile, TradeHistory

# A generic placeholder for the Google Client ID
GOOGLE_CLIENT_ID = "889565597256-ja3mm4qn1hje2f2ojekfa6eqmjivhtfp.apps.googleusercontent.com"

@api_view(['POST'])
@permission_classes([AllowAny])
def google_auth(request):
    token = request.data.get('token')
    if not token:
        return Response({'error': 'Token required'}, status=400)
    
    import requests
    try:
        # Verify the access token with Google UserInfo API
        response = requests.get(
            'https://www.googleapis.com/oauth2/v3/userinfo',
            headers={'Authorization': f'Bearer {token}'}
        )
        if response.status_code != 200:
            print(f"Google userinfo failed: {response.text}")
            return Response({'error': 'Invalid Google token'}, status=401)
            
        idinfo = response.json()
        email = idinfo.get('email')
        if not email:
            return Response({'error': 'No email provided by Google'}, status=400)
            
        first_name = idinfo.get('given_name', '')
        last_name = idinfo.get('family_name', '')
        
        # Find or create user
        user, created = User.objects.get_or_create(username=email, defaults={
            'email': email,
            'first_name': first_name,
            'last_name': last_name
        })
        
        # Ensure user profile exists for paper trading
        UserProfile.objects.get_or_create(user=user)
        
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user': {'username': user.username, 'email': user.email}})
        
    except Exception as e:
        print(f"Google token verification failed: {e}")
        return Response({'error': 'Invalid Google token'}, status=401)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trade(request):
    ticker = request.data.get('ticker', '').upper()
    action = request.data.get('action', '').upper()  # BUY or SELL
    shares = float(request.data.get('shares', 0))
    price = float(request.data.get('price', 0))
    
    if not ticker or not action or shares <= 0 or price <= 0:
        return Response({'error': 'Invalid trade parameters'}, status=400)
        
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)
    total_cost = shares * price
    
    if action == 'BUY':
        if profile.virtual_balance < total_cost:
            return Response({'error': 'Insufficient virtual funds'}, status=400)
            
        # Deduct balance
        profile.virtual_balance -= total_cost
        profile.save()
        
        # Update holding
        holding, created = PortfolioHolding.objects.get_or_create(
            user=user, ticker=ticker,
            defaults={'shares': 0, 'avg_price': 0}
        )
        # Calculate new average price
        old_total = holding.shares * holding.avg_price
        holding.shares += shares
        holding.avg_price = (old_total + total_cost) / holding.shares
        holding.save()
        
    elif action == 'SELL':
        try:
            holding = PortfolioHolding.objects.get(user=user, ticker=ticker)
            if holding.shares < shares:
                return Response({'error': 'Insufficient shares to sell'}, status=400)
                
            # Add to balance
            profile.virtual_balance += total_cost
            profile.save()
            
            # Update holding
            holding.shares -= shares
            if holding.shares == 0:
                holding.delete()
            else:
                holding.save()
        except PortfolioHolding.DoesNotExist:
            return Response({'error': 'You do not own this stock'}, status=400)
    else:
        return Response({'error': 'Invalid action'}, status=400)
        
    # Log trade
    trade = TradeHistory.objects.create(
        user=user, ticker=ticker, action=action,
        shares=shares, price=price
    )
    
    return Response({
        'message': f'Successfully {action}ed {shares} shares of {ticker}',
        'new_balance': profile.virtual_balance
    })

@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def portfolio(request):
    if request.method == 'GET':
        holdings = PortfolioHolding.objects.filter(user=request.user)
        # Fetch live prices for all holdings
        data = []
        for h in holdings:
            item = h.to_dict()
            try:
                result = get_stock_data(h.ticker)
                if result:
                    _, df, info = result
                    current = float(info.get('currentPrice', df['Close'].iloc[-1]))
                    currency = info.get('currency', 'USD')
                    item['currentPrice'] = current
                    item['currency'] = currency
                    item['totalCost'] = round(h.shares * h.avg_price, 2)
                    item['currentValue'] = round(h.shares * current, 2)
                    item['gainLoss'] = round((current - h.avg_price) * h.shares, 2)
                    item['gainLossPct'] = round((current - h.avg_price) / h.avg_price * 100, 2) if h.avg_price else 0
                    item['companyName'] = info.get('longName', info.get('shortName', h.ticker))
            except Exception:
                item['currentPrice'] = None
                item['totalCost'] = round(h.shares * h.avg_price, 2)
                item['currentValue'] = None
                item['gainLoss'] = None
                item['gainLossPct'] = None
                item['companyName'] = h.ticker
        total_cost = sum(h['totalCost'] for h in data)
        total_value = sum(h['currentValue'] for h in data if h['currentValue'])
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        return Response({
            'holdings': data,
            'summary': {
                'totalCost': round(total_cost, 2),
                'totalValue': round(total_value, 2),
                'totalGainLoss': round(total_value - total_cost, 2),
                'totalGainLossPct': round((total_value - total_cost) / total_cost * 100, 2) if total_cost else 0,
                'count': len(data),
                'virtualBalance': profile.virtual_balance
            }
        })

    if request.method == 'POST':
        ticker = request.data.get('ticker', '').upper()
        shares = float(request.data.get('shares', 0))
        avg_price = float(request.data.get('avgPrice', 0))
        if not ticker or shares <= 0 or avg_price <= 0:
            return Response({'error': 'ticker, shares and avgPrice required'}, status=400)
        obj, _ = PortfolioHolding.objects.update_or_create(
            user=request.user, ticker=ticker,
            defaults={'shares': shares, 'avg_price': avg_price}
        )
        return Response(obj.to_dict(), status=201)

    if request.method == 'DELETE':
        ticker = request.data.get('ticker', '').upper()
        PortfolioHolding.objects.filter(user=request.user, ticker=ticker).delete()
        return Response({'message': f'{ticker} removed'})


# ── IPO ───────────────────────────────────────────────────────────────────────

def _fetch_nasdaq_ipos(months=2):
    """Fetch real IPO data from Nasdaq API for US market."""
    import requests as req
    from datetime import datetime, timedelta
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    vader = SentimentIntensityAnalyzer()

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
               'Accept': 'application/json'}
    ipos = []
    now = datetime.now()

    # Fetch current + next month
    for delta in range(months):
        dt = now.replace(day=1) + timedelta(days=32 * delta)
        ym = f"{dt.year}-{dt.month:02d}"
        try:
            r = req.get(f'https://api.nasdaq.com/api/ipo/calendar?date={ym}',
                        headers=headers, timeout=10)
            if r.status_code != 200:
                continue
            data = r.json().get('data', {})

            for section, status in [('upcoming', 'Upcoming'), ('priced', 'Priced'), ('filed', 'Filed'), ('withdrawn', 'Withdrawn')]:
                rows = data.get(section, {}).get('rows') or []
                for row in rows:
                    company = row.get('companyName', '')
                    ticker = row.get('proposedTickerSymbol', '')
                    exchange = row.get('proposedExchange', '')
                    price_str = row.get('proposedSharePrice', '0').replace('$', '').replace(',', '').strip()
                    shares_str = row.get('sharesOffered', '0').replace(',', '').strip()
                    offer_str = row.get('dollarValueOfSharesOffered', '$0').replace('$', '').replace(',', '').strip()
                    date_str = row.get('pricedDate') or row.get('expectedPriceDate', '')

                    try: price = float(price_str) if price_str and price_str != 'N/A' else 0
                    except: price = 0
                    try: shares = int(shares_str) if shares_str else 0
                    except: shares = 0
                    try: offer_amt = float(offer_str) if offer_str else 0
                    except: offer_amt = 0

                    sentiment = vader.polarity_scores(company)['compound']

                    ipos.append({
                        'company': company,
                        'ticker': ticker,
                        'exchange': exchange,
                        'status': status,
                        'issuePrice': price,
                        'sharesOffered': shares,
                        'offerAmount': offer_amt,
                        'date': date_str,
                        'region': 'us',
                        'currency': '$',
                        'sentiment': round(sentiment, 3),
                        'sentiment_label': 'bullish' if sentiment > 0.1 else 'bearish' if sentiment < -0.1 else 'neutral',
                        'url': f'https://www.nasdaq.com/market-activity/ipos',
                        'source': 'Nasdaq',
                    })
        except Exception as e:
            print(f'Nasdaq IPO fetch error: {e}')

    return ipos


def _fetch_india_ipos():
    """Fetch India IPO data from Chittorgarh (public IPO calendar)."""
    import requests as req
    from bs4 import BeautifulSoup
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    vader = SentimentIntensityAnalyzer()

    ipos = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120'}

    try:
        r = req.get('https://www.chittorgarh.com/ipo/ipo_dashboard.asp', headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'lxml')
        tables = soup.find_all('table')

        for table in tables:
            rows = table.find_all('tr')
            for row in rows[1:]:  # skip header
                cells = [c.get_text(strip=True) for c in row.find_all(['td', 'th'])]
                if len(cells) >= 3:
                    company = cells[0] if cells[0] else ''
                    if not company or company.lower() in ['company', 'name', 'ipo name']:
                        continue
                    # Extract price if available
                    price = 0
                    for cell in cells:
                        import re
                        m = re.search(r'[₹]?\s*(\d+(?:\.\d+)?)', cell)
                        if m and 10 < float(m.group(1)) < 100000:
                            price = float(m.group(1))
                            break

                    date_str = cells[2] if len(cells) > 2 else ''
                    sentiment = vader.polarity_scores(company)['compound']

                    ipos.append({
                        'company': company,
                        'ticker': '',
                        'exchange': 'NSE/BSE',
                        'status': 'Upcoming',
                        'issuePrice': price,
                        'sharesOffered': 0,
                        'offerAmount': 0,
                        'date': date_str,
                        'region': 'india',
                        'currency': '₹',
                        'sentiment': round(sentiment, 3),
                        'sentiment_label': 'bullish' if sentiment > 0.1 else 'bearish' if sentiment < -0.1 else 'neutral',
                        'url': 'https://www.chittorgarh.com/ipo/ipo_dashboard.asp',
                        'source': 'Chittorgarh',
                    })
    except Exception as e:
        print(f'India IPO fetch error: {e}')

    # Fallback: use news scraping for India
    if not ipos:
        try:
            from duckduckgo_search import DDGS
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            import re
            vader2 = SentimentIntensityAnalyzer()
            with DDGS() as ddgs:
                results = list(ddgs.news('upcoming IPO 2026 India NSE BSE SEBI', max_results=15, timelimit='m'))
            for r in results:
                title = r.get('title', '')
                body = r.get('body', '')
                match = re.search(r'([A-Z][a-zA-Z\s&]+?)\s+IPO', title)
                company = match.group(1).strip() if match else title[:50]
                sentiment = vader2.polarity_scores(f"{title} {body}")['compound']
                ipos.append({
                    'company': company,
                    'ticker': '',
                    'exchange': 'NSE/BSE',
                    'status': 'News',
                    'issuePrice': 0,
                    'sharesOffered': 0,
                    'offerAmount': 0,
                    'date': r.get('date', ''),
                    'region': 'india',
                    'currency': '₹',
                    'sentiment': round(sentiment, 3),
                    'sentiment_label': 'bullish' if sentiment > 0.1 else 'bearish' if sentiment < -0.1 else 'neutral',
                    'url': r.get('url', ''),
                    'source': r.get('source', ''),
                    'summary': body[:300],
                })
        except Exception as e:
            print(f'India IPO news fallback error: {e}')

    return ipos


def _fetch_generic_ipos(region: str):
    """Fetch IPO news for UK/Europe/Asia via DuckDuckGo news."""
    import re
    from duckduckgo_search import DDGS
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    vader = SentimentIntensityAnalyzer()

    region_queries = {
        'uk':     'upcoming IPO 2026 London Stock Exchange LSE UK listing',
        'europe': 'upcoming IPO 2026 Europe Euronext Frankfurt listing',
        'asia':   'upcoming IPO 2026 Asia Hong Kong Tokyo Singapore listing',
    }
    region_currency = {'uk': '£', 'europe': '€', 'asia': '$'}
    region_exchange = {'uk': 'LSE', 'europe': 'Euronext', 'asia': 'HK/Tokyo/SGX'}

    query = region_queries.get(region, f'upcoming IPO 2026 {region}')
    ipos = []

    try:
        with DDGS() as ddgs:
            results = list(ddgs.news(query, max_results=15, timelimit='m'))
        for r in results:
            title = r.get('title', '')
            body = r.get('body', '')
            match = re.search(r'([A-Z][a-zA-Z\s&\.]+?)\s+(?:IPO|listing|floats|float)', title, re.IGNORECASE)
            company = match.group(1).strip() if match else title[:50]
            sentiment = vader.polarity_scores(f"{title} {body}")['compound']
            ipos.append({
                'company': company,
                'ticker': '',
                'exchange': region_exchange.get(region, ''),
                'status': 'News',
                'issuePrice': 0,
                'sharesOffered': 0,
                'offerAmount': 0,
                'date': r.get('date', ''),
                'region': region,
                'currency': region_currency.get(region, '$'),
                'sentiment': round(sentiment, 3),
                'sentiment_label': 'bullish' if sentiment > 0.1 else 'bearish' if sentiment < -0.1 else 'neutral',
                'url': r.get('url', ''),
                'source': r.get('source', ''),
                'summary': body[:300],
            })
    except Exception as e:
        print(f'Generic IPO fetch error for {region}: {e}')

    return ipos


@api_view(['GET'])
@permission_classes([AllowAny])
def ipo_list(request):
    region = request.query_params.get('region', 'us').lower()
    try:
        if region == 'us':
            ipos = _fetch_nasdaq_ipos(months=2)
        elif region == 'india':
            ipos = _fetch_india_ipos()
        else:
            ipos = _fetch_generic_ipos(region)

        # Sort: Upcoming first, then by date
        status_order = {'Upcoming': 0, 'Filed': 1, 'News': 2, 'Priced': 3, 'Withdrawn': 4}
        ipos.sort(key=lambda x: (status_order.get(x.get('status', 'News'), 5), x.get('date', '')))

        return Response({'ipos': ipos, 'region': region, 'total': len(ipos)})
    except Exception as e:
        import traceback; traceback.print_exc()
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def ipo_predict(request):
    """Predict IPO performance using sector peer comparison + sentiment."""
    company = request.data.get('company', '')
    sector = request.data.get('sector', 'Technology')
    sentiment_score = float(request.data.get('sentiment', 0))
    issue_price = float(request.data.get('issuePrice', 0))
    region = request.data.get('region', 'us')

    sector_tickers = {
        'Technology': ['AAPL', 'MSFT', 'GOOGL'],
        'Finance': ['JPM', 'GS', 'BAC'],
        'Healthcare': ['JNJ', 'PFE', 'UNH'],
        'Energy': ['XOM', 'CVX', 'COP'],
        'Consumer': ['AMZN', 'WMT', 'TGT'],
        'Auto': ['TSLA', 'GM', 'F'],
        'India Tech': ['TCS.NS', 'INFY.NS', 'WIPRO.NS'],
        'India Finance': ['HDFCBANK.NS', 'ICICIBANK.NS', 'SBIN.NS'],
        'India Consumer': ['HINDUNILVR.NS', 'ITC.NS', 'NESTLEIND.NS'],
    }
    peers = sector_tickers.get(sector, sector_tickers['Technology'])

    peer_data = []
    for t in peers:
        try:
            result = get_stock_data(t)
            if result:
                _, df, info = result
                ytd = float(df['Close'].iloc[-1] / df['Close'].iloc[0] - 1) * 100 if len(df) > 1 else 0
                peer_data.append({
                    'ticker': t, 'pe': info.get('trailingPE') or 0,
                    'beta': info.get('beta') or 1.0, 'ytd': round(ytd, 2),
                })
        except Exception:
            pass

    avg_pe = sum(p['pe'] for p in peer_data if p['pe']) / max(len([p for p in peer_data if p['pe']]), 1)
    avg_beta = sum(p['beta'] for p in peer_data) / max(len(peer_data), 1)
    avg_ytd = sum(p['ytd'] for p in peer_data) / max(len(peer_data), 1)

    base_return = avg_ytd * 0.3 + sentiment_score * 30
    risk_adj = 1 + (avg_beta - 1) * 0.2
    predicted_1d = round(base_return * 0.05 * risk_adj, 2)
    predicted_1w = round(base_return * 0.15 * risk_adj, 2)
    predicted_1m = round(base_return * 0.4 * risk_adj, 2)
    predicted_1y = round(base_return * risk_adj, 2)

    listing_price = round(issue_price * (1 + predicted_1d / 100), 2) if issue_price else None

    if predicted_1m > 15 and sentiment_score > 0.1:
        rec, rec_color = 'Strong Subscribe', 'bullish'
    elif predicted_1m > 5:
        rec, rec_color = 'Subscribe', 'bullish'
    elif predicted_1m < -10:
        rec, rec_color = 'Avoid', 'bearish'
    else:
        rec, rec_color = 'Neutral / Wait', 'neutral'

    return Response({
        'company': company, 'sector': sector,
        'recommendation': rec, 'recommendation_sentiment': rec_color,
        'issuePrice': issue_price, 'listingPriceEstimate': listing_price,
        'predictions': {'day1': predicted_1d, 'week1': predicted_1w, 'month1': predicted_1m, 'year1': predicted_1y},
        'peerAnalysis': {'avgPE': round(avg_pe, 1), 'avgBeta': round(avg_beta, 2),
                         'sectorYTD': round(avg_ytd, 2), 'peers': peer_data},
        'sentimentScore': sentiment_score,
    })


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
            'sentiment': {'overall': label, 'score': round(combined, 3), 'confidence': min(95, 50 + total * 2)},
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
            for p in get_reddit_scraper().fetch_ticker_posts(ticker, limit=limit):
                posts.append({'id': p.get('id'), 'source': 'reddit', 'subreddit': p.get('subreddit'),
                               'title': p.get('title'), 'content': p.get('content', '')[:300],
                               'author': p.get('author'), 'url': p.get('url'),
                               'sentiment': p.get('sentiment_score'), 'engagement': p.get('engagement_score'),
                               'created_at': p.get('created_at').isoformat() if p.get('created_at') else None})
        if source in ['all', 'stocktwits']:
            for p in get_forum_scraper().fetch_stocktwits(ticker, limit=limit):
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
        articles = get_news_client().search_stock_news(ticker, max_results=limit)
        def safe_dt(val):
            if val is None: return None
            if hasattr(val, 'isoformat'): return val.isoformat()
            return str(val)
        return Response({
            'ticker': ticker,
            'articles': [{'title': a.get('title'), 'summary': a.get('summary', '')[:500],
                           'url': a.get('url'), 'source': a.get('source'),
                           'sentiment': round(float(a.get('sentiment_score') or 0), 3),
                           'published_at': safe_dt(a.get('published_at'))} for a in articles],
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
        from ai.gemini_client import get_ollama_analyzer
        analyzer = get_ollama_analyzer()
        context = f"ticker: {ticker.upper()}" if ticker else None
        reply = analyzer.chat(message, context=context)
        return Response({
            'response': reply, 'model_used': analyzer.model,
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
            ticker=ticker, overall_sentiment=ai.get('overall_sentiment', 'neutral'),
            confidence_score=ai.get('confidence', 50), reasoning=ai.get('short_term_outlook', ''),
            key_points=ai.get('key_reasoning', []), risk_factors=ai.get('risk_factors', []),
            predicted_trend=ai.get('predicted_trend', ''), recommendation=ai.get('recommendation', ''),
            reddit_posts_count=len(reddit_posts), news_articles_count=len(news_articles),
        )
        return Response(analysis)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
