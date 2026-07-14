"""
Gemini Client - Replaces Ollama with Google Gemini API.
Falls back to VADER rule-based analysis if Gemini is unavailable.
Formats all responses as natural language.
"""

import json
import os
import requests as _requests
from datetime import datetime
from typing import Dict, List, Optional
from google import genai
from google.genai import types
from dotenv import load_dotenv, dotenv_values

# Load .env file — override=True ensures .env wins over stale shell vars
load_dotenv(override=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()

# Lazy client — created on first use so env vars are always fresh
_gemini_client = None


def _get_gemini_client():
    """Return a cached Gemini client, initializing it on first call."""
    global _gemini_client, GEMINI_API_KEY
    if _gemini_client is not None:
        return _gemini_client
    # Re-read key in case it was set after module import (e.g. Render env inject)
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        return None
    try:
        _gemini_client = genai.Client(api_key=key)
        GEMINI_API_KEY = key
        print(f"[OK] Gemini client initialized. Model: {GEMINI_MODEL}")
        return _gemini_client
    except Exception as e:
        print(f"[FAIL] Gemini client init failed: {e}")
        return None

# Conversational system prompt — explicitly forbids raw JSON in chat
SYSTEM_PROMPT = """You are StockAI, a professional stock market analyst assistant built into a trading platform.

Your personality:
- Confident, concise, and data-driven
- Speak in plain English — NEVER output raw JSON or code blocks in chat responses
- Use bullet points and bold text (markdown) for clarity
- Always add a brief disclaimer for investment advice

When asked about a stock price or data, respond conversationally like:
"**AAPL** is currently trading at **$189.50**, up **+1.2%** today. The 52-week range is $164–$199."

When asked for analysis, structure your response with clear sections.
Keep responses under 200 words unless a detailed breakdown is requested."""


def _gemini_chat(prompt: str, system: str = SYSTEM_PROMPT) -> Optional[str]:
    """Call Gemini API using the official google-genai SDK."""
    client = _get_gemini_client()
    if not client:
        print("[WARN] Gemini unavailable - GEMINI_API_KEY not set or client failed")
        return None
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system,
                temperature=0.7,
                max_output_tokens=512,
            ),
        )
        text = response.text.strip()
        print(f"[OK] Gemini responded ({len(text)} chars)")
        return text
    except Exception as e:
        print(f"[FAIL] Gemini API error: {e}")
        return None



def _is_gemini_available() -> bool:
    """Check if Gemini client can be obtained."""
    return _get_gemini_client() is not None


def _vader_sentiment(text: str) -> float:
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        return SentimentIntensityAnalyzer().polarity_scores(text)["compound"]
    except Exception:
        return 0.0


# Minimum ticker length to avoid garbage like 'A', 'I'
_MIN_TICKER_LEN = 2

# Simple set of obviously invalid "tickers" — English words not in SKIP_WORDS
# that still sometimes slip through (e.g. short words the user types)
_INVALID_TICKERS = {
    'HTTP', 'HTML', 'JSON', 'API', 'URL', 'NS', 'BSE', 'NSE', 'NYSE',
    'ETF', 'IPO', 'GDP', 'CPI', 'FED', 'RBI', 'SEBI', 'SEC', 'USD',
    'INR', 'EUR', 'GBP', 'YEN', 'ADR', 'EPS', 'ROE', 'ROI', 'NAV',
    'AI', 'ML', 'IT', 'AM', 'PM', 'EST', 'IST', 'UTC',
}


def _looks_like_ticker(symbol: str) -> bool:
    """Basic sanity check — reject obvious non-tickers."""
    s = symbol.upper().split(".")[0]   # strip .NS / .BO suffix for check
    if len(s) < _MIN_TICKER_LEN:
        return False
    if s in _SKIP_WORDS or s in _INVALID_TICKERS:
        return False
    # Must be all letters (no digits/special chars in base symbol)
    return s.isalpha()


def _get_live_price(ticker: str) -> Optional[Dict]:
    """Fetch live price from yfinance for use in chat responses."""
    if not _looks_like_ticker(ticker):
        return None
    try:
        import yfinance as yf
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            t = yf.Ticker(ticker)
            info = t.info
            hist = t.history(period="2d")
        if hist.empty:
            return None
        price = float(info.get("currentPrice", hist["Close"].iloc[-1]))
        prev = float(hist["Close"].iloc[-2] if len(hist) > 1 else price)
        chg = price - prev
        chg_pct = (chg / prev * 100) if prev else 0
        currency = "₹" if info.get("currency") == "INR" else "$"
        return {
            "ticker": ticker.upper(),
            "name": info.get("longName", info.get("shortName", ticker.upper())),
            "price": price,
            "change": chg,
            "change_pct": chg_pct,
            "currency": currency,
            "high_52w": info.get("fiftyTwoWeekHigh", 0),
            "low_52w": info.get("fiftyTwoWeekLow", 0),
            "market_cap": info.get("marketCap", 0),
            "pe": info.get("trailingPE", 0) or 0,
            "sector": info.get("sector", ""),
        }
    except Exception:
        return None


def _format_price_response(data: Dict) -> str:
    """Format live price data as a natural language response."""
    c = data["currency"]
    sign = "+" if data["change"] >= 0 else ""
    color = "📈" if data["change"] >= 0 else "📉"
    lines = [
        f"{color} **{data['ticker']}** — {data['name']}",
        f"**Price:** {c}{data['price']:.2f}  |  **Change:** {sign}{c}{abs(data['change']):.2f} ({sign}{data['change_pct']:.2f}%)",
    ]
    if data.get("high_52w"):
        lines.append(f"**52W Range:** {c}{data['low_52w']:.2f} – {c}{data['high_52w']:.2f}")
    if data.get("market_cap"):
        cap = data["market_cap"]
        cap_str = f"{c}{cap/1e12:.2f}T" if cap > 1e12 else f"{c}{cap/1e9:.2f}B"
        lines.append(f"**Market Cap:** {cap_str}")
    if data.get("pe"):
        lines.append(f"**P/E Ratio:** {data['pe']:.1f}")
    if data.get("sector"):
        lines.append(f"**Sector:** {data['sector']}")
    lines.append("\n*Data from Yahoo Finance. Not financial advice.*")
    return "\n".join(lines)


def _clean_json_response(content: str) -> str:
    """Convert any JSON in Gemini response to natural language."""
    stripped = content.strip()
    if not (stripped.startswith("{") or stripped.startswith("[")):
        return content

    try:
        start = stripped.find("{")
        end = stripped.rfind("}") + 1
        data = json.loads(stripped[start:end])

        parts = []

        if "overall_sentiment" in data:
            sent = data.get("overall_sentiment", "neutral")
            conf = data.get("confidence_score", 0)
            trend = data.get("predicted_trend", "")
            rec = data.get("recommendation", "").replace("_", " ").title()
            outlook = data.get("short_term_outlook", "")
            reasoning = data.get("key_reasoning", [])
            risks = data.get("risk_factors", [])

            emoji = "🟢" if sent == "bullish" else "🔴" if sent == "bearish" else "🟡"
            parts.append(f"{emoji} **Sentiment: {sent.upper()}** (Confidence: {conf}%)")
            if trend:
                parts.append(f"**Predicted Trend:** {trend.capitalize()}")
            if rec:
                parts.append(f"**Recommendation:** {rec}")
            if outlook:
                parts.append(f"\n{outlook}")
            if reasoning:
                parts.append("\n**Key Reasoning:**")
                parts.extend(f"• {r}" for r in reasoning[:3])
            if risks:
                parts.append("\n**Risk Factors:**")
                parts.extend(f"• {r}" for r in risks[:2])
            parts.append("\n*Not financial advice. Always do your own research.*")
            return "\n".join(parts)

        lines = []
        for k, v in data.items():
            label = k.replace("_", " ").title()
            if isinstance(v, list):
                if v:
                    lines.append(f"**{label}:**")
                    lines.extend(f"• {i}" for i in v[:4])
            elif isinstance(v, (int, float)):
                lines.append(f"**{label}:** {v}")
            elif isinstance(v, str) and v:
                lines.append(f"**{label}:** {v}")
        return "\n".join(lines) if lines else content

    except Exception:
        return content


# Common English words to skip when detecting stock tickers
_SKIP_WORDS = {
    'WHAT', 'IS', 'THE', 'OF', 'ARE', 'HOW', 'MUCH', 'PRICE', 'CURRENT',
    'FOR', 'ME', 'GIVE', 'GET', 'TELL', 'ABOUT', 'CAN', 'YOU', 'SHOW',
    'ANY', 'AND', 'OR', 'NOT', 'BUT', 'ON', 'IN', 'AT', 'TO', 'DO', 'MY',
    'WE', 'UP', 'OUT', 'IF', 'ALL', 'SO', 'AS', 'IT', 'ITS', 'BE', 'BY',
    'AN', 'HE', 'SHE', 'US', 'NO', 'GO', 'NOW', 'NEW', 'TOP', 'WAY',
    'WHO', 'WHY', 'WHEN', 'WHERE', 'WILL', 'WITH', 'FROM', 'INTO', 'MORE',
    'STOCK', 'SHARE', 'TRADE', 'VALUE', 'WORTH', 'QUOTE', 'COST', 'BUY',
    'SELL', 'HOLD', 'LIVE', 'REAL', 'TODAY', 'LAST', 'NEXT', 'HIGH', 'LOW',
}


def _is_price_query(message: str) -> Optional[str]:
    """Detect price queries and extract ticker. Returns valid ticker or None."""
    import re
    msg = message.lower()
    price_words = ["price", "trading at", "current price", "stock price",
                   "how much", "worth", "value", "quote", "cost"]
    if not any(w in msg for w in price_words):
        return None

    # Priority 1: $TICKER pattern — e.g. $AAPL, $RELIANCE
    match = re.search(r'\$([A-Za-z]{1,12})', message)
    if match:
        t = match.group(1).upper()
        if _looks_like_ticker(t):
            return t

    # Priority 2: TICKER.XX pattern — supports long Indian tickers
    # e.g. RELIANCE.NS, BAJFINANCE.BO (up to 12 chars before dot)
    match = re.search(r'\b([A-Za-z]{2,12}\.[A-Za-z]{2,3})\b', message)
    if match:
        t = match.group(1).upper()
        base = t.split(".")[0]
        if _looks_like_ticker(base):
            return t

    # Priority 3: All-caps word that looks like a ticker (e.g. AAPL, TSLA)
    # Only match if user explicitly capitalized it
    caps_candidates = re.findall(r'\b([A-Z]{2,10})\b', message)
    for c in caps_candidates:
        if _looks_like_ticker(c):
            return c

    # Priority 4: Any word that looks like a known ticker format
    # (mixed-case last resort — avoids false positives from sentence words)
    all_candidates = re.findall(r'\b([A-Za-z]{2,10})\b', message.upper())
    for c in all_candidates:
        if _looks_like_ticker(c):
            return c

    return None


def _rule_based_analysis(message: str, ticker: str = "") -> str:
    """Smart rule-based responses using live data — never redirects user."""
    msg_lower = message.lower()
    t = ticker.upper() if ticker else ""

    # Price query — always try live fetch first
    if any(w in msg_lower for w in ["price", "trading", "how much", "worth", "quote", "current"]):
        detected = _is_price_query(message) or t
        if detected:
            data = _get_live_price(detected)
            if data:
                return _format_price_response(data)
        # Live fetch failed — give best effort answer
        return (
            f"⚠️ I couldn't fetch live price data for **{detected or 'that stock'}** right now "
            "(Yahoo Finance may be temporarily unavailable).\n\n"
            "Please try again in a few seconds, or specify the exact ticker symbol "
            "(e.g. `AAPL`, `RELIANCE.NS`, `TSLA`)."
        )

    # Buy decision — use live data if ticker known
    if any(w in msg_lower for w in ["buy", "should i buy"]):
        live = _get_live_price(t) if t else None
        header = f"**{live['ticker']} — {live['name']}**\n" \
                 f"Current Price: {live['currency']}{live['price']:.2f} " \
                 f"({'+' if live['change'] >= 0 else ''}{live['change_pct']:.2f}%)\n\n" if live else ""
        return (
            f"{header}"
            f"**Buy Considerations{' for ' + t if t else ''}:**\n\n"
            "• 📊 Compare P/E ratio to sector average\n"
            "• 📈 Review last 2 quarterly earnings reports\n"
            "• 🏦 Check institutional ownership trends\n"
            "• 📰 Monitor recent news sentiment\n"
            "• ⚡ Consider overall market conditions\n\n"
            "*Not financial advice. Always do your own research.*"
        )

    # Sell decision — use live data if ticker known
    if any(w in msg_lower for w in ["sell", "should i sell"]):
        live = _get_live_price(t) if t else None
        header = f"**{live['ticker']} — {live['name']}**\n" \
                 f"Current Price: {live['currency']}{live['price']:.2f} " \
                 f"({'+' if live['change'] >= 0 else ''}{live['change_pct']:.2f}%)\n\n" if live else ""
        return (
            f"{header}"
            f"**Sell Considerations{' for ' + t if t else ''}:**\n\n"
            "• 🔄 Has your original investment thesis changed?\n"
            "• 💰 Is the stock significantly overvalued vs peers?\n"
            "• 📉 Are fundamentals deteriorating?\n"
            "• 🧾 Consider tax implications before selling\n"
            "• ⚠️ Don't sell purely on short-term volatility\n\n"
            "*Not financial advice. Always do your own research.*"
        )

    # Sentiment
    if any(w in msg_lower for w in ["sentiment", "mood", "bullish", "bearish", "feeling"]):
        live = _get_live_price(t) if t else None
        if live:
            direction = "📈 Bullish" if live["change"] >= 0 else "📉 Bearish"
            return (
                f"**{live['ticker']} Market Sentiment:**\n\n"
                f"Today's movement: **{direction}** ({'+' if live['change'] >= 0 else ''}{live['change_pct']:.2f}%)\n"
                f"Price: {live['currency']}{live['price']:.2f}\n"
                f"52W Range: {live['currency']}{live['low_52w']:.2f} – {live['currency']}{live['high_52w']:.2f}\n\n"
                "*For deep social sentiment (Reddit/StockTwits), visit AI Insights.*\n"
                "*Not financial advice.*"
            )
        return "Please specify a stock ticker to get sentiment (e.g. 'AAPL sentiment' or 'TSLA bullish or bearish?')"

    # Forecast/predict
    if any(w in msg_lower for w in ["predict", "forecast", "target", "future", "will"]):
        live = _get_live_price(t) if t else None
        if live:
            return (
                f"**{live['ticker']} — Current Snapshot:**\n\n"
                f"Price: {live['currency']}{live['price']:.2f} "
                f"({'+' if live['change'] >= 0 else ''}{live['change_pct']:.2f}% today)\n"
                f"52W High: {live['currency']}{live['high_52w']:.2f} | "
                f"52W Low: {live['currency']}{live['low_52w']:.2f}\n\n"
                "⚠️ AI price prediction requires Gemini API. "
                "LSTM model predictions are available on the Market Analysis page.\n\n"
                "*Not financial advice.*"
            )
        return "Please specify a ticker for price forecasting (e.g. 'predict AAPL' or 'TSLA forecast')."

    # Generic fallback — still helpful
    return (
        "I'm StockAI, your market analyst. I can help you with:\n\n"
        "• 💰 **Live prices** — ask: *'price of AAPL'* or *'TSLA current price'*\n"
        "• 📊 **Buy/Sell advice** — ask: *'should I buy MSFT?'*\n"
        "• 📈 **Sentiment** — ask: *'is NVDA bullish?'*\n"
        "• 🔮 **Forecasts** — ask: *'predict AAPL price'*\n\n"
        "*Gemini AI is offline — using live data + rule-based analysis.*"
    )


class OllamaAnalyzer:
    """
    Gemini-powered analyzer (class name kept for backward compatibility).
    Replaces the old Ollama-based implementation.
    """

    def __init__(self):
        # Don't cache availability at init — check dynamically each call
        key_set = bool(os.getenv("GEMINI_API_KEY", "").strip())
        if key_set:
            print(f"[OK] Gemini AI ready. Model: {GEMINI_MODEL}")
        else:
            print("[WARN] GEMINI_API_KEY not set - VADER fallback active")

    @property
    def model(self) -> str:
        return GEMINI_MODEL if _is_gemini_available() else "vader_fallback"

    def is_available(self) -> bool:
        return _is_gemini_available()

    def chat(self, message: str, context: Optional[str] = None) -> str:
        ticker_from_context = ""
        if context and "ticker:" in context.lower():
            ticker_from_context = context.split(":")[-1].strip()

        # Step 1: Always try live price lookup first for price queries
        price_ticker = _is_price_query(message) or ticker_from_context
        if price_ticker and any(w in message.lower() for w in
                                ["price", "trading", "how much", "worth", "quote", "current"]):
            data = _get_live_price(price_ticker)
            if data:
                return _format_price_response(data)
            # Price fetch failed — let Gemini answer it, or rule-based

        # Step 2: Try Gemini AI (adds context with live data if ticker known)
        if _is_gemini_available():
            # Enrich prompt with live data when possible
            live_context = ""
            detected_ticker = price_ticker or ticker_from_context
            if detected_ticker:
                live = _get_live_price(detected_ticker)
                if live:
                    live_context = (
                        f"Live market data for {live['ticker']}: "
                        f"Price={live['currency']}{live['price']:.2f}, "
                        f"Change={'+' if live['change'] >= 0 else ''}{live['change_pct']:.2f}%, "
                        f"52W High={live['currency']}{live['high_52w']:.2f}, "
                        f"52W Low={live['currency']}{live['low_52w']:.2f}, "
                        f"Market Cap={live['currency']}{live['market_cap']/1e9:.1f}B, "
                        f"P/E={live['pe']:.1f}, Sector={live['sector']}. "
                    )

            full_prompt = message
            if live_context or context:
                full_prompt = f"{live_context}{('Context: ' + context) if context else ''}\n\nUser question: {message}"

            result = _gemini_chat(full_prompt)
            if result:
                return _clean_json_response(result)

        # Step 3: Smart rule-based fallback — never redirects user, uses live data
        return _rule_based_analysis(message, ticker_from_context)

    def analyze_ticker(self, ticker: str, market_data: Dict,
                       social_data: Dict, news_data: List[Dict]) -> Dict:
        if not _is_gemini_available():
            return _fallback_analysis(ticker, social_data, news_data)

        reddit_posts = social_data.get("reddit_posts", [])[:5]
        discussions = "\n".join(
            f"{i+1}. {p.get('title', p.get('content', ''))[:100]}"
            for i, p in enumerate(reddit_posts)
        ) or "No recent discussions"
        news_lines = "\n".join(
            f"{i+1}. {a.get('title', '')}"
            for i, a in enumerate(news_data[:5])
        ) or "No recent news"

        prompt = (
            f"Analyze {ticker}: Price={market_data.get('price', 0)}, "
            f"Change={market_data.get('change_percent', 0)}%, "
            f"Reddit posts={social_data.get('reddit_count', 0)}, "
            f"sentiment={social_data.get('reddit_sentiment', 0):.2f}\n"
            f"Discussions:\n{discussions}\nNews:\n{news_lines}\n\n"
            f'Respond ONLY with JSON: {{"overall_sentiment":"bullish|bearish|neutral",'
            f'"confidence_score":0-100,"key_reasoning":[],"risk_factors":[],'
            f'"predicted_trend":"up|down|sideways","recommendation":"buy|hold|sell",'
            f'"short_term_outlook":""}}'
        )

        content = _gemini_chat(prompt)
        if content:
            try:
                start, end = content.find("{"), content.rfind("}") + 1
                result = json.loads(content[start:end])
                result.update({"ticker": ticker, "model_used": GEMINI_MODEL,
                               "generated_at": datetime.utcnow().isoformat()})
                return result
            except Exception:
                pass
        return _fallback_analysis(ticker, social_data, news_data)

    def quick_sentiment(self, text: str) -> Dict:
        score = _vader_sentiment(text)
        return {
            "sentiment": "positive" if score > 0.2 else "negative" if score < -0.2 else "neutral",
            "score": score,
            "method": "vader",
        }


def _fallback_analysis(ticker: str, social_data: Dict, news_data: List[Dict]) -> Dict:
    reddit_s = social_data.get("reddit_sentiment", 0)
    st_s = social_data.get("stocktwits_sentiment", 0)
    news_scores = [n.get("sentiment_score", 0) for n in news_data if n.get("sentiment_score") is not None]
    news_s = sum(news_scores) / len(news_scores) if news_scores else 0
    avg = reddit_s * 0.4 + st_s * 0.3 + news_s * 0.3

    if avg > 0.3:
        overall, rec, trend = "bullish", "buy", "up"
    elif avg < -0.3:
        overall, rec, trend = "bearish", "sell", "down"
    else:
        overall, rec, trend = "neutral", "hold", "sideways"

    data_pts = social_data.get("reddit_count", 0) + social_data.get("stocktwits_count", 0) + len(news_data)
    return {
        "ticker": ticker,
        "overall_sentiment": overall,
        "confidence_score": min(70, 30 + data_pts * 2),
        "key_reasoning": [
            f"Combined sentiment: {avg:.2f}",
            f"Reddit ({social_data.get('reddit_count', 0)} posts): {reddit_s:.2f}",
            f"News ({len(news_data)} articles): {news_s:.2f}",
        ],
        "risk_factors": ["Gemini AI unavailable — rule-based analysis", "Market conditions can change rapidly"],
        "predicted_trend": trend,
        "recommendation": rec,
        "short_term_outlook": f"Sentiment-based outlook: {overall} (score {avg:.2f})",
        "data_quality_note": "VADER fallback",
        "model_used": "vader_fallback",
        "generated_at": datetime.utcnow().isoformat(),
    }


# Backward-compatible alias used by views.py
def get_ollama_analyzer() -> OllamaAnalyzer:
    return OllamaAnalyzer()
