import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { TrendingUp, BarChart2, Layers, Star, Briefcase, MessageSquare, LogOut, Menu, User, Rocket, Compass, Bitcoin } from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import api from '../api/client'

const nav = [
  { to: '/dashboard', icon: BarChart2, label: 'Market Analysis' },
  { to: '/explore', icon: Compass, label: 'Explore Markets' },
  { to: '/commodities', icon: Layers, label: 'Commodities' },
  { to: '/crypto', icon: Bitcoin, label: 'Cryptocurrency' },
  { to: '/insights', icon: MessageSquare, label: 'AI Insights' },
  { to: '/ipo', icon: Rocket, label: 'IPO Tracker' },
  { to: '/watchlist', icon: Star, label: 'Watchlist' },
  { to: '/portfolio', icon: Briefcase, label: 'Portfolio' },
]

export default function AppLayout() {
  const [open, setOpen] = useState(false)
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = async () => {
    try { await api.post('/auth/logout') } catch {}
    logout()
    navigate('/')
  }

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      <Link to="/dashboard" className="flex items-center gap-2 px-4 py-5 border-b border-white/5 hover:opacity-80 transition-opacity">
        <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center flex-shrink-0">
          <TrendingUp size={16} className="text-white" />
        </div>
        <span className="font-bold text-lg">Stock<span className="text-brand-400">.AI</span></span>
      </Link>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {nav.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to} to={to}
            onClick={() => setOpen(false)}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                isActive
                  ? 'bg-brand-600/20 text-brand-400 border border-brand-500/20'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="px-3 py-4 border-t border-white/5">
        <div className="flex items-center gap-3 px-3 py-2 mb-2">
          <div className="w-8 h-8 rounded-full bg-brand-600/30 flex items-center justify-center">
            <User size={14} className="text-brand-400" />
          </div>
          <span className="text-sm font-medium text-gray-300 truncate">{user?.username}</span>
        </div>
        <button onClick={handleLogout}
          className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-gray-400 hover:text-red-400 hover:bg-red-500/10 transition-all w-full">
          <LogOut size={18} />
          Sign Out
        </button>
      </div>
    </div>
  )

  return (
    <div className="flex h-screen bg-gray-950 overflow-hidden">
      {/* Desktop sidebar */}
      <aside className="hidden md:flex flex-col w-60 glass border-r border-white/5 flex-shrink-0">
        <SidebarContent />
      </aside>

      {/* Mobile sidebar */}
      {open && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div className="absolute inset-0 bg-black/60" onClick={() => setOpen(false)} />
          <aside className="absolute left-0 top-0 bottom-0 w-60 bg-gray-900 border-r border-white/10 flex flex-col">
            <SidebarContent />
          </aside>
        </div>
      )}

      {/* Main */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Mobile topbar */}
        <header className="md:hidden flex items-center justify-between px-4 h-14 border-b border-white/5 glass">
          <button onClick={() => setOpen(true)} className="text-gray-400 hover:text-white">
            <Menu size={22} />
          </button>
          <Link to="/dashboard" className="font-bold hover:opacity-80 transition-opacity">Stock<span className="text-brand-400">.AI</span></Link>
          <div className="w-8" />
        </header>

        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
