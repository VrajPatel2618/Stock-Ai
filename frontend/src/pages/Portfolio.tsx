import { useState, useEffect } from 'react'
import { Plus, Trash2, Briefcase, RefreshCw, LogIn } from 'lucide-react'
import { Link } from 'react-router-dom'
import api from '../api/client'
import { useAuthStore } from '../store/authStore'

interface Holding {
  id: number; ticker: string; shares: number; avg_price: number
  currentPrice: number | null; currentValue: number | null
  totalCost: number; gainLoss: number | null; gainLossPct: number | null
  companyName: string; currency: string
}
interface Summary {
  totalCost: number; totalValue: number; totalGainLoss: number
  totalGainLossPct: number; count: number; virtualBalance: number
}

export default function Portfolio() {
  const { token } = useAuthStore()
  const [holdings, setHoldings] = useState<Holding[]>([])
  const [summary, setSummary] = useState<Summary | null>(null)
  const [form, setForm] = useState({ ticker: '', action: 'BUY', shares: '', price: '' })
  const [loading, setLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState('')

  const fetchPortfolio = async (silent = false) => {
    if (!silent) setRefreshing(true)
    try {
      const res = await api.get('/portfolio')
      setHoldings(res.data.holdings)
      setSummary(res.data.summary)
    } catch {}
    setRefreshing(false)
  }

  useEffect(() => { if (token) fetchPortfolio() }, [token])

  const trade = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.ticker || !form.shares || !form.price) return setError('All fields required')
    if (+form.shares <= 0 || +form.price <= 0) return setError('Shares and price must be positive')
    setLoading(true); setError('')
    try {
      await api.post('/trade', { ticker: form.ticker.toUpperCase(), action: form.action, shares: +form.shares, price: +form.price })
      setForm({ ticker: '', action: 'BUY', shares: '', price: '' })
      fetchPortfolio()
    } catch (err: any) {
      setError(err.response?.data?.error || 'Trade failed')
    }
    setLoading(false)
  }

  const remove = async (ticker: string) => {
    try {
      await api.delete('/portfolio', { data: { ticker } })
      setHoldings(h => h.filter(x => x.ticker !== ticker))
      fetchPortfolio(true)
    } catch {}
  }

  const sym = (currency: string) => currency === 'INR' ? '₹' : '$'

  if (!token) return (
    <div className="max-w-xl mx-auto text-center py-24">
      <Briefcase size={48} className="text-gray-700 mx-auto mb-4" />
      <h2 className="text-xl font-bold mb-2">Sign in to track your portfolio</h2>
      <p className="text-gray-400 mb-6">Your holdings are saved to your account — not just this browser.</p>
      <Link to="/login" className="btn-primary inline-flex items-center gap-2"><LogIn size={16} /> Sign In</Link>
    </div>
  )

  const gainColor = (v: number | null) => v === null ? 'text-gray-400' : v >= 0 ? 'text-emerald-400' : 'text-red-400'
  const gainSign = (v: number | null) => v !== null && v >= 0 ? '+' : ''

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Portfolio</h1>
          <p className="text-gray-400 text-sm mt-1">Your holdings with live P&amp;L — saved to your account</p>
        </div>
        <button onClick={() => fetchPortfolio()} disabled={refreshing}
          className="btn-ghost flex items-center gap-2 text-sm">
          <RefreshCw size={15} className={refreshing ? 'animate-spin' : ''} /> Refresh
        </button>
      </div>

      {/* Summary cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {[
            { label: 'Virtual Cash Balance', value: `$${summary.virtualBalance?.toLocaleString('en-US', { minimumFractionDigits: 2 }) || '0.00'}`, cls: 'text-brand-400' },
            { label: 'Total Invested', value: `$${summary.totalCost.toLocaleString('en-US', { minimumFractionDigits: 2 })}`, cls: 'text-white' },
            { label: 'Portfolio Value', value: `$${summary.totalValue.toLocaleString('en-US', { minimumFractionDigits: 2 })}`, cls: 'text-white' },
            { label: 'Total Gain/Loss', value: `${gainSign(summary.totalGainLoss)}$${Math.abs(summary.totalGainLoss).toFixed(2)}`, cls: gainColor(summary.totalGainLoss) },
            { label: 'Return %', value: `${gainSign(summary.totalGainLossPct)}${summary.totalGainLossPct.toFixed(2)}%`, cls: gainColor(summary.totalGainLoss) },
          ].map(({ label, value, cls }) => (
            <div key={label} className="card">
              <div className="text-xs text-gray-500 mb-1">{label}</div>
              <div className={`text-lg font-bold ${cls}`}>{value}</div>
            </div>
          ))}
        </div>
      )}

      {/* Trade form */}
      <form onSubmit={trade} className="card space-y-4">
        <h3 className="font-semibold">Paper Trade Simulator</h3>
        {error && <div className="text-red-400 text-sm bg-red-500/10 px-3 py-2 rounded-lg">{error}</div>}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Ticker</label>
            <input className="input-field" placeholder="AAPL" value={form.ticker}
              onChange={(e) => setForm({ ...form, ticker: e.target.value.toUpperCase() })} />
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Action</label>
            <select className="input-field" value={form.action} onChange={(e) => setForm({ ...form, action: e.target.value })}>
              <option value="BUY">BUY</option>
              <option value="SELL">SELL</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Shares</label>
            <input className="input-field" type="number" min="0.001" step="any" placeholder="10"
              value={form.shares} onChange={(e) => setForm({ ...form, shares: e.target.value })} />
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Price</label>
            <input className="input-field" type="number" min="0.01" step="any" placeholder="150.00"
              value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} />
          </div>
        </div>
        <button type="submit" disabled={loading} className={`flex items-center gap-2 justify-center w-full py-3 rounded-xl font-medium transition-colors disabled:opacity-50 ${form.action === 'BUY' ? 'bg-brand-600 hover:bg-brand-500 text-white' : 'bg-red-600 hover:bg-red-500 text-white'}`}>
          {loading ? <RefreshCw size={15} className="animate-spin" /> : <Briefcase size={15} />}
          {loading ? 'Processing…' : `Execute ${form.action} Order`}
        </button>
      </form>

      {/* Holdings table */}
      {holdings.length > 0 ? (
        <div className="card p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/5">
                  {['Stock', 'Shares', 'Avg Price', 'Current', 'Invested', 'Value', 'Gain/Loss', ''].map(h => (
                    <th key={h} className="text-left text-xs text-gray-500 font-medium px-4 py-3 whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {holdings.map((h) => (
                  <tr key={h.ticker} className="border-b border-white/5 last:border-0 hover:bg-white/5 transition-colors">
                    <td className="px-4 py-4">
                      <div className="font-bold">{h.ticker}</div>
                      <div className="text-xs text-gray-500 truncate max-w-28">{h.companyName}</div>
                    </td>
                    <td className="px-4 py-4 text-gray-300">{h.shares}</td>
                    <td className="px-4 py-4 text-gray-300">{sym(h.currency)}{h.avg_price.toFixed(2)}</td>
                    <td className="px-4 py-4">
                      {h.currentPrice
                        ? <span className="font-semibold">{sym(h.currency)}{h.currentPrice.toFixed(2)}</span>
                        : <span className="text-gray-600">—</span>}
                    </td>
                    <td className="px-4 py-4 text-gray-300">{sym(h.currency)}{h.totalCost.toFixed(2)}</td>
                    <td className="px-4 py-4 font-semibold">
                      {h.currentValue ? `${sym(h.currency)}${h.currentValue.toFixed(2)}` : '—'}
                    </td>
                    <td className="px-4 py-4">
                      {h.gainLoss !== null ? (
                        <div>
                          <div className={`font-semibold text-sm ${gainColor(h.gainLoss)}`}>
                            {gainSign(h.gainLoss)}{sym(h.currency)}{Math.abs(h.gainLoss).toFixed(2)}
                          </div>
                          <div className={`text-xs ${gainColor(h.gainLossPct)}`}>
                            {gainSign(h.gainLossPct)}{h.gainLossPct?.toFixed(2)}%
                          </div>
                        </div>
                      ) : <span className="text-gray-600">—</span>}
                    </td>
                    <td className="px-4 py-4">
                      <button onClick={() => remove(h.ticker)}
                        className="text-gray-600 hover:text-red-400 transition-colors">
                        <Trash2 size={15} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="card text-center py-16">
          <Briefcase size={40} className="text-gray-700 mx-auto mb-3" />
          <p className="text-gray-500">No positions yet. Add your first holding above.</p>
          <p className="text-gray-600 text-xs mt-1">Indian stocks: use .NS suffix (e.g. RELIANCE.NS)</p>
        </div>
      )}
    </div>
  )
}
