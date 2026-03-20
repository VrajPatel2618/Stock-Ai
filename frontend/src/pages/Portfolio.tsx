import { useState } from 'react'
import { Plus, Trash2, Briefcase } from 'lucide-react'

interface Holding { ticker: string; shares: number; avgPrice: number; currentPrice?: number }

export default function Portfolio() {
  const [holdings, setHoldings] = useState<Holding[]>(() => {
    try { return JSON.parse(localStorage.getItem('portfolio') || '[]') } catch { return [] }
  })
  const [form, setForm] = useState({ ticker: '', shares: '', avgPrice: '' })
  const [error, setError] = useState('')

  const save = (h: Holding[]) => {
    setHoldings(h)
    localStorage.setItem('portfolio', JSON.stringify(h))
  }

  const add = (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.ticker || !form.shares || !form.avgPrice) return setError('All fields required')
    const existing = holdings.findIndex(h => h.ticker === form.ticker.toUpperCase())
    const newH = { ticker: form.ticker.toUpperCase(), shares: +form.shares, avgPrice: +form.avgPrice }
    if (existing >= 0) {
      const updated = [...holdings]; updated[existing] = newH; save(updated)
    } else {
      save([...holdings, newH])
    }
    setForm({ ticker: '', shares: '', avgPrice: '' }); setError('')
  }

  const remove = (ticker: string) => save(holdings.filter(h => h.ticker !== ticker))

  const totalCost = holdings.reduce((s, h) => s + h.shares * h.avgPrice, 0)

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Portfolio</h1>
        <p className="text-gray-400 text-sm mt-1">Track your holdings and performance</p>
      </div>

      {/* Summary */}
      <div className="card">
        <div className="flex items-center gap-3 mb-2">
          <Briefcase size={20} className="text-brand-400" />
          <span className="font-semibold">Total Invested</span>
        </div>
        <div className="text-3xl font-bold">${totalCost.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
        <div className="text-sm text-gray-400 mt-1">{holdings.length} position{holdings.length !== 1 ? 's' : ''}</div>
      </div>

      {/* Add form */}
      <form onSubmit={add} className="card space-y-4">
        <h3 className="font-semibold">Add / Update Position</h3>
        {error && <div className="text-red-400 text-sm">{error}</div>}
        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Ticker</label>
            <input className="input-field" placeholder="AAPL" value={form.ticker}
              onChange={(e) => setForm({ ...form, ticker: e.target.value.toUpperCase() })} />
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Shares</label>
            <input className="input-field" type="number" placeholder="10" value={form.shares}
              onChange={(e) => setForm({ ...form, shares: e.target.value })} />
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Avg Price ($)</label>
            <input className="input-field" type="number" step="0.01" placeholder="150.00" value={form.avgPrice}
              onChange={(e) => setForm({ ...form, avgPrice: e.target.value })} />
          </div>
        </div>
        <button type="submit" className="btn-primary flex items-center gap-2">
          <Plus size={16} /> Add Position
        </button>
      </form>

      {/* Holdings table */}
      {holdings.length > 0 && (
        <div className="card p-0 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/5">
                {['Ticker', 'Shares', 'Avg Price', 'Total Cost', ''].map(h => (
                  <th key={h} className={`text-xs text-gray-500 font-medium px-6 py-3 ${h === '' ? '' : 'text-left'}`}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {holdings.map((h) => (
                <tr key={h.ticker} className="border-b border-white/5 last:border-0 hover:bg-white/5 transition-colors">
                  <td className="px-6 py-4 font-bold">{h.ticker}</td>
                  <td className="px-6 py-4 text-gray-300">{h.shares}</td>
                  <td className="px-6 py-4 text-gray-300">${h.avgPrice.toFixed(2)}</td>
                  <td className="px-6 py-4 font-semibold">${(h.shares * h.avgPrice).toFixed(2)}</td>
                  <td className="px-6 py-4 text-right">
                    <button onClick={() => remove(h.ticker)} className="text-gray-600 hover:text-red-400 transition-colors">
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {holdings.length === 0 && (
        <div className="card text-center py-16">
          <Briefcase size={40} className="text-gray-700 mx-auto mb-3" />
          <p className="text-gray-500">No positions yet. Add your first holding above.</p>
        </div>
      )}
    </div>
  )
}
