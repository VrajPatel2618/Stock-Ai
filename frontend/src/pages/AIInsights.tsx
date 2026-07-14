import { useState, useRef, useEffect } from 'react'
import {
  Search, Send, RefreshCw, TrendingUp, TrendingDown, Minus,
  MessageCircle, Bot, User, Zap, CheckCircle, ExternalLink, ChevronDown, ChevronUp
} from 'lucide-react'
import api from '../api/client'
import { TickerSearch } from '../components/TickerSearch'
import MarkdownText from '../components/MarkdownText'

interface ChatMessage {
  role: 'user' | 'ai'
  text: string
  timestamp: Date
  isWarning?: boolean
}

// Simple markdown renderer for bold, bullets
function MarkdownText({ text }: { text: string }) {
  const lines = text.split('\n')
  return (
    <div className="space-y-1">
      {lines.map((line, i) => {
        if (!line.trim()) return <div key={i} className="h-1" />
        // Bold: **text**
        const parts = line.split(/(\*\*[^*]+\*\*)/)
        const rendered = parts.map((p, j) =>
          p.startsWith('**') && p.endsWith('**')
            ? <strong key={j} className="text-white font-semibold">{p.slice(2, -2)}</strong>
            : <span key={j}>{p}</span>
        )
        // Bullet
        if (line.startsWith('• ') || line.startsWith('- ')) {
          return (
            <div key={i} className="flex gap-2">
              <span className="text-brand-400 mt-0.5 flex-shrink-0">•</span>
              <span>{rendered.map((p, j) => p.props?.children ? p : <span key={j}>{p}</span>)}</span>
            </div>
          )
        }
        // Numbered
        if (/^\d+\./.test(line)) {
          return <div key={i} className="flex gap-2"><span className="text-brand-400 flex-shrink-0">{line.match(/^\d+\./)?.[0]}</span><span>{rendered}</span></div>
        }
        return <div key={i}>{rendered}</div>
      })}
    </div>
  )
}

const SUGGESTIONS = [
  'What is the price of AAPL?',
  'Should I buy TSLA right now?',
  'Explain P/E ratio',
  'What is market sentiment today?',
]

export default function AIInsights() {
  const [ticker, setTicker] = useState('')
  const [loading, setLoading] = useState(false)
  const [sentiment, setSentiment] = useState<any>(null)
  const [posts, setPosts] = useState<any[]>([])
  const [showAllPosts, setShowAllPosts] = useState(false)

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'ai',
      text: "Hello! I'm **StockAI**, your professional market analyst.\n\nI can help you with:\n• Live stock prices (ask \"price of AAPL\")\n• Market analysis & sentiment\n• Buy/sell decision frameworks\n• Social media insights\n\nWhat would you like to know?",
      timestamp: new Date(),
    }
  ])
  const [msg, setMsg] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const [ollamaStatus, setOllamaStatus] = useState<'unknown' | 'online' | 'offline'>('unknown')
  const chatEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, chatLoading])

  const analyze = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!ticker.trim()) return
    setLoading(true); setSentiment(null); setPosts([])
    try {
      const [sentRes, socialRes] = await Promise.allSettled([
        api.get(`/sentiment/${ticker.toUpperCase()}`),
        api.get(`/social/${ticker.toUpperCase()}`),
      ])
      if (sentRes.status === 'fulfilled') setSentiment(sentRes.value.data)
      if (socialRes.status === 'fulfilled') setPosts(socialRes.value.data.posts || [])
    } catch {}
    setLoading(false)
  }

  const sendMessage = async (text?: string) => {
    const userMsg = text || msg
    if (!userMsg.trim() || chatLoading) return
    setMsg('')

    const userEntry: ChatMessage = { role: 'user', text: userMsg, timestamp: new Date() }
    setMessages(m => [...m, userEntry])
    setChatLoading(true)

    try {
      const res = await api.post('/chat', { message: userMsg, ticker })
      const available = res.data.ollama_available ?? false
      setOllamaStatus(available ? 'online' : 'offline')
      const isWarning = !available
      setMessages(m => [...m, {
        role: 'ai', text: res.data.response,
        timestamp: new Date(), isWarning
      }])
    } catch {
      setMessages(m => [...m, {
        role: 'ai', text: 'Failed to reach the backend. Make sure Django is running.',
        timestamp: new Date(), isWarning: true
      }])
    }
    setChatLoading(false)
    inputRef.current?.focus()
  }

  const handleSubmit = (e: React.FormEvent) => { e.preventDefault(); sendMessage() }

  const SentIcon = sentiment?.sentiment?.overall === 'bullish' ? TrendingUp
    : sentiment?.sentiment?.overall === 'bearish' ? TrendingDown : Minus
  const sentColor = sentiment?.sentiment?.overall === 'bullish' ? 'text-emerald-400'
    : sentiment?.sentiment?.overall === 'bearish' ? 'text-red-400' : 'text-gray-400'

  return (
    <div className="max-w-7xl mx-auto space-y-6 h-full">
      <div>
        <h1 className="text-2xl font-bold">AI Insights</h1>
        <p className="text-gray-400 text-sm mt-1">Sentiment analysis, social insights, and AI-powered chat</p>
      </div>

      {/* Ticker search */}
      <form onSubmit={analyze} className="flex gap-3">
        <TickerSearch 
          value={ticker} 
          onChange={setTicker} 
          className="flex-1 max-w-md" 
          placeholder="Analyze ticker (e.g. AAPL, RELIANCE.NS)"
        />
        <button type="submit" disabled={loading} className="btn-primary flex items-center gap-2 disabled:opacity-50">
          {loading ? <RefreshCw size={16} className="animate-spin" /> : <Search size={16} />}
          {loading ? 'Analyzing…' : 'Analyze'}
        </button>
      </form>

      {/* Sentiment cards */}
      {sentiment && (
        <div className="grid md:grid-cols-3 gap-4">
          <div className="card flex items-center gap-4">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
              sentiment.sentiment.overall === 'bullish' ? 'bg-emerald-500/20' :
              sentiment.sentiment.overall === 'bearish' ? 'bg-red-500/20' : 'bg-gray-500/20'}`}>
              <SentIcon size={24} className={sentColor} />
            </div>
            <div>
              <div className="text-xs text-gray-500 mb-0.5">Overall Sentiment</div>
              <div className="font-bold text-lg capitalize">{sentiment.sentiment.overall}</div>
              <div className="text-xs text-gray-400">Score: {sentiment.sentiment.score} · {sentiment.sentiment.confidence}% confidence</div>
            </div>
          </div>
          {[
            { label: 'Reddit', data: sentiment.sources.reddit },
            { label: 'StockTwits', data: sentiment.sources.stocktwits },
          ].map(({ label, data }) => (
            <div key={label} className="card">
              <div className="text-xs text-gray-500 mb-3 font-medium">{label}</div>
              <div className="space-y-2">
                {[
                  { l: 'Posts', v: data.count, cls: 'text-white' },
                  { l: 'Bullish', v: `${data.bullish_pct?.toFixed(0)}%`, cls: 'text-emerald-400' },
                  { l: 'Bearish', v: `${data.bearish_pct?.toFixed(0)}%`, cls: 'text-red-400' },
                ].map(({ l, v, cls }) => (
                  <div key={l} className="flex justify-between text-sm">
                    <span className="text-gray-400">{l}</span>
                    <span className={`font-semibold ${cls}`}>{v}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="grid lg:grid-cols-5 gap-6">
        {/* Social — 2 cols */}
        <div className="lg:col-span-2 flex flex-col gap-6 min-h-0">
          {/* Social */}
          <div className="card flex flex-col flex-1 min-h-0">
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <MessageCircle size={18} className="text-brand-400" /> 
              Social {posts.length > 0 && `(${posts.length})`}
            </h3>
            <div className="flex-1 overflow-y-auto space-y-2 min-h-32">
              {posts.length === 0 && (
                <div className="text-center py-6">
                  <MessageCircle size={28} className="text-gray-700 mx-auto mb-2" />
                  <p className="text-gray-500 text-sm">Search a ticker to load social posts</p>
                </div>
              )}
              {(showAllPosts ? posts : posts.slice(0, 3)).map((p, i) => (
                <a key={i} href={p.url || '#'} target={p.url ? "_blank" : "_self"} rel="noopener noreferrer" 
                   className="block p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors group">
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                      p.source === 'reddit' ? 'bg-orange-500/20 text-orange-400' : 'bg-blue-500/20 text-blue-400'}`}>
                      {p.source}
                    </span>
                    {p.subreddit && <span className="text-xs text-gray-500">r/{p.subreddit}</span>}
                    {p.sentiment !== null && (
                      <span className={`ml-auto text-xs font-medium ${
                        p.sentiment > 0.2 ? 'text-emerald-400' : p.sentiment < -0.2 ? 'text-red-400' : 'text-gray-500'}`}>
                        {p.sentiment > 0.2 ? '↑' : p.sentiment < -0.2 ? '↓' : '→'} {p.sentiment?.toFixed(2)}
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-gray-300 leading-snug line-clamp-2 group-hover:text-brand-400 transition-colors">
                    {p.title || p.content}
                  </div>
                  <div className="flex items-center justify-between mt-1">
                    <div className="text-xs text-gray-600">by {p.author}</div>
                    {p.url && <ExternalLink size={12} className="text-gray-600 group-hover:text-brand-400 transition-colors" />}
                  </div>
                </a>
              ))}
              {posts.length > 3 && (
                <button 
                  onClick={() => setShowAllPosts(!showAllPosts)}
                  className="w-full py-2 mt-2 flex items-center justify-center gap-2 text-sm text-gray-400 hover:text-white transition-colors bg-white/5 hover:bg-white/10 rounded-lg"
                >
                  {showAllPosts ? (
                    <><ChevronUp size={16} /> Show Less</>
                  ) : (
                    <><ChevronDown size={16} /> Show All ({posts.length})</>
                  )}
                </button>
              )}
            </div>
          </div>
        </div>

        {/* AI Chat — 3 cols */}
        <div className="lg:col-span-3 card flex flex-col" style={{ height: '600px' }}>
          {/* Chat header */}
          <div className="flex items-center justify-between pb-4 border-b border-white/5 flex-shrink-0">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-brand-600/20 flex items-center justify-center">
                <Bot size={18} className="text-brand-400" />
              </div>
              <div>
                <div className="font-semibold text-sm">StockAI Assistant</div>
                <div className="text-xs text-gray-500">Powered by Gemini AI + VADER</div>
              </div>
            </div>
            <div className="flex items-center gap-1.5">
              {ollamaStatus === 'online' && (
                <span className="flex items-center gap-1.5 text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2.5 py-1 rounded-full">
                  <CheckCircle size={11} /> Gemini Online
                </span>
              )}
              {ollamaStatus === 'offline' && (
                <span className="flex items-center gap-1.5 text-xs bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2.5 py-1 rounded-full">
                  <Zap size={11} /> Fallback Mode
                </span>
              )}
              {ollamaStatus === 'unknown' && (
                <span className="flex items-center gap-1.5 text-xs bg-gray-500/10 text-gray-400 border border-gray-500/20 px-2.5 py-1 rounded-full">
                  <Bot size={11} /> Ready
                </span>
              )}
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto py-4 space-y-4 min-h-0">
            {messages.map((m, i) => (
              <div key={i} className={`flex gap-3 ${m.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                {/* Avatar */}
                <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
                  m.role === 'user' ? 'bg-brand-600' : m.isWarning ? 'bg-amber-500/20' : 'bg-white/10'}`}>
                  {m.role === 'user'
                    ? <User size={13} className="text-white" />
                    : <Bot size={13} className={m.isWarning ? 'text-amber-400' : 'text-brand-400'} />}
                </div>

                {/* Bubble */}
                <div className={`max-w-sm lg:max-w-md rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                  m.role === 'user'
                    ? 'bg-brand-600 text-white rounded-tr-sm'
                    : m.isWarning
                    ? 'bg-amber-500/10 border border-amber-500/20 text-amber-100 rounded-tl-sm'
                    : 'bg-white/8 border border-white/8 text-gray-200 rounded-tl-sm'
                }`}>
                  {m.role === 'ai' ? <MarkdownText text={m.text} /> : m.text}
                  <div className={`text-xs mt-2 ${m.role === 'user' ? 'text-brand-200' : 'text-gray-600'}`}>
                    {m.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
              </div>
            ))}

            {/* Typing indicator */}
            {chatLoading && (
              <div className="flex gap-3">
                <div className="w-7 h-7 rounded-full bg-white/10 flex items-center justify-center flex-shrink-0">
                  <Bot size={13} className="text-brand-400" />
                </div>
                <div className="bg-white/8 border border-white/8 rounded-2xl rounded-tl-sm px-4 py-3">
                  <div className="flex gap-1 items-center h-4">
                    {[0, 1, 2].map(i => (
                      <div key={i} className="w-1.5 h-1.5 rounded-full bg-gray-400 animate-bounce"
                        style={{ animationDelay: `${i * 0.15}s` }} />
                    ))}
                  </div>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Suggestions */}
          {messages.length <= 1 && (
            <div className="flex flex-wrap gap-2 pb-3 flex-shrink-0">
              {SUGGESTIONS.map(s => (
                <button key={s} onClick={() => sendMessage(s)}
                  className="text-xs bg-white/5 hover:bg-brand-600/20 hover:text-brand-400 border border-white/10 hover:border-brand-500/30 text-gray-400 px-3 py-1.5 rounded-full transition-all">
                  {s}
                </button>
              ))}
            </div>
          )}

          {/* Input */}
          <form onSubmit={handleSubmit} className="flex gap-2 pt-3 border-t border-white/5 flex-shrink-0">
            <input
              ref={inputRef}
              className="input-field flex-1 py-2.5 text-sm"
              placeholder={ticker ? `Ask about ${ticker} or anything…` : 'Ask about stocks, prices, analysis…'}
              value={msg}
              onChange={(e) => setMsg(e.target.value)}
              disabled={chatLoading}
            />
            <button type="submit" disabled={chatLoading || !msg.trim()}
              className="btn-primary px-4 py-2.5 disabled:opacity-40 flex items-center gap-1.5">
              <Send size={15} />
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
