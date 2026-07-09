import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Globe, ArrowRight, Coins, Building2, Search } from 'lucide-react'

const MARKETS = [
  {
    category: 'Indian Markets (NSE/BSE)',
    icon: Building2,
    description: 'Top Indian companies across various caps',
    groups: [
      {
        name: 'Large Cap',
        stocks: [
          { ticker: 'RELIANCE.NS', name: 'Reliance Industries' },
          { ticker: 'TCS.NS', name: 'Tata Consultancy Services' },
          { ticker: 'HDFCBANK.NS', name: 'HDFC Bank' },
          { ticker: 'ICICIBANK.NS', name: 'ICICI Bank' },
          { ticker: 'INFY.NS', name: 'Infosys' },
          { ticker: 'ITC.NS', name: 'ITC Limited' },
          { ticker: 'SBIN.NS', name: 'State Bank of India' },
          { ticker: 'BHARTIARTL.NS', name: 'Bharti Airtel' },
          { ticker: 'HINDUNILVR.NS', name: 'Hindustan Unilever' },
        ]
      },
      {
        name: 'Mid & Small Cap',
        stocks: [
          { ticker: 'ZOMATO.NS', name: 'Zomato' },
          { ticker: 'IREDA.NS', name: 'IREDA' },
          { ticker: 'SUZLON.NS', name: 'Suzlon Energy' },
          { ticker: 'IRFC.NS', name: 'Indian Railway Finance' },
          { ticker: 'TATASTEEL.NS', name: 'Tata Steel' },
          { ticker: 'JIOFIN.NS', name: 'Jio Financial Services' },
          { ticker: 'TVSMOTOR.NS', name: 'TVS Motor Company' },
          { ticker: 'YESBANK.NS', name: 'Yes Bank' },
        ]
      }
    ]
  },
  {
    category: 'US Markets (NYSE/NASDAQ)',
    icon: Globe,
    description: 'Top technology and global companies',
    groups: [
      {
        name: 'Mega Cap Tech',
        stocks: [
          { ticker: 'AAPL', name: 'Apple Inc.' },
          { ticker: 'MSFT', name: 'Microsoft Corp.' },
          { ticker: 'NVDA', name: 'NVIDIA Corp.' },
          { ticker: 'GOOGL', name: 'Alphabet Inc.' },
          { ticker: 'AMZN', name: 'Amazon.com Inc.' },
          { ticker: 'META', name: 'Meta Platforms' },
          { ticker: 'TSLA', name: 'Tesla Inc.' },
        ]
      },
      {
        name: 'Popular Growth',
        stocks: [
          { ticker: 'PLTR', name: 'Palantir Technologies' },
          { ticker: 'AMD', name: 'Advanced Micro Devices' },
          { ticker: 'SMCI', name: 'Super Micro Computer' },
          { ticker: 'COIN', name: 'Coinbase Global' },
          { ticker: 'UBER', name: 'Uber Technologies' },
          { ticker: 'CRWD', name: 'CrowdStrike' },
          { ticker: 'HOOD', name: 'Robinhood Markets' },
        ]
      }
    ]
  },
  {
    category: 'Cryptocurrency',
    icon: Coins,
    description: 'Major digital assets (24/7 trading)',
    groups: [
      {
        name: 'Top Coins',
        stocks: [
          { ticker: 'BTC-USD', name: 'Bitcoin' },
          { ticker: 'ETH-USD', name: 'Ethereum' },
          { ticker: 'SOL-USD', name: 'Solana' },
          { ticker: 'BNB-USD', name: 'Binance Coin' },
          { ticker: 'XRP-USD', name: 'XRP' },
          { ticker: 'DOGE-USD', name: 'Dogecoin' },
          { ticker: 'ADA-USD', name: 'Cardano' },
          { ticker: 'AVAX-USD', name: 'Avalanche' },
        ]
      }
    ]
  }
]

export default function Explore() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')

  const handleStockClick = (ticker: string) => {
    navigate('/dashboard', { state: { searchTicker: ticker } })
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      handleStockClick(query.trim())
    }
  }

  // Filter logic
  const filteredMarkets = MARKETS.map(market => {
    const groups = market.groups.map(group => {
      const stocks = group.stocks.filter(
        s => s.ticker.toLowerCase().includes(query.toLowerCase()) || 
             s.name.toLowerCase().includes(query.toLowerCase())
      )
      return { ...group, stocks }
    }).filter(g => g.stocks.length > 0)
    return { ...market, groups }
  }).filter(m => m.groups.length > 0)

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold mb-2">Explore Markets</h1>
          <p className="text-gray-400 text-sm">
            Browse popular stocks and assets from global markets, or search for any ticker.
          </p>
        </div>
        
        <form onSubmit={handleSearch} className="relative w-full md:w-96">
          <Search size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500" />
          <input 
            type="text" 
            placeholder="Search any ticker (e.g. AAPL, TCS.NS)..." 
            className="input-field pl-10 w-full"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </form>
      </div>

      <div className="space-y-12">
        {filteredMarkets.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            No predefined stocks found for "{query}". 
            Press Enter to search for this ticker on the dashboard anyway!
          </div>
        ) : (
          filteredMarkets.map((market) => (
          <div key={market.category} className="space-y-6">
            <div className="flex items-center gap-3 border-b border-white/5 pb-4">
              <div className="w-10 h-10 rounded-xl bg-brand-600/20 flex items-center justify-center">
                <market.icon size={20} className="text-brand-400" />
              </div>
              <div>
                <h2 className="text-xl font-bold">{market.category}</h2>
                <p className="text-sm text-gray-500">{market.description}</p>
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              {market.groups.map((group) => (
                <div key={group.name} className="card bg-gray-900/50">
                  <h3 className="font-semibold text-gray-300 mb-4 flex items-center gap-2">
                    {group.name}
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {group.stocks.map((stock) => (
                      <button
                        key={stock.ticker}
                        onClick={() => handleStockClick(stock.ticker)}
                        className="flex items-center justify-between p-3 rounded-xl bg-white/5 hover:bg-brand-600/20 border border-transparent hover:border-brand-500/30 transition-all text-left group"
                      >
                        <div className="min-w-0 pr-2">
                          <div className="font-bold text-sm text-white group-hover:text-brand-400 transition-colors truncate">
                            {stock.ticker}
                          </div>
                          <div className="text-xs text-gray-500 truncate mt-0.5">
                            {stock.name}
                          </div>
                        </div>
                        <ArrowRight size={14} className="text-gray-600 group-hover:text-brand-400 opacity-0 group-hover:opacity-100 transition-all -translate-x-2 group-hover:translate-x-0" />
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )))}
      </div>
    </div>
  )
}
