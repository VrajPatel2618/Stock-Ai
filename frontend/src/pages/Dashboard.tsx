import { useState, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Search, TrendingUp, TrendingDown, Minus, RefreshCw, Activity } from 'lucide-react'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, LineChart, Line, Legend, ComposedChart, Bar } from 'recharts'
import api from '../api/client'

// Custom Candlestick Shape for Recharts
const Candlestick = (props: any) => {
  const { x, y, width, height, payload } = props;
  const { open, close, low, high } = payload;
  const isGrowing = close >= open;
  const color = isGrowing ? '#34d399' : '#f87171'; // emerald-400 : red-400
  
  const ratio = Math.abs(high - low);
  if (ratio === 0) return null;
  const pixelPerValue = height / ratio;
  
  const yHigh = y;
  const yLow = y + height;
  
  const yOpen = yHigh + (high - open) * pixelPerValue;
  const yClose = yHigh + (high - close) * pixelPerValue;
  
  const bodyTop = isGrowing ? yClose : yOpen;
  const bodyBottom = isGrowing ? yOpen : yClose;
  const bodyHeight = Math.max(1, bodyBottom - bodyTop);
  const halfWidth = width / 2;

  return (
    <g stroke={color} fill={color} strokeWidth="1.5">
      <line x1={x + halfWidth} y1={yHigh} x2={x + halfWidth} y2={yLow} />
      <rect x={x} y={bodyTop} width={width} height={bodyHeight} />
    </g>
  );
};

interface RangeData { low: number; high: number; change: number; target: number }
interface PredictResult {
  ticker: string; currentPrice: number; confidence: number; sentiment: string
  historicalData: { date: string; close: number }[]
  todayRange: RangeData; weekRange: RangeData; monthRange: RangeData
  sixMonthRange: RangeData; yearRange: RangeData
  featureImportance?: { Price: number; Volume: number; Sentiment: number }
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
  const location = useLocation()
  const navigate = useNavigate()
  const [ticker, setTicker] = useState(location.state?.searchTicker || '')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [stockInfo, setStockInfo] = useState<StockInfo | null>(null)
  const [result, setResult] = useState<PredictResult | null>(null)
  const [backtestResult, setBacktestResult] = useState<any | null>(null)
  const [backtesting, setBacktesting] = useState(false)
  const [chartType, setChartType] = useState<'line' | 'candle'>('line')

  const handleBacktest = async () => {
    if (!ticker.trim()) return
    setBacktesting(true)
    try {
      const res = await api.post('/backtest', { ticker: ticker.toUpperCase() })
      setBacktestResult(res.data)
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to run backtest')
    } finally {
      setBacktesting(false)
    }
  }

  const analyze = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!ticker.trim()) return
    setLoading(true); setError(''); setResult(null); setStockInfo(null); setBacktestResult(null)
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

  useEffect(() => {
    if (location.state?.searchTicker) {
      // Create a synthetic event or just call an extracted function, but since analyze expects an event, 
      // we'll bypass the event.preventDefault by passing a dummy object or extracting the logic.
      const fetchInitial = async () => {
        const t = location.state.searchTicker
        setLoading(true); setError(''); setResult(null); setStockInfo(null); setBacktestResult(null)
        try {
          const [infoRes, predRes] = await Promise.all([
            api.get(`/stock/${t.toUpperCase()}`),
            api.post('/predict', { ticker: t.toUpperCase(), days: 365 }),
          ])
          setStockInfo(infoRes.data)
          setResult(predRes.data)
        } catch (err: any) {
          setError(err.response?.data?.error || 'Failed to fetch data')
        } finally {
          setLoading(false)
        }
        // clear the state so it doesn't re-fetch on refresh
        navigate('/dashboard', { replace: true, state: {} })
      }
      fetchInitial()
    }
  }, [location.state?.searchTicker, navigate])

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
                <div className="flex items-center gap-4">
                  <div className="flex items-center bg-white/5 rounded-lg p-1">
                    <button onClick={() => setChartType('line')} className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${chartType === 'line' ? 'bg-brand-600 text-white' : 'text-gray-400 hover:text-white'}`}>Line</button>
                    <button onClick={() => setChartType('candle')} className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${chartType === 'candle' ? 'bg-brand-600 text-white' : 'text-gray-400 hover:text-white'}`}>Candle</button>
                  </div>
                  <div className="flex items-center gap-2 text-sm hidden sm:flex">
                    <SentimentIcon size={16} className={sentimentColor} />
                    <span className={sentimentColor}>{result.confidence.toFixed(0)}% confidence</span>
                  </div>
                </div>
              </div>
              <ResponsiveContainer width="100%" height={280}>
                {chartType === 'line' ? (
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
                ) : (
                  <ComposedChart data={result.historicalData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" />
                    <XAxis dataKey="date" tick={{ fill: '#6b7280', fontSize: 11 }} tickFormatter={(v) => v.slice(5)} interval={14} />
                    <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} domain={['auto', 'auto']} tickFormatter={(v) => `${sym}${Number(v).toFixed(0)}`} />
                    <Tooltip
                      contentStyle={{ background: '#111827', border: '1px solid #ffffff15', borderRadius: 12 }}
                      labelStyle={{ color: '#9ca3af' }}
                      // eslint-disable-next-line @typescript-eslint/no-explicit-any
                      formatter={((v: any, name: any, props: any) => {
                        if (name === 'OHLC') {
                          const { open, high, low, close } = props.payload;
                          return [`O: ${sym}${open.toFixed(2)} H: ${sym}${high.toFixed(2)} L: ${sym}${low.toFixed(2)} C: ${sym}${close.toFixed(2)}`, ''];
                        }
                        return [v, name];
                      }) as any}
                    />
                    <Bar dataKey={(d) => [d.low, d.high]} shape={<Candlestick />} name="OHLC" />
                  </ComposedChart>
                )}
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


            {/* Backtesting Engine */}
            <div className="card lg:col-span-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold flex items-center gap-2"><Activity size={18} className="text-emerald-400" /> Backtesting Engine</h3>
                <button onClick={handleBacktest} disabled={backtesting} className="btn-secondary text-sm py-1.5 px-3">
                  {backtesting ? 'Running Backtest...' : 'Run Backtest'}
                </button>
              </div>
              
              {!backtestResult && !backtesting && (
                <div className="text-center py-8 text-gray-500 text-sm">
                  Run a backtest to simulate past predictions and compare them against actual historical data to verify the LSTM's accuracy.
                </div>
              )}
              
              {backtestResult && (
                <div className="space-y-6 animate-in fade-in zoom-in duration-300">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-white/5 rounded-lg p-4">
                      <div className="text-xs text-gray-400">Accuracy (MAPE)</div>
                      <div className="text-2xl font-bold text-emerald-400">{backtestResult.accuracy}%</div>
                    </div>
                    <div className="bg-white/5 rounded-lg p-4">
                      <div className="text-xs text-gray-400">Error (RMSE)</div>
                      <div className="text-2xl font-bold text-red-400">{sym}{backtestResult.rmse}</div>
                    </div>
                  </div>
                  
                  <div className="h-[300px] w-full">
                    <ResponsiveContainer>
                      <LineChart data={backtestResult.dates.map((d: string, i: number) => ({
                        date: d.slice(5),
                        actual: backtestResult.actual[i],
                        predicted: backtestResult.predicted[i]
                      }))}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" />
                        <XAxis dataKey="date" tick={{ fill: '#6b7280', fontSize: 11 }} />
                        <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} domain={['auto', 'auto']} tickFormatter={(v) => `${sym}${Number(v).toFixed(0)}`} />
                        <Tooltip contentStyle={{ background: '#111827', border: '1px solid #ffffff15', borderRadius: 12 }} />
                        <Legend />
                        <Line type="monotone" dataKey="actual" name="Actual Price" stroke="#6b7280" strokeWidth={2} dot={false} />
                        <Line type="monotone" dataKey="predicted" name="AI Prediction" stroke="#0d9488" strokeWidth={2} dot={false} strokeDasharray="5 5" />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}
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
