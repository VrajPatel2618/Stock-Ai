import React, { useState, useEffect, useRef } from 'react'
import { Search, Loader2 } from 'lucide-react'
import api from '../api/client'

interface SearchResult {
  symbol: string
  name: string
  exchange: string
  type: string
}

interface TickerSearchProps {
  value: string
  onChange: (value: string) => void
  onSelect?: (symbol: string) => void
  placeholder?: string
  className?: string
  autoFocus?: boolean
}

export function TickerSearch({ 
  value, 
  onChange, 
  onSelect,
  placeholder = "Search ticker (e.g. AAPL)...",
  className = "",
  autoFocus = false
}: TickerSearchProps) {
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [showDropdown, setShowDropdown] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  
  const containerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Debounce API calls
  useEffect(() => {
    if (!value.trim() || value.length < 2) {
      setResults([])
      setLoading(false)
      return
    }

    const timer = setTimeout(async () => {
      setLoading(true)
      try {
        const res = await api.get(`/api/search?q=${encodeURIComponent(value)}`)
        const data = res.data
        setResults(data)
        if (data.length > 0) setShowDropdown(true)
      } catch (e) {
        console.error("Search failed", e)
      } finally {
        setLoading(false)
      }
    }, 300)

    return () => clearTimeout(timer)
  }, [value])

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showDropdown || results.length === 0) return

    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedIndex(prev => (prev < results.length - 1 ? prev + 1 : prev))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedIndex(prev => (prev > 0 ? prev - 1 : 0))
    } else if (e.key === 'Enter') {
      if (selectedIndex >= 0 && selectedIndex < results.length) {
        e.preventDefault()
        handleSelect(results[selectedIndex])
      }
    } else if (e.key === 'Escape') {
      setShowDropdown(false)
    }
  }

  const handleSelect = (r: SearchResult) => {
    onChange(r.symbol)
    setShowDropdown(false)
    if (onSelect) {
      onSelect(r.symbol)
    }
  }

  return (
    <div className={`relative ${className}`} ref={containerRef}>
      <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={(e) => {
          onChange(e.target.value.toUpperCase())
          setShowDropdown(true)
          setSelectedIndex(-1)
        }}
        onKeyDown={handleKeyDown}
        onFocus={() => {
          if (results.length > 0) setShowDropdown(true)
        }}
        placeholder={placeholder}
        autoFocus={autoFocus}
        className="w-full bg-white/5 border border-white/10 rounded-xl py-3 pl-11 pr-12 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-brand-500/50 transition-all uppercase"
      />
      {loading && (
        <div className="absolute right-4 top-1/2 -translate-y-1/2">
          <Loader2 size={16} className="text-gray-400 animate-spin" />
        </div>
      )}

      {showDropdown && results.length > 0 && (
        <div className="absolute z-50 top-full left-0 right-0 mt-2 bg-[#1a1f2e] border border-white/10 rounded-xl shadow-2xl overflow-hidden max-h-[300px] overflow-y-auto">
          {results.map((r, i) => (
            <button
              key={`${r.symbol}-${i}`}
              className={`w-full text-left px-4 py-3 hover:bg-white/5 transition-colors border-b border-white/5 last:border-0 flex flex-col ${
                i === selectedIndex ? 'bg-white/10' : ''
              }`}
              onClick={() => handleSelect(r)}
            >
              <div className="flex items-baseline justify-between">
                <span className="font-bold text-white">{r.symbol}</span>
                <span className="text-xs font-medium text-gray-500 bg-white/5 px-2 py-0.5 rounded-full">
                  {r.exchange}
                </span>
              </div>
              <span className="text-sm text-gray-400 truncate mt-0.5">{r.name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
