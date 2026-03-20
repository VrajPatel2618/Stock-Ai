"""
Ollama Client - uses requests directly, never crashes when Ollama is offline.
Falls back to VADER rule-based analysis. Formats all responses as natural language.
"""

import json
import os
import requests as _requests
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.7"))

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


def _get_available_model() -> Optional[str]:
    try:
        r = _requests.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
        if r.status_code != 200:
            return None
        models = [m.get("name", "") for m in r.json().get("models", [])]
        if not models:
            return None
        for m in models:
            if OLLAMA_MODEL in m:
                return m
        return models[0]
    except Exception:
        return None


def _ollama_chat(messages: List[Dict], model: str) -> Optional[str]:
    try:
        r = _requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json={"model": model, "messages": messages, "stream": False,
                  "options": {"temperature": OLLAMA_TEMPERATURE, "num_predict": 512}},
            timeout=90,
        )
        if r.status_code == 200:
            return r.json().get("message", {}).get("content", "")
        return None
    except Exception:
        return None


def _vader_sentiment(text: str) -> float:
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        return SentimentIntensityAnalyzer().polarity_scores(text)["compound"]
    except Exception:
        return 0.0


def _get_live_price(ticker: str) -> Optional[Dict]:
    """Fetch live price from yfinance for use in chat responses."""
    try:
        import yfinance as yf
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
    """Convert any JSON in Ollama response to natural language."""
    stripped = content.strip()
    # Check if response is mostly JSON
    if not (stripped.startswith("{") or stripped.startswith("[")):
        return content

    try:
        start = stripped.find("{")
        end = stripped.rfind("}") + 1
        data = json.loads(stripped[start:end])

        parts = []

        # Analysis JSON
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

        # Generic key-value JSON
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


def _is_price_query(message: str) -> Optional[str]:
    """Detect price queries and extract ticker. Returns ticker or None."""
    import re
    msg = message.lower()
    price_words = ["price", "trading at", "current price", "stock price",
                   "how much", "worth", "value", "quote", "cost"]
    if not any(w in msg for w in price_words):
        return None
    # Look for $TICKER or TICKER.NS patterns
    match = re.search(r'\$([A-Z]{1,5})|([A-Z]{1,5}\.[A-Z]{2})|([A-Z]{2,5})\b', message.upper())
    if match:
        return match.group(1) or match.group(2) or match.group(3)
    return None


def _fallback_chat(message: str, ticker: str = "") -> str:
    msg_lower = message.lower()

    if any(w in msg_lower for w in ["price", "trading", "how much", "worth", "quote"]):
        t = ticker or _is_price_query(message)
        if t:
            data = _get_live_price(t)
            if data:
                return _format_price_response(data)
        return (
            "I can look up live prices! Try asking:\n"
            "• \"What is the price of AAPL?\"\n"
            "• \"RELIANCE.NS current price\"\n\n"
            "Or use the **Market Analysis** page for full predictions."
        )

    if any(w in msg_lower for w in ["buy", "should i buy"]):
        return (
            f"**Buy Decision Framework{' for ' + ticker.upper() if ticker else ''}:**\n\n"
            "• Check P/E ratio vs sector average\n"
            "• Review last 2 earnings reports\n"
            "• Look at institutional ownership trends\n"
            "• Assess overall market sentiment\n\n"
            "Use the **Market Analysis** page for LSTM price predictions.\n\n"
            "*⚠️ Ollama AI offline — install from https://ollama.ai for full AI analysis.*"
        )

    if any(w in msg_lower for w in ["sell", "should i sell"]):
        return (
            f"**Sell Decision Framework{' for ' + ticker.upper() if ticker else ''}:**\n\n"
            "• Has your original investment thesis changed?\n"
            "• Is the stock significantly overvalued vs peers?\n"
            "• Consider tax implications before selling\n"
            "• Don't sell on short-term volatility alone\n\n"
            "*⚠️ Ollama AI offline — install from https://ollama.ai for full AI analysis.*"
        )

    if any(w in msg_lower for w in ["sentiment", "mood", "feeling", "bullish", "bearish"]):
        return (
            f"**Sentiment Analysis{' for ' + ticker.upper() if ticker else ''}** is available on the **AI Insights** page.\n\n"
            "It aggregates:\n"
            "• Reddit (r/wallstreetbets, r/stocks, r/investing)\n"
            "• StockTwits social posts\n"
            "• DuckDuckGo news with VADER scoring\n\n"
            "*⚠️ Ollama AI offline — VADER sentiment works without it.*"
        )

    if any(w in msg_lower for w in ["predict", "forecast", "target", "future"]):
        return (
            f"**Price Forecasting{' for ' + ticker.upper() if ticker else ''}** is available on the **Market Analysis** page.\n\n"
            "The LSTM neural network predicts:\n"
            "• Today / 1 Week / 1 Month\n"
            "• 6 Month / 1 Year ranges\n\n"
            "*⚠️ Ollama AI offline — LSTM predictions work without it.*"
        )

    return (
        "**StockAI is running in fallback mode** — Ollama is not connected.\n\n"
        "What still works:\n"
        "• 📈 LSTM price predictions (Market Analysis)\n"
        "• 📰 News sentiment (AI Insights)\n"
        "• 💬 Reddit/StockTwits posts (AI Insights)\n"
        "• 💰 Live price lookup (ask me \"price of AAPL\")\n\n"
        "To enable full AI chat:\n"
        "1. Install Ollama → https://ollama.ai\n"
        "2. Run `ollama serve`\n"
        "3. Run `ollama pull llama3.2`"
    )


class OllamaAnalyzer:
    def __init__(self):
        self._model = _get_available_model()
        if self._model:
            print(f"✓ Ollama connected. Model: {self._model}")
        else:
            print("⚠ Ollama offline — VADER fallback active")

    @property
    def model(self) -> str:
        return self._model or "vader_fallback"

    def is_available(self) -> bool:
        return self._model is not None

    def chat(self, message: str, context: Optional[str] = None) -> str:
        # Always try live price lookup first for price queries
        ticker_from_context = ""
        if context and "ticker:" in context.lower():
            ticker_from_context = context.split(":")[-1].strip()

        price_ticker = _is_price_query(message) or ticker_from_context
        if price_ticker and any(w in message.lower() for w in ["price", "trading", "how much", "worth", "quote", "current"]):
            data = _get_live_price(price_ticker)
            if data:
                return _format_price_response(data)

        # Try Ollama
        model = _get_available_model()
        if not model:
            return _fallback_chat(message, ticker_from_context)

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if context:
            messages.append({"role": "user", "content": f"Context: {context}"})
        messages.append({"role": "user", "content": message})

        result = _ollama_chat(messages, model)
        if result:
            return _clean_json_response(result)
        return _fallback_chat(message, ticker_from_context)

    def analyze_ticker(self, ticker: str, market_data: Dict,
                       social_data: Dict, news_data: List[Dict]) -> Dict:
        model = _get_available_model()
        if not model:
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
            f"Analyze {ticker}: Price={market_data.get('price',0)}, "
            f"Change={market_data.get('change_percent',0)}%, "
            f"Reddit posts={social_data.get('reddit_count',0)}, "
            f"sentiment={social_data.get('reddit_sentiment',0):.2f}\n"
            f"Discussions:\n{discussions}\nNews:\n{news_lines}\n\n"
            f'Respond ONLY with JSON: {{"overall_sentiment":"bullish|bearish|neutral",'
            f'"confidence_score":0-100,"key_reasoning":[],"risk_factors":[],'
            f'"predicted_trend":"up|down|sideways","recommendation":"buy|hold|sell",'
            f'"short_term_outlook":""}}'
        )

        content = _ollama_chat(
            [{"role": "system", "content": SYSTEM_PROMPT},
             {"role": "user", "content": prompt}], model
        )
        if content:
            try:
                start, end = content.find("{"), content.rfind("}") + 1
                result = json.loads(content[start:end])
                result.update({"ticker": ticker, "model_used": model,
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
        "risk_factors": ["Ollama offline — rule-based analysis", "Market conditions can change rapidly"],
        "predicted_trend": trend,
        "recommendation": rec,
        "short_term_outlook": f"Sentiment-based outlook: {overall} (score {avg:.2f})",
        "data_quality_note": "VADER fallback",
        "model_used": "vader_fallback",
        "generated_at": datetime.utcnow().isoformat(),
    }


def get_ollama_analyzer() -> OllamaAnalyzer:
    return OllamaAnalyzer()
