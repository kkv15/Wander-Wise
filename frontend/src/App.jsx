import React, { useState, useEffect } from 'react'
import { planTrip } from './api'
import ItineraryView from './components/ItineraryView'
import AutocompleteInput from './components/AutocompleteInput'
import { Routes, Route, Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from './auth/AuthProvider'
import SignInPage from './pages/SignIn'
import TripsPage from './pages/Trips'

export default function App() {
  const [form, setForm] = useState({
    originCity: '',
    destinationCity: '',
    numDays: 5,
    numPeople: 2,
    budgetCurrency: 'INR',
    budgetAmount: '',
    includeFoodRecos: true,
    includeCommuteTimes: true
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [loadingMsgIdx, setLoadingMsgIdx] = useState(0)
  const loadingMsgs = [
    'Finding best routes and nearby airports…',
    'Picking balanced daily activities…',
    'Estimating hotel and activity costs…',
    'Finalizing your personalized itinerary…'
  ]
  const travelEmojis = ['✈','🚇','🚢']
  const [logoOk, setLogoOk] = useState(true)
  const auth = useAuth?.() || {}
  const navigate = useNavigate()

  // Prefill planner from /plan?origin=&dest=&days=&budget=&currency=
  const location = useLocation()
  useEffect(() => {
    if (location.pathname !== '/plan') return
    const qs = new URLSearchParams(location.search || '')
    const origin = qs.get('origin')
    const dest = qs.get('dest')
    const days = qs.get('days')
    const budget = qs.get('budget')
    const currency = qs.get('currency')
    setForm(prev => ({
      ...prev,
      originCity: origin || prev.originCity,
      destinationCity: dest || prev.destinationCity,
      numDays: days ? Number(days) : prev.numDays,
      budgetAmount: budget ? Number(budget) : prev.budgetAmount,
      budgetCurrency: currency || prev.budgetCurrency
    }))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname, location.search])

  // Smooth scroll helper for on-page sections
  const scrollToId = (id) => {
    const el = document.getElementById(id)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm(prev => ({ ...prev, [name]: value }))
  }

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setResult(null)
    
    // Check authentication before planning trip
    if (!auth?.user) {
      navigate('/signin?redirect=/plan')
      return
    }
    
    if (!form.originCity || !form.destinationCity) {
      setError('Please enter both origin and destination')
      return
    }
    setLoading(true)
    const timer = setInterval(() => setLoadingMsgIdx(i => (i + 1) % loadingMsgs.length), 1200)
    try {
      const payload = {
        originCity: form.originCity,
        destinationCity: form.destinationCity,
        numDays: Number(form.numDays),
        numPeople: Number(form.numPeople),
        budgetCurrency: form.budgetCurrency || 'INR',
        budgetAmount: form.budgetAmount ? Number(form.budgetAmount) : null,
        includeFoodRecos: !!form.includeFoodRecos,
        includeCommuteTimes: !!form.includeCommuteTimes
      }
      const resp = await planTrip(payload)
      setResult(resp)
    } catch (err) {
      setError(err?.message || 'Something went wrong')
    } finally {
      clearInterval(timer)
      setLoading(false)
    }
  }

  return (
    <>
      <header className="site-header">
        <div className="site-logo">
          <img src="/images/logo.png" alt="WanderWise logo" onError={(e) => { e.currentTarget.src = '/favicon.ico' }} />
          <span>WanderWise</span>
        </div>

        <nav className="nav-links">
          {location.pathname !== '/trips' && (
            <a
              href="#explore"
              onClick={(e) => {
                e.preventDefault()
                if (location.pathname === '/plan') {
                  // On plan page, scroll to explore section
                  setTimeout(() => {
                    const el = document.getElementById('explore')
                    if (el) {
                      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
                    }
                  }, 50)
                } else {
                  // On home page, scroll to explore section
                  const el = document.getElementById('explore')
                  if (el) {
                    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
                  } else {
                    // If section doesn't exist, navigate to home
                    navigate('/#explore')
                  }
                }
              }}
            >
              Explore
            </a>
          )}
          
          {!auth?.user ? (
            <Link to="/signin" className="btn-secondary" style={{ marginLeft: 16 }}>Sign In</Link>
          ) : (
            <>
              {location.pathname !== '/trips' && (
                <Link to="/trips" className="btn-secondary" style={{ marginLeft: 16 }}>My Trips</Link>
              )}
              <button className="btn-secondary" style={{ marginLeft: 8 }} onClick={() => { auth.signOut?.(); navigate('/'); }}>
                Sign Out
              </button>
            </>
          )}
        </nav>
      </header>

      <Routes>
        <Route
          path="/"
          element={
            <main className="container">
              <section className="split-hero card">
                <div className="split-hero-text">
                  <h1>
                    Plan smarter trips <br />
                    with WanderWise
                  </h1>
                  <p>
                    Instant itineraries, realistic budgets, and trusted providers — all in one place.
                  </p>
                  <div className="cta-buttons">
                    <Link to="/plan" className="btn-primary">Plan My Trip</Link>
                    <a href="#explore" className="btn-secondary" onClick={(e) => { e.preventDefault(); scrollToId('explore') }}>Explore</a>
                  </div>
                </div>
                <div>
                  <img
                    className="hero-img"
                    src="https://images.unsplash.com/photo-1500530855697-b586d89ba3ee"
                    alt="Travel destination"
                  />
                </div>
              </section>
              <section id="explore" className="card" style={{ marginTop: 48, padding: 32 }}>
                <h2 style={{ 
                  margin: 0, 
                  fontSize: 'clamp(22px, 4vw, 28px)', 
                  fontWeight: 700,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  marginBottom: 8,
                  flexWrap: 'wrap'
                }}>
                  <span>🌟</span>
                  Discover Itineraries
                </h2>
                <p className="muted" style={{ 
                  marginTop: 12, 
                  marginBottom: 24, 
                  fontSize: 'clamp(14px, 2vw, 16px)', 
                  lineHeight: 1.6 
                }}>
                  Hand-picked travel ideas to get you started. Click any trip to pre-fill the planner.
                </p>
                <div className="grid grid-2" style={{ gap: 24 }}>
                  {SAMPLE_ITINERARIES.map((it) => (
                    <div 
                      key={it.slug} 
                      className="card" 
                      style={{ 
                        padding: 24, 
                        minHeight: 280,
                        transition: 'all 0.3s ease',
                        border: '2px solid #e2e8f0',
                        cursor: 'pointer'
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
                      <div style={{ display: 'flex', gap: 16, flexDirection: 'column' }}>
                        <img 
                          src={it.image} 
                          alt={it.title} 
                          style={{ 
                            width: '100%', 
                            height: 180, 
                            objectFit: 'cover', 
                            borderRadius: 12, 
                            border: '1px solid #e5e7eb' 
                          }} 
                        />
                        <div style={{ flex: 1 }}>
                          <h3 style={{ 
                            margin: 0, 
                            fontSize: 20, 
                            fontWeight: 700,
                            color: '#1e293b',
                            marginBottom: 8
                          }}>
                            {it.title}
                          </h3>
                          <div className="muted" style={{ marginTop: 4, fontSize: 14, marginBottom: 12 }}>
                            {it.days} days · {it.style} · {it.budgetText}
                          </div>
                          <ul style={{ margin: 0, paddingLeft: 20, marginBottom: 16 }}>
                            {(it.briefPlan || []).slice(0, 3).map((p, idx) => (
                              <li key={idx} className="muted" style={{ fontSize: 14, lineHeight: 1.6, marginBottom: 4 }}>
                                {p}
                              </li>
                            ))}
                          </ul>
                          <div style={{ marginTop: 'auto' }}>
                            <Link
                              to={`/plan?origin=${encodeURIComponent(it.origin)}&dest=${encodeURIComponent(it.dest)}&days=${it.days}&budget=${it.budgetMin}&currency=${it.currency}`}
                              style={{
                                display: 'block',
                                padding: '12px 20px',
                                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                color: 'white',
                                borderRadius: 10,
                                textAlign: 'center',
                                fontWeight: 600,
                                fontSize: 15,
                                textDecoration: 'none',
                                transition: 'all 0.3s ease',
                                boxShadow: '0 4px 12px rgba(102, 126, 234, 0.3)'
                              }}
                              onMouseEnter={(e) => {
                                e.currentTarget.style.transform = 'scale(1.02)'
                                e.currentTarget.style.boxShadow = '0 6px 16px rgba(102, 126, 234, 0.4)'
                              }}
                              onMouseLeave={(e) => {
                                e.currentTarget.style.transform = 'scale(1)'
                                e.currentTarget.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.3)'
                              }}
                            >
                              Plan this trip →
                            </Link>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            </main>
          }
        />
        <Route
          path="/plan"
          element={
            !auth?.user ? (
              <main className="container">
                <div className="card" style={{ marginTop: 64, padding: 48, maxWidth: 600, marginLeft: 'auto', marginRight: 'auto', textAlign: 'center' }}>
                  <div style={{ fontSize: 64, marginBottom: 24 }}>🔒</div>
                  <h2 style={{ margin: 0, fontSize: 28, fontWeight: 700, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>
                    Sign In Required
                  </h2>
                  <p className="muted" style={{ marginTop: 16, fontSize: 16, lineHeight: 1.6 }}>
                    Please sign in to create and save your travel itineraries. Your trips will be saved automatically so you can access them anytime.
                  </p>
                  <div style={{ marginTop: 32, display: 'flex', gap: 12, justifyContent: 'center' }}>
                    <Link to="/signin" className="btn-primary">Sign In</Link>
                  </div>
                </div>
              </main>
            ) : (
            <main className="container">
              <div className="itinerary-form-card" style={{ marginTop: 32 }}>
                <div className="form-header" style={{ marginBottom: 32 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
                    <span style={{ fontSize: 32 }}>✈️</span>
                    <h2 style={{ margin: 0, fontSize: 32, fontWeight: 700, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>
                      Build your itinerary
                    </h2>
                  </div>
                  <p className="form-subtitle" style={{ marginTop: 8, fontSize: 16, color: '#64748b' }}>
                    Plan your perfect trip in seconds — just enter the basics and let us create a personalized itinerary for you
                  </p>
                </div>
                <form onSubmit={submit} className="planner-form">
                  <div className="form-section">
                    <div className="section-label">📍 Trip Details</div>
                    <div className="grid-2" style={{ gap: 20, width: '100%' }}>
                      <div className="field-wrapper" style={{ width: '100%' }}>
                        <AutocompleteInput
                          label="Origin City"
                          placeholder="e.g., New Delhi, India"
                          value={form.originCity}
                          onSelect={(val) => setForm(prev => ({ ...prev, originCity: val }))}
                        />
                      </div>
                      <div className="field-wrapper" style={{ width: '100%' }}>
                        <AutocompleteInput
                          label="Destination City"
                          placeholder="e.g., Jaipur, India"
                          value={form.destinationCity}
                          onSelect={(val) => setForm(prev => ({ ...prev, destinationCity: val }))}
                        />
                      </div>
                    </div>
                  </div>

                  <div className="form-section" style={{ marginTop: 28 }}>
                    <div className="section-label">📅 Travel Preferences</div>
                    <div className="preferences-grid">
                      <div className="field-wrapper">
                        <label className="field-label">
                          <span className="label-icon">📆</span>
                          Days
                        </label>
                        <input 
                          name="numDays" 
                          type="number" 
                          min="1" 
                          max="30" 
                          value={form.numDays} 
                          onChange={handleChange}
                          className="form-input"
                          placeholder="Number of days"
                        />
                      </div>
                      <div className="field-wrapper">
                        <label className="field-label">
                          <span className="label-icon">👥</span>
                          People
                        </label>
                        <input 
                          name="numPeople" 
                          type="number" 
                          min="1" 
                          max="20" 
                          value={form.numPeople} 
                          onChange={handleChange}
                          className="form-input"
                          placeholder="Number of travelers"
                        />
                      </div>
                      <div className="field-wrapper">
                        <label className="field-label">
                          <span className="label-icon">💱</span>
                          Budget Currency
                        </label>
                        <select 
                          name="budgetCurrency" 
                          value={form.budgetCurrency} 
                          onChange={handleChange}
                          className="form-select"
                        >
                          <option>INR</option>
                          <option>USD</option>
                          <option>EUR</option>
                          <option>GBP</option>
                        </select>
                      </div>
                      <div className="field-wrapper">
                        <label className="field-label">
                          <span className="label-icon">💰</span>
                          Total Budget (optional)
                        </label>
                        <input 
                          name="budgetAmount" 
                          type="number" 
                          min="0" 
                          placeholder="e.g., 120000" 
                          value={form.budgetAmount} 
                          onChange={handleChange}
                          className="form-input"
                        />
                      </div>
                    </div>
                  </div>

                  <div className="form-section" style={{ marginTop: 28 }}>
                    <div className="section-label">✨ Additional Options</div>
                    <div className="checkbox-group">
                      <label className="checkbox-label">
                        <input 
                          type="checkbox" 
                          checked={!!form.includeFoodRecos} 
                          onChange={(e) => setForm(prev => ({ ...prev, includeFoodRecos: e.target.checked }))}
                          className="styled-checkbox"
                        />
                        <span className="checkbox-content">
                          <span className="checkbox-icon">🍽️</span>
                          <span>
                            <strong>Include food recommendations</strong>
                            <small>Get local cuisine suggestions and restaurant tips</small>
                          </span>
                        </span>
                      </label>
                      <label className="checkbox-label">
                        <input 
                          type="checkbox" 
                          checked={!!form.includeCommuteTimes} 
                          onChange={(e) => setForm(prev => ({ ...prev, includeCommuteTimes: e.target.checked }))}
                          className="styled-checkbox"
                        />
                        <span className="checkbox-content">
                          <span className="checkbox-icon">🚇</span>
                          <span>
                            <strong>Include commute times/modes</strong>
                            <small>Show transportation details between locations</small>
                          </span>
                        </span>
                      </label>
                    </div>
                  </div>

                  <div className="planner-actions" style={{ marginTop: 36 }}>
                    <button 
                      className="btn-plan-trip" 
                      type="submit" 
                      disabled={loading}
                      style={{ 
                        background: loading ? '#94a3b8' : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        cursor: loading ? 'not-allowed' : 'pointer',
                        opacity: loading ? 0.7 : 1
                      }}
                    >
                      {loading ? (
                        <>
                          <span className="spinner-btn" style={{ marginRight: 10 }}></span>
                          Planning your trip...
                        </>
                      ) : (
                        <>
                          <span style={{ marginRight: 10, fontSize: 20 }}>🚀</span>
                          Plan My Trip
                        </>
                      )}
                    </button>
                  </div>
                  {loading && (
                    <div className="loading-banner">
                      <div className="spinner" />
                      <div style={{ fontSize: 15, color: '#64748b' }}>
                        {`${travelEmojis[loadingMsgIdx % travelEmojis.length]} ${loadingMsgs[loadingMsgIdx]}`}
                      </div>
                    </div>
                  )}
                </form>
              </div>
              {error && (
                <div className="error-card" style={{ marginTop: 24 }}>
                  <span style={{ marginRight: 8 }}>⚠️</span>
                  <strong>Error:</strong> {error}
                </div>
              )}
              {result && (
                <div className="card" style={{ marginTop: 24 }}>
                  <ItineraryView data={result} />
                </div>
              )}
              
              {/* Explore Section on Plan Page */}
              <section id="explore" className="card" style={{ marginTop: 48, padding: 32 }}>
                <h2 style={{ 
                  margin: 0, 
                  fontSize: 28, 
                  fontWeight: 700,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  marginBottom: 8
                }}>
                  <span>🌟</span>
                  Discover Itineraries
                </h2>
                <p className="muted" style={{ marginTop: 12, marginBottom: 24, fontSize: 16, lineHeight: 1.6 }}>
                  Hand-picked travel ideas to get you started. Click any trip to pre-fill the planner above.
                </p>
                <div className="grid grid-2" style={{ gap: 24 }}>
                  {SAMPLE_ITINERARIES.map((it) => (
                    <div 
                      key={it.slug} 
                      className="card" 
                      style={{ 
                        padding: 24, 
                        minHeight: 280,
                        transition: 'all 0.3s ease',
                        border: '2px solid #e2e8f0',
                        cursor: 'pointer'
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
                      onClick={() => {
                        setForm(prev => ({
                          ...prev,
                          originCity: it.origin,
                          destinationCity: it.dest,
                          numDays: it.days,
                          budgetAmount: it.budgetMin,
                          budgetCurrency: it.currency
                        }))
                        // Scroll to top of form
                        const formCard = document.querySelector('.itinerary-form-card')
                        if (formCard) {
                          formCard.scrollIntoView({ behavior: 'smooth', block: 'start' })
                        }
                      }}
                    >
                      <div style={{ display: 'flex', gap: 16, flexDirection: 'column' }}>
                        <img 
                          src={it.image} 
                          alt={it.title} 
                          style={{ 
                            width: '100%', 
                            height: 180, 
                            objectFit: 'cover', 
                            borderRadius: 12, 
                            border: '1px solid #e5e7eb' 
                          }} 
                        />
                        <div style={{ flex: 1 }}>
                          <h3 style={{ 
                            margin: 0, 
                            fontSize: 20, 
                            fontWeight: 700,
                            color: '#1e293b',
                            marginBottom: 8
                          }}>
                            {it.title}
                          </h3>
                          <div className="muted" style={{ marginTop: 4, fontSize: 14, marginBottom: 12 }}>
                            {it.days} days · {it.style} · {it.budgetText}
                          </div>
                          <ul style={{ margin: 0, paddingLeft: 20, marginBottom: 16 }}>
                            {(it.briefPlan || []).slice(0, 3).map((p, idx) => (
                              <li key={idx} className="muted" style={{ fontSize: 14, lineHeight: 1.6, marginBottom: 4 }}>
                                {p}
                              </li>
                            ))}
                          </ul>
                          <div style={{ 
                            marginTop: 'auto',
                            padding: '12px 20px',
                            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                            color: 'white',
                            borderRadius: 10,
                            textAlign: 'center',
                            fontWeight: 600,
                            fontSize: 15,
                            transition: 'all 0.3s ease'
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.transform = 'scale(1.02)'
                            e.currentTarget.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.3)'
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.transform = 'scale(1)'
                            e.currentTarget.style.boxShadow = 'none'
                          }}
                          >
                            Use this trip →
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            </main>
            )
          }
        />
        <Route path="/signin" element={<SignInPage />} />
        <Route path="/trips" element={<TripsPage />} />
      </Routes>
    </>
  )
}

// Simple curated examples (can be moved to a separate file later)
const SAMPLE_ITINERARIES = [
  {
    slug: 'jaipur-5d',
    title: '5 Days in Jaipur',
    origin: 'New Delhi, IN',
    dest: 'Jaipur, IN',
    days: 5,
    budgetMin: 18000,
    currency: 'INR',
    budgetText: '₹18k–₹35k',
    style: 'Heritage & Food',
    briefPlan: ['City Palace & Hawa Mahal', 'Amer Fort + Stepwell', 'Pink City walk + local kachori'],
    image: '/images/jaipur.jpg'
  },
  {
    slug: 'goa-budget',
    title: 'Goa on a Budget',
    origin: 'Mumbai, IN',
    dest: 'Goa, IN',
    days: 4,
    budgetMin: 15000,
    currency: 'INR',
    budgetText: '₹15k–₹28k',
    style: 'Beaches & Cafes',
    briefPlan: ['Candolim & Baga beaches', 'Fort Aguada sunset', 'Fontainhas cafes'],
    image: '/images/goa.jpg'
  },
  {
    slug: 'kerala-backwaters',
    title: 'Kerala Backwaters',
    origin: 'Bengaluru, IN',
    dest: 'Alleppey, IN',
    days: 5,
    budgetMin: 22000,
    currency: 'INR',
    budgetText: '₹22k–₹40k',
    style: 'Relaxed & Nature',
    briefPlan: ['Houseboat cruise', 'Kumarakom birdwatching', 'Ayurvedic spa evening'],
    image: '/images/kerala.jpg'
  },
  {
    slug: 'delhi-weekend',
    title: 'Weekend from Delhi',
    origin: 'New Delhi, IN',
    dest: 'Rishikesh, IN',
    days: 2,
    budgetMin: 8000,
    currency: 'INR',
    budgetText: '₹8k–₹15k',
    style: 'Weekend',
    briefPlan: ['Ganga aarti', 'Lakshman Jhula & cafes', 'Short riverside hike'],
    image: '/images/delhi.jpg'
  }
] 


