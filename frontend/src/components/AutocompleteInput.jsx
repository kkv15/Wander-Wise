import React, { useEffect, useRef, useState } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export default function AutocompleteInput({ label, placeholder, value, onSelect, minChars = 2 }) {
  const [q, setQ] = useState(value || '')
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [items, setItems] = useState([])
  const debouncer = useRef(null)
  const boxRef = useRef(null)

  useEffect(() => {
    function onClick(e) {
      if (boxRef.current && !boxRef.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('click', onClick)
    return () => document.removeEventListener('click', onClick)
  }, [])

  useEffect(() => {
    if (!q || q.trim().length < minChars) {
      setItems([])
      setOpen(false)
      setLoading(false)
      if (debouncer.current) {
        clearTimeout(debouncer.current)
        debouncer.current = null
      }
      return
    }
    
    if (debouncer.current) clearTimeout(debouncer.current)
    
    setLoading(true)
    setOpen(true)  // Show dropdown immediately when typing starts
    
    const searchQuery = q.trim()
    debouncer.current = setTimeout(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/cities?q=${encodeURIComponent(searchQuery)}`)
        const data = await res.json()
        const fetchedItems = Array.isArray(data) ? data : []
        setItems(fetchedItems)
        // Keep dropdown open if we have items (or show "no results" message)
        setOpen(fetchedItems.length > 0 || searchQuery.length >= minChars)
      } catch (e) {
        console.error('Failed to fetch cities:', e)
        setItems([])
        // Keep dropdown open to show error/no results state
        setOpen(searchQuery.length >= minChars)
      } finally {
        setLoading(false)
      }
    }, 300)
    
    return () => {
      if (debouncer.current) {
        clearTimeout(debouncer.current)
        debouncer.current = null
      }
    }
  }, [q, minChars])

  const pick = (item) => {
    onSelect?.(item.name)
    setQ(item.name)
    setItems([item])  // Keep the selected item in list
    setOpen(false)
  }
  
  // Sync with external value changes
  useEffect(() => {
    if (value && value !== q) {
      setQ(value)
    }
  }, [value])

  // Add class to parent form-section when dropdown is open to elevate z-index above Travel Preferences
  useEffect(() => {
    if (boxRef.current) {
      const formSection = boxRef.current.closest('.form-section')
      if (formSection) {
        if (open) {
          formSection.classList.add('has-autocomplete-open')
        } else {
          formSection.classList.remove('has-autocomplete-open')
        }
      }
    }
    return () => {
      // Cleanup: remove class when component unmounts or dropdown closes
      if (boxRef.current) {
        const formSection = boxRef.current.closest('.form-section')
        if (formSection) {
          formSection.classList.remove('has-autocomplete-open')
        }
      }
    }
  }, [open])

  return (
    <div ref={boxRef} style={{ position: 'relative', width: '100%', zIndex: open ? 10000 : 'auto', minWidth: 0, maxWidth: '100%', isolation: open ? 'isolate' : 'auto' }}>
      <label className="field-label" style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, fontWeight: 600, color: '#334155', marginBottom: 8 }}>
        {label}
      </label>
      <div style={{ position: 'relative', width: '100%', minWidth: 0, maxWidth: '100%', zIndex: open ? 10001 : 'auto' }}>
        <input
          className="form-input"
          placeholder={placeholder}
          value={q}
          onChange={(e) => {
            const newValue = e.target.value
            setQ(newValue)
            if (newValue.trim().length >= minChars) {
              setOpen(true)
            } else {
              setOpen(false)
              setItems([])
            }
          }}
          onFocus={() => {
            // Open dropdown if we have items or if we have enough chars to search
            if (items.length > 0 || (q.trim().length >= minChars)) {
              setOpen(true)
            }
          }}
          onBlur={(e) => {
            // Delay closing to allow clicks on dropdown items
            setTimeout(() => {
              if (boxRef.current && !boxRef.current.contains(document.activeElement)) {
                setOpen(false)
              }
            }, 200)
          }}
          style={{ 
            height: 48, 
            padding: '0 16px', 
            border: '2px solid #e2e8f0', 
            borderRadius: 12, 
            fontSize: 15, 
            color: '#1e293b', 
            background: 'linear-gradient(135deg, #ffffff 0%, #fafbfc 100%)', 
            transition: 'all 0.3s ease', 
            width: '100%',
            maxWidth: '100%',
            boxSizing: 'border-box',
            outline: 'none',
            display: 'block'
          }}
          onMouseEnter={(e) => {
            e.target.style.borderColor = '#667eea';
            e.target.style.background = 'linear-gradient(135deg, #fafbfc 0%, #f0f4ff 100%)';
            e.target.style.boxShadow = '0 2px 8px rgba(102, 126, 234, 0.1)';
          }}
          onMouseLeave={(e) => {
            if (!e.target.matches(':focus')) {
              e.target.style.borderColor = '#e2e8f0';
              e.target.style.background = 'linear-gradient(135deg, #ffffff 0%, #fafbfc 100%)';
              e.target.style.boxShadow = 'none';
            }
          }}
        />
        {open && (items.length > 0 || loading || (q.trim().length >= minChars && items.length === 0)) && (
          <div style={{
            position: 'absolute', 
            zIndex: 999999, 
            top: 'calc(100% + 8px)', 
            left: 0, 
            right: 0,
            width: '100%',
            minWidth: 0,
            maxWidth: '100%',
            background: '#ffffff', 
            border: '2px solid #667eea', 
            borderRadius: 14, 
            maxHeight: 320, 
            overflowY: 'auto', 
            overflowX: 'hidden',
            boxShadow: '0 12px 40px rgba(102, 126, 234, 0.25), 0 0 0 1px rgba(102, 126, 234, 0.15)', 
            padding: '8px 0',
            transform: 'translateZ(0)',
            willChange: 'transform',
            pointerEvents: 'auto',
            marginTop: 0,
            boxSizing: 'border-box'
          }}>
            {loading ? (
              <div style={{ 
                padding: 20, 
                textAlign: 'center', 
                background: 'linear-gradient(135deg, #f0f4ff 0%, #fef0ff 100%)',
                color: '#667eea', 
                fontSize: 14, 
                fontWeight: 600 
              }}>
                🔍 Searching cities…
              </div>
            ) : (
              items.map((it, idx) => (
                <div
                  key={idx}
                  onClick={() => pick(it)}
                  style={{ 
                    padding: '14px 20px', 
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    margin: '4px 12px',
                    borderRadius: 10,
                    background: '#ffffff',
                    border: '1px solid #e2e8f0',
                    boxSizing: 'border-box',
                    position: 'relative',
                    outline: 'none'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = 'linear-gradient(135deg, #f0f4ff 0%, #fef0ff 100%)';
                    e.currentTarget.style.borderColor = '#667eea';
                    e.currentTarget.style.borderWidth = '2px';
                    e.currentTarget.style.boxShadow = '0 2px 8px rgba(102, 126, 234, 0.15)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = '#ffffff';
                    e.currentTarget.style.borderColor = '#e2e8f0';
                    e.currentTarget.style.borderWidth = '1px';
                    e.currentTarget.style.boxShadow = 'none';
                  }}
                  onMouseDown={(e) => {
                    e.preventDefault();
                    e.currentTarget.style.background = 'linear-gradient(135deg, #e0e7ff 0%, #ede9fe 100%)';
                    e.currentTarget.style.borderColor = '#667eea';
                    e.currentTarget.style.borderWidth = '2px';
                    e.currentTarget.style.transform = 'scale(0.98)';
                  }}
                  onMouseUp={(e) => {
                    e.currentTarget.style.transform = 'scale(1)';
                    e.currentTarget.style.background = 'linear-gradient(135deg, #f0f4ff 0%, #fef0ff 100%)';
                  }}
                  onFocus={(e) => {
                    e.currentTarget.style.background = 'linear-gradient(135deg, #f0f4ff 0%, #fef0ff 100%)';
                    e.currentTarget.style.borderColor = '#667eea';
                    e.currentTarget.style.borderWidth = '2px';
                    e.currentTarget.style.outline = 'none';
                  }}
                >
                  <span style={{ 
                    fontSize: 15, 
                    color: '#1e293b', 
                    fontWeight: 500,
                    display: 'block',
                    wordBreak: 'break-word',
                    lineHeight: 1.5,
                    whiteSpace: 'normal'
                  }}>
                    {it.name}
                  </span>
                </div>
              ))
            )}
            {!loading && items.length === 0 && q.trim().length >= minChars && (
              <div style={{ 
                padding: 20, 
                textAlign: 'center', 
                color: '#64748b', 
                fontSize: 14,
                background: 'linear-gradient(135deg, #fafbfc 0%, #f1f5f9 100%)'
              }}>
                📍 No cities found
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}


