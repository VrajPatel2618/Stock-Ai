import { useState } from 'react'
import { Search, TrendingUp, TrendingDown, Minus, RefreshCw } from 'lucide-react'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import api from '../api/client'

interface RangeData { low: number; high: number; change: number; target: number }
interface PredictResult {
  ticker: string; currentPrice: number; confidence: number; sentiment: string
  historicalData: { date: string; close: number }[]
  todayRange: RangeData; weekRange: RangeData; monthRange: RangeData
  sixMonthRange: RangeData; yearRange: RangeData
}
interface StockInfo {
  companyName: string; currentPrice: number; change: number; changePercent: number
  marketCap: number; peRatio: number; fiftyTwoWeekHigh: number; fiftyTwoWeekLow: number
  volume: number; sector: string; currency: string
}

const RangeRow = ({ label, data, sym }: { label: string; data: RangeData; sym: string }) => {
  const pos = data.change >= 0
  return (
    <div className="flex items-center justify-between py-3 border-b border-white/5 last:border-0">
      <span className="text-sm text-gray-400">{label}</span>
      <div className="text-right">
        <div className="text-sm font-medium text-white">{sym}{data.low.toFixed(2)} – {sym}{data.high.toFixed(2)}</div>
        <div className={`text-xs font-semibold ${pos ? 'text-emerald-400' : 'text-red-400'}`}>
          {pos ? '+' : ''}{data.change.toFixed(2)}%
        </div>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [ticker, setTicker] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [stockInfo, setStockInfo] = useState<StockInfo | null>(null)
  const [result, setResult] = useState<PredictResult | null>(null)

  const analyze = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!ticker.trim()) return
    setLoading(true); setError(''); setResult(null); setStockInfo(null)
    try {
      const [infoRes, predRes] = await Promise.all([
        api.get(`/stock/${ticker.toUpperCase()}`),
        api.post('/predict', { ticker: ticker.toUpperCase(), days: 365 }),
      ])
      setStockInfo(infoRes.data)
      setResult(predRes.data)
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to fetch data')
    } finally {
      setLoading(false)
    }
  }

  const chartData = result?.historicalData.map(d => ({ date: d.date, price: d.close })) ?? []
  const SentimentIcon = result?.sentiment === 'bullish' ? TrendingUp : result?.sentiment === 'bearish' ? TrendingDown : Minus
  const sentimentColor = result?.sentiment === 'bullish' ? 'text-emerald-400' : result?.sentiment === 'bearish' ? 'text-red-400' : 'text-gray-400'
  const sym = stockInfo?.currency === 'INR' ? '₹' : '$'

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Market Analysis</h1>
        <p className="text-gray-400 text-sm mt-1">AI-powered stock predictions with LSTM neural networks</p>
      </div>

      <form onSubmit={analyze} className="flex gap-3">
        <div className="relative flex-1 max-w-md">
          <Search size={18} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            className="input-field pl-10"
            placeholder="Enter ticker (e.g. AAPL, RELIANCE.NS, TSLA)"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
          />
        </div>
        <button type="submit" disabled={loading} className="btn-primary flex items-center gap-2 disabled:opacity-50">
          {loading ? <RefreshCw size={16} className="animate-spin" /> : <Search size={16} />}
          {loading ? 'Analyzing…' : 'Analyze'}
        </button>
      </form>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-sm rounded-xl px-4 py-3">{error}</div>
      )}

      {stockInfo && result && (
        <>
          <div className="card">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-3 mb-1">
                  <h2 className="text-2xl font-bold">{result.ticker}</h2>
                  <span className={`badge-${result.sentiment}`}>{result.sentiment}</span>
                  {sym === '₹' && <span className="text-xs text-orange-400 bg-orange-400/10 px-2 py-0.5 rounded-full">🇮🇳 NSE/BSE</span>}
                </div>
                <p className="text-gray-400 text-sm">{stockInfo.companyName} · {stockInfo.sector}</p>
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold">{sym}{stockInfo.currentPrice.toFixed(2)}</div>
                <div className={`text-sm font-semibold ${stockInfo.change >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {stockInfo.change >= 0 ? '+' : ''}{sym}{Math.abs(stockInfo.change).toFixed(2)} ({stockInfo.changePercent.toFixed(2)}%)
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t border-white/5">
              {[
                { label: 'Market Cap', value: stockInfo.marketCap ? `${sym}${(stockInfo.marketCap / 1e9).toFixed(2)}B` : 'N/A' },
                { label: 'P/E Ratio', value: stockInfo.peRatio ? stockInfo.peRatio.toFixed(2) : 'N/A' },
                { label: '52W High', value: `${sym}${stockInfo.fiftyTwoWeekHigh.toFixed(2)}` },
                { label: '52W Low', value: `${sym}${stockInfo.fiftyTwoWeekLow.toFixed(2)}` },
              ].map(({ label, value }) => (
                <div key={label}>
                  <div className="text-xs text-gray-500 mb-1">{label}</div>
                  <div className="font-semibold">{value}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="grid lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 card">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold">90-Day Price History</h3>
                <div className="flex items-center gap-2 text-sm">
                  <SentimentIcon size={16} className={sentimentColor} />
                  <span className={sentimentColor}>{result.confidence.toFixed(0)}% confidence</span>
                </div>
              </div>
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="priceGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#0d9488" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#0d9488" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" />
                  <XAxis dataKey="date" tick={{ fill: '#6b7280', fontSize: 11 }}
                    tickFormatter={(v) => v.slice(5)} interval={14} />
                  <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} domain={['auto', 'auto']}
                    tickFormatter={(v) => `${sym}${Number(v).toFixed(0)}`} />
                  <Tooltip
                    contentStyle={{ background: '#111827', border: '1px solid #ffffff15', borderRadius: 12 }}
                    labelStyle={{ color: '#9ca3af' }}
                    formatter={(v: any) => [`${sym}${Number(v).toFixed(2)}`, 'Price']}
                  />
                  <Area type="monotone" dataKey="price" stroke="#0d9488" strokeWidth={2} fill="url(#priceGrad)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            <div className="card">
              <h3 className="font-semibold mb-4">AI Forecast Ranges</h3>
              <RangeRow label="Today" data={result.todayRange} sym={sym} />
              <RangeRow label="1 Week" data={result.weekRange} sym={sym} />
              <RangeRow label="1 Month" data={result.monthRange} sym={sym} />
              <RangeRow label="6 Months" data={result.sixMonthRange} sym={sym} />
              <RangeRow label="1 Year" data={result.yearRange} sym={sym} />
            </div>
          </div>
        </>
      )}

      {!result && !loading && (
        <div className="card text-center py-16">
          <TrendingUp size={48} className="text-gray-700 mx-auto mb-4" />
          <p className="text-gray-500">Enter a stock ticker above to get AI-powered predictions</p>
          <p className="text-gray-600 text-xs mt-2">Indian stocks: use .NS suffix (e.g. RELIANCE.NS, TCS.NS)</p>
        </div>
      )}
    </div>
  )
}
