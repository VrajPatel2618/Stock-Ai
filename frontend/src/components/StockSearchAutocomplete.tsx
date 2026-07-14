import React, { useState, useEffect, useRef } from 'react'
import { Search, Loader2, TrendingUp } from 'lucide-react'
import api from '../api/client'

interface StockResult {
  symbol: string
  name: string
  type: string
  exchange: string
}

interface StockSearchAutocompleteProps {
  onSelect: (ticker: string) => void
  onChange?: (value: string) => void
  placeholder?: string
  className?: string
  value?: string
}

export default function StockSearchAutocomplete({ onSelect, onChange, placeholder = "Search for a stock...", className = "", value = "" }: StockSearchAutocompleteProps) {
  const [internalQuery, setInternalQuery] = useState(value)
  const query = value !== undefined ? value : internalQuery

  const handleQueryChange = (newVal: string) => {
    setInternalQuery(newVal)
    if (onChange) onChange(newVal)
  }

  const [results, setResults] = useState<StockResult[]>([])
  const [similarStocks, setSimilarStocks] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [showDropdown, setShowDropdown] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  
  const [debouncedQuery, setDebouncedQuery] = useState(value)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedQuery(query)
    }, 400)
    return () => clearTimeout(handler)
  }, [query])

  useEffect(() => {
    if (debouncedQuery && debouncedQuery.length >= 1) {
      setLoading(true)
      api.get(`/search?q=${debouncedQuery}`)
        .then(res => {
          setResults(res.data)
          setShowDropdown(true)
        })
        .catch(err => console.error("Search API Error:", err))
        .finally(() => setLoading(false))
    } else {
      setResults([])
      setShowDropdown(false)
    }
  }, [debouncedQuery])

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  const handleSelect = (ticker: string) => {
    handleQueryChange(ticker)
    setShowDropdown(false)
    setSimilarStocks([])
    onSelect(ticker)
    
    // Fetch similar stocks
    api.get(`/similar/${ticker}`)
      .then(res => setSimilarStocks(res.data))
      .catch(err => console.error("Similar Stocks API Error:", err))
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      const ticker = query.trim().toUpperCase()
      if (ticker) {
        handleSelect(ticker)
      }
    }
  }

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
        <input
          type="text"
          className="input-field pl-10 w-full"
          placeholder={placeholder}
          value={query}
          onChange={(e) => handleQueryChange(e.target.value)}
          onFocus={() => { if (results.length > 0) setShowDropdown(true) }}
          onKeyDown={handleKeyDown}
        />
        {loading && <Loader2 className="absolute right-3 top-1/2 transform -translate-y-1/2 text-brand-400 animate-spin" size={16} />}
      </div>
      
      {showDropdown && results.length > 0 && (
        <div className="absolute z-50 mt-2 w-full bg-[#1A1F2E] border border-white/10 rounded-xl shadow-2xl max-h-64 overflow-y-auto">
          {results.map((r, i) => (
            <button
              key={i}
              className="w-full text-left px-4 py-3 hover:bg-white/5 border-b border-white/5 last:border-b-0 flex items-center justify-between group transition-colors"
              onClick={() => handleSelect(r.symbol)}
            >
              <div>
                <div className="font-semibold text-gray-100 group-hover:text-brand-400 transition-colors">{r.symbol}</div>
                <div className="text-xs text-gray-400 truncate w-48 sm:w-64">{r.name}</div>
              </div>
              <div className="text-xs text-gray-500 bg-white/5 px-2 py-1 rounded">
                {r.exchange}
              </div>
            </button>
          ))}
        </div>
      )}

      {similarStocks.length > 0 && !showDropdown && (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <span className="text-xs text-gray-400 flex items-center gap-1">
            <TrendingUp size={12} /> Similar:
          </span>
          {similarStocks.map((ticker, i) => (
            <button
              key={i}
              className="text-xs bg-brand-500/10 hover:bg-brand-500/20 text-brand-400 border border-brand-500/20 px-2.5 py-1 rounded-full transition-colors"
              onClick={() => handleSelect(ticker)}
            >
              {ticker}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
