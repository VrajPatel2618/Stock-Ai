import { useState, useEffect } from 'react'
import { RefreshCw } from 'lucide-react'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import api from '../api/client'

const COMMODITIES = [
  { symbol: 'GC=F', name: 'Gold', emoji: '🥇' },
  { symbol: 'SI=F', name: 'Silver', emoji: '🥈' },
  { symbol: 'CL=F', name: 'Crude Oil', emoji: '🛢️' },
  { symbol: 'NG=F', name: 'Natural Gas', emoji: '⚡' },
]

export default function Commodities() {
  const [selected, setSelected] = useState('GC=F')
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<any>(null)
  const [prices, setPrices] = useState<Record<string, any>>({})

  useEffect(() => {
    COMMODITIES.forEach(async ({ symbol }) => {
      try {
        const res = await api.get(`/commodity/${symbol}`)
        setPrices(p => ({ ...p, [symbol]: res.data }))
      } catch {}
    })
  }, [])

  const analyze = async (symbol: string) => {
    setSelected(symbol); setLoading(true); setData(null)
    try {
      const res = await api.post('/commodity/predict', { symbol })
      setData(res.data)
    } catch {}
    setLoading(false)
  }

  useEffect(() => { analyze(selected) }, [])

  const chartData = data?.historicalData?.map((d: any) => ({ date: d.date, price: d.close })) ?? []

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Commodity Forecast</h1>
        <p className="text-gray-400 text-sm mt-1">AI predictions for global commodities</p>
      </div>

      {/* Commodity cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {COMMODITIES.map(({ symbol, name, emoji }) => {
          const p = prices[symbol]
          const pos = p?.changePercent >= 0
          return (
            <button key={symbol} onClick={() => analyze(symbol)}
              className={`card text-left transition-all hover:border-brand-500/30 ${selected === symbol ? 'border-brand-500/50 bg-brand-600/10' : ''}`}>
              <div className="text-2xl mb-2">{emoji}</div>
              <div className="font-semibold text-sm">{name}</div>
              {p ? (
                <>
                  <div className="text-lg font-bold mt-1">${p.currentPrice?.toFixed(2)}</div>
                  <div className={`text-xs font-semibold ${pos ? 'text-emerald-400' : 'text-red-400'}`}>
                    {pos ? '+' : ''}{p.changePercent?.toFixed(2)}%
                  </div>
                </>
              ) : <div className="text-gray-600 text-sm mt-1">Loading…</div>}
            </button>
          )
        })}
      </div>

      {loading && (
        <div className="card flex items-center justify-center py-16">
          <RefreshCw size={24} className="animate-spin text-brand-400" />
          <span className="ml-3 text-gray-400">Running AI forecast…</span>
        </div>
      )}

      {data && !loading && (
        <div className="grid lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold">90-Day Price History</h3>
              <span className="text-sm text-gray-400">Current: <span className="text-white font-semibold">${data.currentPrice?.toFixed(2)}</span></span>
            </div>
            <ResponsiveContainer width="100%" height={280}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="commGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" />
                <XAxis dataKey="date" tick={{ fill: '#6b7280', fontSize: 11 }} tickFormatter={(v) => v.slice(5)} interval={14} />
                <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} domain={['auto', 'auto']} tickFormatter={(v) => `$${v.toFixed(0)}`} />
                <Tooltip contentStyle={{ background: '#111827', border: '1px solid #ffffff15', borderRadius: 12 }}
                  formatter={(v: any) => [`$${Number(v).toFixed(2)}`, 'Price']} />
                <Area type="monotone" dataKey="price" stroke="#f59e0b" strokeWidth={2} fill="url(#commGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="card">
            <h3 className="font-semibold mb-4">30-Day Forecast</h3>
            <div className="text-center py-6">
              <div className="text-4xl font-bold text-amber-400">${data.prediction30Day?.toFixed(2)}</div>
              <div className="text-gray-400 text-sm mt-1">30-Day Target</div>
              {data.ranges && (
                <div className={`mt-3 text-sm font-semibold ${data.ranges.monthRange?.change >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                  {data.ranges.monthRange?.change >= 0 ? '+' : ''}{data.ranges.monthRange?.change?.toFixed(2)}% expected
                </div>
              )}
            </div>
            {data.ranges && (
              <div className="space-y-3 mt-4 pt-4 border-t border-white/5">
                {[
                  { label: 'Today', r: data.ranges.todayRange },
                  { label: '1 Week', r: data.ranges.weekRange },
                  { label: '1 Month', r: data.ranges.monthRange },
                ].map(({ label, r }) => r && (
                  <div key={label} className="flex justify-between text-sm">
                    <span className="text-gray-400">{label}</span>
                    <span className={r.change >= 0 ? 'text-emerald-400' : 'text-red-400'}>
                      {r.change >= 0 ? '+' : ''}{r.change?.toFixed(2)}%
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
