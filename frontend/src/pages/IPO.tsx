import { useState, useEffect } from 'react'
import { RefreshCw, TrendingUp, TrendingDown, Minus, ExternalLink, Zap, Globe, ChevronRight } from 'lucide-react'
import api from '../api/client'

const REGIONS = [
  { id: 'us',     label: '🇺🇸 USA',    desc: 'Nasdaq / NYSE' },
  { id: 'india',  label: '🇮🇳 India',  desc: 'NSE / BSE' },
]

const SECTORS: Record<string, string[]> = {
  us: [
    'Technology', 'Artificial Intelligence', 'Fintech', 'Healthcare', 'Biotechnology',
    'Energy', 'Clean Energy', 'Consumer Discretionary', 'Consumer Staples',
    'Industrials', 'Real Estate', 'Materials', 'Utilities', 'Communication Services',
    'Aerospace & Defense', 'Automotive', 'Retail', 'SaaS', 'Cybersecurity',
  ],
  india: [
    'Technology', 'Fintech', 'Banking & Finance', 'Insurance', 'NBFC',
    'Healthcare', 'Pharmaceuticals', 'Consumer Goods', 'FMCG',
    'Infrastructure', 'Real Estate', 'Energy', 'Oil & Gas', 'Renewables',
    'Retail', 'E-Commerce', 'Manufacturing', 'Defence', 'Agri & Food',
    'Chemicals', 'Logistics', 'Media & Entertainment', 'Telecom',
  ],
}

interface IPO {
  company: string; ticker: string; exchange: string; status: string
  issuePrice: number; sharesOffered: number; offerAmount: number
  date: string; region: string; currency: string
  sentiment: number; sentiment_label: string; url: string; source: string; summary?: string
}

interface Prediction {
  company: string; sector: string; recommendation: string; recommendation_sentiment: string
  issuePrice: number; listingPriceEstimate: number | null
  predictions: { day1: number; week1: number; month1: number; year1: number }
  peerAnalysis: { avgPE: number; avgBeta: number; sectorYTD: number; peers: any[] }
}

const STATUS_STYLE: Record<string, string> = {
  Upcoming: 'bg-brand-600/20 text-brand-400 border-brand-500/30',
  Filed:    'bg-amber-500/20 text-amber-400 border-amber-500/30',
  Priced:   'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  News:     'bg-purple-500/20 text-purple-400 border-purple-500/30',
  Withdrawn:'bg-red-500/20 text-red-400 border-red-500/30',
}

function SentBadge({ label }: { label: string }) {
  const Icon = label === 'bullish' ? TrendingUp : label === 'bearish' ? TrendingDown : Minus
  const cls = label === 'bullish' ? 'badge-bullish' : label === 'bearish' ? 'badge-bearish' : 'badge-neutral'
  return <span className={`${cls} inline-flex items-center gap-1`}><Icon size={10} />{label}</span>
}

function PredRow({ label, value, base, currency }: { label: string; value: number; base?: number; currency: string }) {
  const pos = value >= 0
  const price = base && base > 0 ? base * (1 + value / 100) : null
  return (
    <div className="flex items-center justify-between py-2.5 border-b border-white/5 last:border-0">
      <span className="text-sm text-gray-400">{label}</span>
      <div className="text-right">
        <span className={`font-semibold text-sm ${pos ? 'text-emerald-400' : 'text-red-400'}`}>
          {pos ? '+' : ''}{value.toFixed(2)}%
        </span>
        {price && <div className="text-xs text-gray-500">{currency}{price.toFixed(2)}</div>}
      </div>
    </div>
  )
}

function formatAmount(amt: number, currency: string) {
  if (!amt) return '—'
  if (amt >= 1e9) return `${currency}${(amt / 1e9).toFixed(2)}B`
  if (amt >= 1e6) return `${currency}${(amt / 1e6).toFixed(1)}M`
  return `${currency}${amt.toLocaleString()}`
}

export default function IPOPage() {
  const [region, setRegion] = useState('us')
  const [ipos, setIpos] = useState<IPO[]>([])
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState<IPO | null>(null)
  const [sector, setSector] = useState('Technology')
  const [issuePrice, setIssuePrice] = useState('')
  const [prediction, setPrediction] = useState<Prediction | null>(null)
  const [predLoading, setPredLoading] = useState(false)
  const [filter, setFilter] = useState('All')
  const [showLimit, setShowLimit] = useState(5)

  const fetchIPOs = async (r: string) => {
    setLoading(true); setIpos([]); setSelected(null); setPrediction(null)
    try {
      const res = await api.get(`/ipo?region=${r}`)
      setIpos(res.data.ipos || [])
    } catch {}
    setLoading(false)
  }

  useEffect(() => {
    setSector(SECTORS[region]?.[0] || 'Technology')
    fetchIPOs(region)
  }, [region])

  const runPrediction = async () => {
    if (!selected) return
    setPredLoading(true); setPrediction(null)
    try {
      const res = await api.post('/ipo/predict', {
        company: selected.company, sector,
        sentiment: selected.sentiment,
        issuePrice: issuePrice ? +issuePrice : selected.issuePrice || 0,
        region,
      })
      setPrediction(res.data)
    } catch {}
    setPredLoading(false)
  }

  const statuses = ['All', ...Array.from(new Set(ipos.map(i => i.status)))]
  const filtered = filter === 'All' ? ipos : ipos.filter(i => i.status === filter)
  const displayed = showLimit === 0 ? filtered : filtered.slice(0, showLimit)

  const recBg = (s: string) => s === 'bullish' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
    : s === 'bearish' ? 'bg-red-500/10 border-red-500/20 text-red-400'
    : 'bg-amber-500/10 border-amber-500/20 text-amber-400'

  const currency = selected?.currency || (region === 'india' ? '₹' : region === 'uk' ? '£' : region === 'europe' ? '€' : '$')

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">IPO Tracker</h1>
        <p className="text-gray-400 text-sm mt-1">Live IPO calendar with AI-powered listing predictions</p>
      </div>

      {/* Region tabs */}
      <div className="flex flex-wrap gap-2">
        {REGIONS.map(r => (
          <button key={r.id} onClick={() => setRegion(r.id)}
            className={`flex flex-col items-start px-4 py-2.5 rounded-xl border text-sm font-medium transition-all ${
              region === r.id
                ? 'bg-brand-600/20 border-brand-500/40 text-brand-400'
                : 'glass border-white/10 text-gray-400 hover:text-white hover:border-white/20'}`}>
            <span>{r.label}</span>
            <span className="text-xs opacity-60 font-normal">{r.desc}</span>
          </button>
        ))}
      </div>

      <div className="grid lg:grid-cols-5 gap-6">
        {/* IPO list */}
        <div className="lg:col-span-3 space-y-3">
          <div className="flex items-center justify-between flex-wrap gap-2">
            {/* Status filter */}
            <div className="flex gap-1.5 flex-wrap">
              {statuses.map(s => (
                <button key={s} onClick={() => setFilter(s)}
                  className={`text-xs px-3 py-1 rounded-full border transition-all ${
                    filter === s ? 'bg-brand-600/20 border-brand-500/30 text-brand-400' : 'border-white/10 text-gray-500 hover:text-white'}`}>
                  {s}
                </button>
              ))}
            </div>
            <button onClick={() => fetchIPOs(region)} disabled={loading}
              className="btn-ghost text-xs flex items-center gap-1.5">
              <RefreshCw size={13} className={loading ? 'animate-spin' : ''} /> Refresh
            </button>
            {/* Show limit dropdown */}
            <select
              value={showLimit}
              onChange={e => setShowLimit(Number(e.target.value))}
              className="text-xs bg-white/5 border border-white/10 text-gray-300 rounded-lg px-2 py-1 hover:border-white/20 transition-all cursor-pointer"
              style={{ backgroundColor: '#1a1f2e', colorScheme: 'dark' }}
            >
              <option value={5}  style={{ backgroundColor: '#1a1f2e' }}>Top 5</option>
              <option value={10} style={{ backgroundColor: '#1a1f2e' }}>Top 10</option>
              <option value={20} style={{ backgroundColor: '#1a1f2e' }}>Top 20</option>
              <option value={0}  style={{ backgroundColor: '#1a1f2e' }}>All</option>
            </select>
          </div>

          {loading && (
            <div className="card flex items-center justify-center py-16 gap-3">
              <RefreshCw size={20} className="animate-spin text-brand-400" />
              <span className="text-gray-400">Fetching live IPO data…</span>
            </div>
          )}

          {!loading && filtered.length === 0 && (
            <div className="card text-center py-16">
              <Globe size={40} className="text-gray-700 mx-auto mb-3" />
              <p className="text-gray-500">No IPO data found.</p>
              <p className="text-gray-600 text-xs mt-1">Try refreshing or selecting another region.</p>
            </div>
          )}

          <div className="space-y-2">
            {displayed.map((ipo, i) => (
              <button key={i} onClick={() => { setSelected(ipo); setPrediction(null); setIssuePrice(ipo.issuePrice ? String(ipo.issuePrice) : '') }}
                className={`w-full text-left card py-4 hover:border-brand-500/30 transition-all ${
                  selected?.company === ipo.company && selected?.date === ipo.date ? 'border-brand-500/50 bg-brand-600/5' : ''}`}>
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                      <span className="font-bold text-sm">{ipo.company}</span>
                      {ipo.ticker && <span className="text-xs text-brand-400 font-mono bg-brand-600/10 px-1.5 py-0.5 rounded">{ipo.ticker}</span>}
                      <span className={`text-xs px-2 py-0.5 rounded-full border ${STATUS_STYLE[ipo.status] || STATUS_STYLE['News']}`}>
                        {ipo.status}
                      </span>
                      <SentBadge label={ipo.sentiment_label} />
                    </div>
                    <div className="flex flex-wrap gap-3 text-xs text-gray-500">
                      {ipo.exchange && <span>📍 {ipo.exchange}</span>}
                      {ipo.issuePrice > 0 && <span>💰 {ipo.currency}{ipo.issuePrice.toFixed(2)}</span>}
                      {ipo.offerAmount > 0 && <span>📊 {formatAmount(ipo.offerAmount, ipo.currency)}</span>}
                      {ipo.date && <span>📅 {ipo.date}</span>}
                      {ipo.source && <span>🔗 {ipo.source}</span>}
                    </div>
                    {ipo.summary && <p className="text-xs text-gray-500 mt-1.5 line-clamp-1">{ipo.summary}</p>}
                  </div>
                  <ChevronRight size={16} className="text-gray-600 flex-shrink-0 mt-1" />
                </div>
              </button>
            ))}
          </div>
          {/* Show more / show less footer */}
          {filtered.length > 5 && (
            <div className="flex items-center justify-between text-xs text-gray-500 pt-1">
              <span>Showing {displayed.length} of {filtered.length} IPOs</span>
              <div className="flex gap-2">
                {showLimit !== 0 && showLimit < filtered.length && (
                  <button onClick={() => setShowLimit(l => l + 5)}
                    className="text-brand-400 hover:text-brand-300 transition-colors">
                    Show more
                  </button>
                )}
                {showLimit !== 5 && (
                  <button onClick={() => setShowLimit(5)}
                    className="text-gray-600 hover:text-gray-400 transition-colors">
                    Collapse
                  </button>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Prediction panel */}
        <div className="lg:col-span-2 space-y-4">
          {!selected ? (
            <div className="card text-center py-16">
              <Zap size={36} className="text-gray-700 mx-auto mb-3" />
              <p className="text-gray-500 text-sm">Select an IPO to run AI prediction</p>
              <p className="text-gray-600 text-xs mt-1">Powered by sector peer analysis + sentiment</p>
            </div>
          ) : (
            <>
              {/* Selected IPO */}
              <div className="card">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="font-bold text-lg leading-tight">{selected.company}</h3>
                    {selected.ticker && <div className="text-brand-400 font-mono text-sm mt-0.5">{selected.ticker}</div>}
                    <div className="flex items-center gap-2 mt-2 flex-wrap">
                      <span className={`text-xs px-2 py-0.5 rounded-full border ${STATUS_STYLE[selected.status] || STATUS_STYLE['News']}`}>
                        {selected.status}
                      </span>
                      <SentBadge label={selected.sentiment_label} />
                    </div>
                  </div>
                  <a href={selected.url} target="_blank" rel="noopener noreferrer"
                    className="text-gray-500 hover:text-brand-400 transition-colors flex-shrink-0">
                    <ExternalLink size={16} />
                  </a>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  {[
                    { l: 'Exchange', v: selected.exchange || '—' },
                    { l: 'Issue Price', v: selected.issuePrice > 0 ? `${selected.currency}${selected.issuePrice}` : '—' },
                    { l: 'Offer Size', v: formatAmount(selected.offerAmount, selected.currency) },
                    { l: 'Date', v: selected.date || '—' },
                  ].map(({ l, v }) => (
                    <div key={l} className="bg-white/5 rounded-lg p-2">
                      <div className="text-gray-500 mb-0.5">{l}</div>
                      <div className="font-semibold text-white">{v}</div>
                    </div>
                  ))}
                </div>
                {selected.summary && <p className="text-xs text-gray-400 mt-3 leading-relaxed">{selected.summary}</p>}
              </div>

              {/* Prediction form */}
              <div className="card space-y-3">
                <h3 className="font-semibold flex items-center gap-2">
                  <Zap size={16} className="text-brand-400" /> AI Prediction
                </h3>
                <div>
                  <label className="text-xs text-gray-400 mb-1 block">Sector</label>
                  <select
                    className="input-field"
                    value={sector}
                    onChange={e => setSector(e.target.value)}
                    style={{ backgroundColor: '#1a1f2e', color: 'white' }}
                  >
                    {(SECTORS[region] || SECTORS['us']).map(s => (
                      <option key={s} value={s} style={{ backgroundColor: '#1a1f2e', color: 'white' }}>
                        {s}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-gray-400 mb-1 block">Issue Price {selected.currency} (optional)</label>
                  <input className="input-field" type="number" step="any"
                    placeholder={selected.issuePrice > 0 ? String(selected.issuePrice) : 'e.g. 500'}
                    value={issuePrice} onChange={e => setIssuePrice(e.target.value)} />
                </div>
                <button onClick={runPrediction} disabled={predLoading}
                  className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50">
                  {predLoading ? <RefreshCw size={15} className="animate-spin" /> : <Zap size={15} />}
                  {predLoading ? 'Analyzing peers…' : 'Run AI Prediction'}
                </button>
              </div>

              {/* Results */}
              {prediction && (
                <div className="card space-y-4">
                  <div className={`rounded-xl border px-4 py-3 ${recBg(prediction.recommendation_sentiment)}`}>
                    <div className="text-xs opacity-70 mb-0.5">Recommendation</div>
                    <div className="text-xl font-bold">{prediction.recommendation}</div>
                    {prediction.listingPriceEstimate && (
                      <div className="text-xs opacity-70 mt-1">
                        Est. listing: <span className="font-semibold text-white">{currency}{prediction.listingPriceEstimate.toFixed(2)}</span>
                      </div>
                    )}
                  </div>

                  <div>
                    <div className="text-xs text-gray-500 font-medium mb-1 uppercase tracking-wide">Expected Returns</div>
                    <PredRow label="Listing Day" value={prediction.predictions.day1} base={prediction.issuePrice || undefined} currency={currency} />
                    <PredRow label="1 Week" value={prediction.predictions.week1} base={prediction.issuePrice || undefined} currency={currency} />
                    <PredRow label="1 Month" value={prediction.predictions.month1} base={prediction.issuePrice || undefined} currency={currency} />
                    <PredRow label="1 Year" value={prediction.predictions.year1} base={prediction.issuePrice || undefined} currency={currency} />
                  </div>

                  <div>
                    <div className="text-xs text-gray-500 font-medium mb-2 uppercase tracking-wide">Sector Peers ({prediction.sector})</div>
                    <div className="grid grid-cols-3 gap-2 mb-3">
                      {[
                        { l: 'Avg P/E', v: prediction.peerAnalysis.avgPE },
                        { l: 'Avg Beta', v: prediction.peerAnalysis.avgBeta },
                        { l: 'Sector YTD', v: `${prediction.peerAnalysis.sectorYTD.toFixed(1)}%` },
                      ].map(({ l, v }) => (
                        <div key={l} className="bg-white/5 rounded-lg p-2 text-center">
                          <div className="text-xs text-gray-500">{l}</div>
                          <div className="font-semibold text-sm">{v}</div>
                        </div>
                      ))}
                    </div>
                    <div className="space-y-1">
                      {prediction.peerAnalysis.peers.map(p => (
                        <div key={p.ticker} className="flex justify-between text-xs text-gray-400 py-1 border-b border-white/5 last:border-0">
                          <span className="font-medium text-gray-300">{p.ticker}</span>
                          <span>P/E {p.pe?.toFixed(1) || '—'} · YTD {p.ytd?.toFixed(1)}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <p className="text-xs text-gray-600">*Based on sector peer analysis + sentiment. Not financial advice.</p>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
