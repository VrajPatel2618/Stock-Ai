# Stock.AI - Advanced Stock Analysis Platform

A professional-grade stock analysis platform featuring AI-powered predictions, real-time sentiment analysis, and neural network forecasting.

![Stock.AI](https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=1200&h=400&fit=crop)

## 🚀 Features

### Core Analysis
- **AI Stock Predictions** - LSTM neural network predictions for stocks and commodities
- **Technical Analysis** - Real-time price data, P/E ratios, market cap, 52-week ranges
- **Commodity Forecasting** - Gold, Silver, Oil, Natural Gas predictions

### Sentiment & Social Analysis
- **Reddit Scraping** - Real-time sentiment from r/wallstreetbets, r/stocks, r/investing
- **StockTwits Integration** - Public social sentiment data
- **News Analysis** - DuckDuckGo news search with sentiment scoring
- **AI Critical Thinking** - Local Ollama LLM analysis (optional)

### Portfolio Management
- **Watchlist Tracking** - Track your favorite stocks with auto-refresh
- **Portfolio Dashboard** - Monitor holdings, gains/losses, and performance
- **Price Alerts** - Get notified when stocks hit your targets

## 🏗️ Tech Stack

### Backend
- **Python 3.10+** with Flask/Dash
- **yFinance** for market data
- **scikit-learn & PyTorch** for ML models
- **VADER** sentiment analysis
- **SQLite** database for persistence
- **APScheduler** for background jobs
- **Ollama** (optional) for AI critical thinking

### Frontend
- **React 18** with TypeScript
- **Vite** for fast development
- **TailwindCSS** for styling
- **Framer Motion** for animations
- **Zustand** for state management
- **React Router** for navigation

## 📦 Quick Start

### One-Click Launch
```bash
# Windows
start.bat

# Or manually:
.\start.bat
```

This will:
1. Start the Python backend (port 8050)
2. Start the React frontend (port 5173)
3. Open your browser to the app

### Manual Setup

#### Backend
```bash
cd "Stock Market"

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements_new.txt

# Initialize database
python database.py

# Run backend
python Market.py
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Optional: AI Critical Thinking
Install Ollama for enhanced AI analysis:
```bash
# Install Ollama from https://ollama.ai
ollama serve
ollama pull llama3.2
```

## 🔧 Configuration

All configuration is in `.env`:

```env
# Ollama (optional)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Database
DATABASE_URL=sqlite:///stock_analysis.db

# Scheduler intervals (minutes)
REDDIT_SCRAPE_INTERVAL=5
NEWS_FETCH_INTERVAL=15
AI_ANALYSIS_INTERVAL=30
```

**No API keys required!** All data sources use public APIs or web scraping.

## 📱 Pages

| Page | Description |
|------|-------------|
| **Market Analysis** | AI predictions for any stock ticker |
| **Commodities** | Gold, Silver, Oil forecasts with news |
| **AI Insights** | Sentiment analysis, social posts, AI chat |
| **Watchlist** | Track favorite stocks |
| **Portfolio** | Monitor your investments |
| **Settings** | Customize appearance and preferences |

## 🔌 API Endpoints

### Stock Analysis
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/stock/<ticker>` | GET | Stock data and fundamentals |
| `/api/predict/<ticker>` | GET | AI price predictions |
| `/api/commodity/<symbol>` | GET | Commodity predictions |

### Sentiment & Social
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/sentiment/<ticker>` | GET | Aggregated sentiment scores |
| `/api/social/<ticker>` | GET | Reddit/StockTwits posts |
| `/api/news/<ticker>` | GET | Recent news articles |
| `/api/analyze/<ticker>` | POST | Full AI critical analysis |
| `/api/chat` | POST | Chat with AI about stocks |

### Management
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/watchlist` | GET/POST/DELETE | Manage watchlist |
| `/api/health` | GET | API status and features |

## 🛡️ Security Notes

- All data is stored locally in SQLite
- No external API keys required
- Reddit scraping uses public JSON endpoints
- News search uses DuckDuckGo (no tracking)

## 📈 Screenshots

### Dark Mode
Professional trading terminal aesthetic with glowing accents and glassmorphism.

### Light Mode
Clean, modern interface for daytime trading.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - feel free to use for personal or commercial projects.

---

**Built with ❤️ for traders and investors**
