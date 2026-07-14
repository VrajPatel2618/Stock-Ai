import { useState, useEffect } from 'react'
import { Trash2, TrendingUp, TrendingDown, RefreshCw, Plus } from 'lucide-react'
import api from '../api/client'
import StockSearchAutocomplete from '../components/StockSearchAutocomplete'
import { useAuthStore } from '../store/authStore'
import { Link } from 'react-router-dom'

export default function Watchlist() {
  const { token } = useAuthStore()
  const [watchlist, setWatchlist] = useState<any[]>([])
  const [prices, setPrices] = useState<Record<string, any>>({})
  const [newTicker, setNewTicker] = useState('')
  const [loading, setLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)

  const fetchWatchlist = async () => {
    try {
      const res = await api.get('/watchlist')
      setWatchlist(res.data.watchlist)
      refreshPrices(res.data.watchlist.map((w: any) => w.ticker))
    } catch {}
  }

  const refreshPrices = async (tickers: string[]) => {
    if (!tickers.length) return
    setRefreshing(true)
    try {
      const res = await api.post('/watchlist/prices', { tickers })
      const map: Record<string, any> = {}
      res.data.prices.forEach((p: any) => { map[p.ticker] = p })
      setPrices(map)
    } catch {}
    setRefreshing(false)
  }

  useEffect(() => { if (token) fetchWatchlist() }, [token])

  const add = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newTicker.trim()) return
    setLoading(true)
    try {
      await api.post('/watchlist', { ticker: newTicker.toUpperCase() })
      setNewTicker('')
      fetchWatchlist()
    } catch {}
    setLoading(false)
  }

  const remove = async (ticker: string) => {
    try {
      await api.delete('/watchlist', { data: { ticker } })
      setWatchlist(w => w.filter(i => i.ticker !== ticker))
    } catch {}
  }

  if (!token) return (
    <div className="max-w-xl mx-auto text-center py-24">
      <TrendingUp size={48} className="text-gray-700 mx-auto mb-4" />
      <h2 className="text-xl font-bold mb-2">Sign in to use Watchlist</h2>
      <p className="text-gray-400 mb-6">Track your favorite stocks with auto-refresh prices.</p>
      <Link to="/login" className="btn-primary">Sign In</Link>
    </div>
  )

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Watchlist</h1>
          <p className="text-gray-400 text-sm mt-1">Track your favorite stocks</p>
        </div>
        <button onClick={() => refreshPrices(watchlist.map(w => w.ticker))}
          disabled={refreshing} className="btn-ghost flex items-center gap-2 text-sm">
          <RefreshCw size={16} className={refreshing ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      <form onSubmit={add} className="flex gap-3">
        <div className="flex-1 max-w-xs">
          <StockSearchAutocomplete
            value={newTicker}
            onChange={(val) => setNewTicker(val.toUpperCase())}
            onSelect={(t) => setNewTicker(t)}
            placeholder="Add ticker (e.g. NVDA)"
          />
        </div>
        <button type="submit" disabled={loading} className="btn-primary flex items-center gap-2 disabled:opacity-50">
          <Plus size={16} /> Add
        </button>
      </form>

      {watchlist.length === 0 ? (
        <div className="card text-center py-16">
          <TrendingUp size={40} className="text-gray-700 mx-auto mb-3" />
          <p className="text-gray-500">Your watchlist is empty. Add some tickers above.</p>
        </div>
      ) : (
        <div className="card p-0 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-white/5">
                <th className="text-left text-xs text-gray-500 font-medium px-6 py-3">Ticker</th>
                <th className="text-right text-xs text-gray-500 font-medium px-6 py-3">Price</th>
                <th className="text-right text-xs text-gray-500 font-medium px-6 py-3">Change</th>
                <th className="text-right text-xs text-gray-500 font-medium px-6 py-3">Added</th>
                <th className="px-6 py-3" />
              </tr>
            </thead>
            <tbody>
              {watchlist.map((item) => {
                const p = prices[item.ticker]
                const pos = p?.isPositive
                return (
                  <tr key={item.ticker} className="border-b border-white/5 last:border-0 hover:bg-white/5 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        {pos !== undefined && (pos
                          ? <TrendingUp size={16} className="text-emerald-400" />
                          : <TrendingDown size={16} className="text-red-400" />)}
                        <span className="font-bold">{item.ticker}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right font-semibold">
                      {p ? `$${p.price.toFixed(2)}` : '—'}
                    </td>
                    <td className={`px-6 py-4 text-right text-sm font-semibold ${pos ? 'text-emerald-400' : pos === false ? 'text-red-400' : 'text-gray-500'}`}>
                      {p ? `${pos ? '+' : ''}${p.changePercent.toFixed(2)}%` : '—'}
                    </td>
                    <td className="px-6 py-4 text-right text-xs text-gray-500">
                      {new Date(item.added_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button onClick={() => remove(item.ticker)}
                        className="text-gray-600 hover:text-red-400 transition-colors">
                        <Trash2 size={16} />
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
