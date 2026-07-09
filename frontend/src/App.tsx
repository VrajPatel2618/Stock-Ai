import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Register from './pages/Register'
import AppLayout from './components/AppLayout'
import Dashboard from './pages/Dashboard'
import Commodities from './pages/Commodities'
import AIInsights from './pages/AIInsights'
import Watchlist from './pages/Watchlist'
import Portfolio from './pages/Portfolio'
import IPOPage from './pages/IPO'
import Explore from './pages/Explore'
import Crypto from './pages/Crypto'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/commodities" element={<Commodities />} />
          <Route path="/insights" element={<AIInsights />} />
          <Route path="/watchlist" element={<Watchlist />} />
          <Route path="/portfolio" element={<Portfolio />} />
          <Route path="/ipo" element={<IPOPage />} />
          <Route path="/explore" element={<Explore />} />
          <Route path="/crypto" element={<Crypto />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
