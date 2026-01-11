import React, { useEffect, useState } from 'react'
import { fetchMyTrips } from '../api'
import { useAuth } from '../auth/AuthProvider'
import { Link, useNavigate } from 'react-router-dom'
import ItineraryView from '../components/ItineraryView'

export default function TripsPage() {
  const { user, token } = useAuth()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedTrip, setSelectedTrip] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    let mounted = true
    const run = async () => {
      setLoading(true)
      setError('')
      try {
        const data = await fetchMyTrips(50)
        if (mounted) setItems(data.items || [])
      } catch (e) {
        if (mounted) setError(e?.message || 'Failed to load trips')
      } finally {
        if (mounted) setLoading(false)
      }
    }
    if (token) run()
    return () => { mounted = false }
  }, [token])

  const formatDate = (dateStr) => {
    if (!dateStr) return ''
    try {
      const date = new Date(dateStr)
      return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return dateStr
    }
  }

  const formatCurrency = (amount, currency = 'INR') => {
    if (amount == null) return '-'
    try {
      return new Intl.NumberFormat('en-IN', { 
        style: 'currency', 
        currency: currency || 'INR', 
        maximumFractionDigits: 0 
      }).format(amount)
    } catch {
      return `${currency || ''} ${amount}`
    }
  }

  if (!user) {
    return (
      <main className="container">
        <div className="trip-auth-card" style={{ marginTop: 64, padding: 48, maxWidth: 600, marginLeft: 'auto', marginRight: 'auto', textAlign: 'center' }}>
          <div style={{ fontSize: 64, marginBottom: 24 }}>🔐</div>
          <h2 style={{ margin: 0, fontSize: 28, fontWeight: 700, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>
            Sign In Required
          </h2>
          <p className="muted" style={{ marginTop: 16, fontSize: 16, lineHeight: 1.6, color: '#64748b' }}>
            Please sign in to view your saved travel itineraries. All your trips are automatically saved for easy access.
          </p>
          <div style={{ marginTop: 32, display: 'flex', gap: 12, justifyContent: 'center' }}>
            <Link to="/signin" className="btn-primary">Sign In</Link>
            <Link to="/plan" className="btn-secondary">Plan New Trip</Link>
          </div>
        </div>
      </main>
    )
  }

  if (selectedTrip) {
    return (
      <main className="container">
        <div style={{ marginTop: 32 }}>
          <button 
            onClick={() => setSelectedTrip(null)}
            className="btn-secondary"
            style={{ marginBottom: 24, display: 'flex', alignItems: 'center', gap: 8 }}
          >
            ← Back to My Trips
          </button>
          <div className="card" style={{ padding: 32 }}>
            <ItineraryView data={selectedTrip} />
          </div>
        </div>
      </main>
    )
  }

  return (
    <main className="container">
      <div style={{ marginTop: 32 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 32 }}>
          <div>
            <h1 style={{ 
              margin: 0, 
              fontSize: 36, 
              fontWeight: 700, 
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
              WebkitBackgroundClip: 'text', 
              WebkitTextFillColor: 'transparent', 
              backgroundClip: 'text',
              display: 'flex',
              alignItems: 'center',
              gap: 12
            }}>
              <span>🗺️</span>
              My Trips
            </h1>
            <p className="muted" style={{ marginTop: 8, fontSize: 16 }}>
              View and manage all your saved travel itineraries
            </p>
          </div>
          <Link to="/plan" className="btn-primary">
            + Plan New Trip
          </Link>
        </div>

        {loading && (
          <div className="loading-card" style={{ padding: 48, textAlign: 'center' }}>
            <div className="spinner" style={{ margin: '0 auto 16px', width: 32, height: 32, borderWidth: 4 }} />
            <div className="muted" style={{ fontSize: 16 }}>Loading your trips...</div>
          </div>
        )}

        {error && (
          <div className="error-card" style={{ marginTop: 24, padding: 24 }}>
            <span style={{ marginRight: 12 }}>⚠️</span>
            <strong>Error:</strong> {error}
          </div>
        )}

        {!loading && !error && items.length === 0 && (
          <div className="empty-trips-card" style={{ 
            marginTop: 32, 
            padding: 64, 
            textAlign: 'center',
            background: 'linear-gradient(135deg, #f0f4ff 0%, #fef0ff 100%)',
            border: '2px dashed #cbd5e1',
            borderRadius: 20
          }}>
            <div style={{ fontSize: 64, marginBottom: 24 }}>✈️</div>
            <h3 style={{ 
              margin: 0, 
              fontSize: 24, 
              fontWeight: 700, 
              color: '#475569',
              marginBottom: 12
            }}>
              No trips yet
            </h3>
            <p className="muted" style={{ marginTop: 8, fontSize: 16, marginBottom: 32, maxWidth: 400, marginLeft: 'auto', marginRight: 'auto' }}>
              Start planning your first adventure! Create a personalized itinerary in just a few seconds.
            </p>
            <Link to="/plan" className="btn-primary">
              Plan Your First Trip
            </Link>
          </div>
        )}

        {!loading && !error && items.length > 0 && (
          <div className="grid grid-2" style={{ gap: 24, alignItems: 'stretch' }}>
            {items.map((it) => (
              <div 
                key={it.id} 
                className="trip-card"
                onClick={() => setSelectedTrip(it)}
                style={{
                  background: 'linear-gradient(135deg, #ffffff 0%, #fafbfc 100%)',
                  border: '2px solid #e2e8f0',
                  borderRadius: 16,
                  padding: 24,
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                  position: 'relative',
                  overflow: 'hidden',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = '#667eea'
                  e.currentTarget.style.boxShadow = '0 8px 24px rgba(102, 126, 234, 0.15)'
                  e.currentTarget.style.transform = 'translateY(-4px)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = '#e2e8f0'
                  e.currentTarget.style.boxShadow = 'none'
                  e.currentTarget.style.transform = 'translateY(0)'
                }}
              >
                <div style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  height: 4,
                  background: 'linear-gradient(90deg, #667eea 0%, #764ba2 100%)'
                }} />
                
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
                  <div style={{ flex: 1, minHeight: 72 }}>
                    <h3 style={{ 
                      margin: 0, 
                      fontSize: 18, 
                      fontWeight: 700, 
                      color: '#1e293b',
                      marginBottom: 8,
                      lineHeight: 1.5,
                      display: '-webkit-box',
                      WebkitLineClamp: 3,
                      WebkitBoxOrient: 'vertical',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      wordBreak: 'break-word'
                    }}>
                      {it?.summary || 'Untitled Trip'}
                    </h3>
                    <div style={{ 
                      fontSize: 13, 
                      color: '#64748b',
                      marginTop: 4,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8
                    }}>
                      <span>📅</span>
                      <span>{formatDate(it.createdAt)}</span>
                    </div>
                  </div>
                  <div style={{
                    background: 'linear-gradient(135deg, #f0f4ff 0%, #fef0ff 100%)',
                    border: '1px solid #e2e8f0',
                    borderRadius: 8,
                    padding: '4px 12px',
                    fontSize: 12,
                    fontWeight: 600,
                    color: '#667eea'
                  }}>
                    View →
                  </div>
                </div>

                {it?.flights && (
                  <div style={{
                    background: 'linear-gradient(135deg, #fafbfc 0%, #f1f5f9 100%)',
                    borderRadius: 12,
                    padding: 16,
                    marginTop: 16,
                    border: '1px solid #e2e8f0'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
                      <span style={{ fontSize: 20 }}>✈️</span>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: 13, color: '#64748b', marginBottom: 4 }}>Route</div>
                        <div style={{ fontSize: 15, fontWeight: 600, color: '#1e293b' }}>
                          {it.flights.originAirport || 'Origin'} → {it.flights.destinationAirport || 'Destination'}
                        </div>
                      </div>
                    </div>
                    {it.flights.estimatedRoundTripPerPerson && (
                      <div style={{ 
                        marginTop: 12, 
                        paddingTop: 12, 
                        borderTop: '1px solid #e2e8f0',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                      }}>
                        <span style={{ fontSize: 13, color: '#64748b' }}>Est. Cost per Person</span>
                        <span style={{ fontSize: 16, fontWeight: 700, color: '#667eea' }}>
                          {formatCurrency(it.flights.estimatedRoundTripPerPerson, it.flights.currency)}
                        </span>
                      </div>
                    )}
                  </div>
                )}

                {it?.estimatedTotals && (
                  <div style={{ 
                    marginTop: 16, 
                    padding: 12, 
                    background: 'linear-gradient(135deg, #f0f4ff 0%, #fef0ff 100%)',
                    borderRadius: 10,
                    border: '1px solid #e2e8f0'
                  }}>
                    <div style={{ fontSize: 13, color: '#64748b', marginBottom: 6 }}>Total Budget Estimate</div>
                    <div style={{ fontSize: 20, fontWeight: 700, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>
                      {formatCurrency(it.estimatedTotals.grandTotal, it.estimatedTotals.currency)}
                    </div>
                  </div>
                )}

                {it?.dailyPlan && it.dailyPlan.length > 0 && (
                  <div style={{ 
                    marginTop: 'auto',
                    paddingTop: 16, 
                    borderTop: '1px solid #e2e8f0'
                  }}>
                    <div style={{ fontSize: 13, color: '#64748b', marginBottom: 8 }}>Daily Plan Preview</div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                      {it.dailyPlan.slice(0, 3).map((day, idx) => (
                        <div 
                          key={idx}
                          style={{
                            background: '#ffffff',
                            border: '1px solid #e2e8f0',
                            borderRadius: 6,
                            padding: '6px 10px',
                            fontSize: 12,
                            fontWeight: 600,
                            color: '#667eea'
                          }}
                        >
                          Day {day.day}
                        </div>
                      ))}
                      {it.dailyPlan.length > 3 && (
                        <div style={{
                          background: '#ffffff',
                          border: '1px solid #e2e8f0',
                          borderRadius: 6,
                          padding: '6px 10px',
                          fontSize: 12,
                          fontWeight: 600,
                          color: '#64748b'
                        }}>
                          +{it.dailyPlan.length - 3} more
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  )
}
