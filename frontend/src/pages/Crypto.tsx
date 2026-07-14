import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, Search, Bitcoin, Wallet, Zap } from 'lucide-react'
import { TickerSearch } from '../components/TickerSearch'

const CRYPTO_MARKETS = [
  {
    category: 'Major Cryptocurrencies',
    icon: Bitcoin,
    description: 'The highest market cap digital assets',
    groups: [
      {
        name: 'Top Tier (Layer 1)',
        stocks: [
          { ticker: 'BTC-USD', name: 'Bitcoin' },
          { ticker: 'ETH-USD', name: 'Ethereum' },
          { ticker: 'SOL-USD', name: 'Solana' },
          { ticker: 'BNB-USD', name: 'Binance Coin' },
          { ticker: 'ADA-USD', name: 'Cardano' },
          { ticker: 'AVAX-USD', name: 'Avalanche' },
        ]
      },
      {
        name: 'Memes & Altcoins',
        stocks: [
          { ticker: 'DOGE-USD', name: 'Dogecoin' },
          { ticker: 'SHIB-USD', name: 'Shiba Inu' },
          { ticker: 'XRP-USD', name: 'XRP' },
          { ticker: 'DOT-USD', name: 'Polkadot' },
          { ticker: 'LINK-USD', name: 'Chainlink' },
          { ticker: 'MATIC-USD', name: 'Polygon' },
        ]
      }
    ]
  },
  {
    category: 'DeFi & Ecosystems',
    icon: Wallet,
    description: 'Decentralized finance and utility tokens',
    groups: [
      {
        name: 'DeFi Protocols',
        stocks: [
          { ticker: 'UNI-USD', name: 'Uniswap' },
          { ticker: 'AAVE-USD', name: 'Aave' },
          { ticker: 'MKR-USD', name: 'Maker' },
          { ticker: 'SNX-USD', name: 'Synthetix' },
        ]
      },
      {
        name: 'Infrastructure',
        stocks: [
          { ticker: 'FIL-USD', name: 'Filecoin' },
          { ticker: 'AR-USD', name: 'Arweave' },
          { ticker: 'GRT-USD', name: 'The Graph' },
          { ticker: 'QNT-USD', name: 'Quant' },
        ]
      }
    ]
  }
]

export default function Crypto() {
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
  const filteredMarkets = CRYPTO_MARKETS.map(market => {
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
          <h1 className="text-2xl font-bold mb-2 text-brand-400 flex items-center gap-2">
            <Zap size={24} /> Cryptocurrency
          </h1>
          <p className="text-gray-400 text-sm">
            Analyze 24/7 digital asset markets. Search any crypto pair (e.g., PEPE-USD).
          </p>
        </div>
        
        <form onSubmit={handleSearch} className="relative w-full md:w-96">
          <TickerSearch 
            value={query} 
            onChange={setQuery} 
            className="w-full" 
            placeholder="Search crypto (e.g. BTC-USD)..."
          />
        </form>
      </div>

      <div className="space-y-12">
        {filteredMarkets.length === 0 ? (
          <div className="text-center py-12 text-gray-400 bg-gray-900/30 rounded-2xl border border-white/5">
            No predefined coins found for "{query}". 
            <br/><br/>
            Press <strong className="text-white">Enter</strong> to search for this symbol on the dashboard anyway!
          </div>
        ) : (
          filteredMarkets.map((market) => (
          <div key={market.category} className="space-y-6">
            <div className="flex items-center gap-3 border-b border-brand-500/10 pb-4">
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
                <div key={group.name} className="card bg-gray-900/40 border border-brand-500/5">
                  <h3 className="font-semibold text-gray-300 mb-4 flex items-center gap-2">
                    {group.name}
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {group.stocks.map((stock) => (
                      <button
                        key={stock.ticker}
                        onClick={() => handleStockClick(stock.ticker)}
                        className="flex items-center justify-between p-3 rounded-xl bg-black/20 hover:bg-brand-600/20 border border-transparent hover:border-brand-500/30 transition-all text-left group"
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
