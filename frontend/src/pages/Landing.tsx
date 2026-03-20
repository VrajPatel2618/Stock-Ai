import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { TrendingUp, Brain, BarChart2, Shield, Zap, Globe } from 'lucide-react'

const features = [
  { icon: Brain, title: 'AI Predictions', desc: 'LSTM neural network forecasts up to 1 year ahead with confidence scoring.' },
  { icon: TrendingUp, title: 'Real-Time Data', desc: 'Live stock prices, P/E ratios, market cap and 52-week ranges.' },
  { icon: BarChart2, title: 'Sentiment Analysis', desc: 'Reddit, StockTwits and news sentiment aggregated into actionable signals.' },
  { icon: Globe, title: 'Commodities', desc: 'Gold, Silver, Oil and Natural Gas forecasting with AI analysis.' },
  { icon: Shield, title: 'Portfolio Tracking', desc: 'Monitor your holdings, gains/losses and watchlist in one place.' },
  { icon: Zap, title: 'No API Keys', desc: 'All data from public sources — no subscriptions or API keys required.' },
]

const stats = [
  { label: 'Prediction Horizon', value: '365 Days' },
  { label: 'Data Sources', value: '5+' },
  { label: 'Model Accuracy', value: 'LSTM' },
  { label: 'Setup Time', value: '< 2 min' },
]

export default function Landing() {
  return (
    <div className="min-h-screen bg-gray-950 text-white overflow-hidden">
      {/* Nav */}
      <nav className="fixed top-0 inset-x-0 z-50 glass border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center">
              <TrendingUp size={16} className="text-white" />
            </div>
            <span className="font-bold text-lg">Stock<span className="text-brand-400">.AI</span></span>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/login" className="btn-ghost text-sm">Sign In</Link>
            <Link to="/register" className="btn-primary text-sm">Get Started</Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative pt-32 pb-24 px-6">
        {/* Glow */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-brand-600/20 rounded-full blur-3xl" />
        </div>

        <div className="relative max-w-4xl mx-auto text-center">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
            <span className="inline-flex items-center gap-2 glass rounded-full px-4 py-1.5 text-sm text-brand-400 mb-6">
              <Zap size={14} /> AI-Powered Stock Analysis Platform
            </span>
            <h1 className="text-5xl md:text-7xl font-extrabold leading-tight mb-6">
              Predict Markets with
              <span className="block text-transparent bg-clip-text bg-gradient-to-r from-brand-400 to-emerald-400">
                Neural Intelligence
              </span>
            </h1>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-10">
              LSTM-powered forecasts, real-time sentiment from Reddit & news, and AI-driven insights — all in one terminal.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/register" className="btn-primary text-base px-8 py-3">
                Start Analyzing Free
              </Link>
              <Link to="/dashboard" className="glass hover:bg-white/10 text-white font-semibold px-8 py-3 rounded-xl transition-all">
                View Dashboard
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-12 px-6 border-y border-white/5">
        <div className="max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((s) => (
            <div key={s.label} className="text-center">
              <div className="text-3xl font-bold text-brand-400">{s.value}</div>
              <div className="text-sm text-gray-500 mt-1">{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4">Everything you need to trade smarter</h2>
            <p className="text-gray-400 text-lg">Professional-grade tools, zero cost.</p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f, i) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                viewport={{ once: true }}
                className="card hover:border-brand-500/30 transition-colors group"
              >
                <div className="w-10 h-10 rounded-xl bg-brand-600/20 flex items-center justify-center mb-4 group-hover:bg-brand-600/30 transition-colors">
                  <f.icon size={20} className="text-brand-400" />
                </div>
                <h3 className="font-semibold text-lg mb-2">{f.title}</h3>
                <p className="text-gray-400 text-sm leading-relaxed">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6">
        <div className="max-w-2xl mx-auto text-center">
          <div className="card border-brand-500/20">
            <h2 className="text-3xl font-bold mb-4">Ready to start?</h2>
            <p className="text-gray-400 mb-8">Create a free account and get AI predictions in seconds.</p>
            <Link to="/register" className="btn-primary text-base px-10 py-3 inline-block">
              Create Free Account
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-8 px-6 text-center text-gray-600 text-sm">
        © {new Date().getFullYear()} Stock.AI — Built for traders and investors
      </footer>
    </div>
  )
}
