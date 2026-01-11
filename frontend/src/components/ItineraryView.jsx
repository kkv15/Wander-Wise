import React from 'react'

export default function ItineraryView({ data }) {
  const est = data.estimatedTotals || {}
  
  const fmt = (currency, value) => {
    if (value == null) return '-'
    try {
      return new Intl.NumberFormat('en-IN', { 
        style: 'currency', 
        currency: currency || 'INR', 
        maximumFractionDigits: 0 
      }).format(value)
    } catch {
      return `${currency || ''} ${value}`
    }
  }

  const truncate = (text, n) => {
    if (!text) return ''
    return text.length > n ? text.slice(0, n - 1) + '…' : text
  }

  // Format daily plan items: bold timings and places
  const formatDailyPlanItem = (text) => {
    if (!text) return text
    
    let formatted = text
    
    // First, bold time patterns like "Morning (9:00 AM - 12:00 PM):", "Afternoon (1:00 PM - 5:00 PM):", etc.
    // This matches the full pattern including the colon
    formatted = formatted.replace(/((?:Morning|Afternoon|Evening|Early\s+Morning|Late\s+Evening|Night)\s*(?:\([^\)]+\))?\s*:)/gi, '<strong style="font-weight: 700; color: #667eea;">$1</strong>')
    
    // Also bold standalone time references like "9:00 AM", "12:30 PM", etc.
    formatted = formatted.replace(/(\d{1,2}:\d{2}\s*(?:AM|PM))/gi, '<strong style="font-weight: 700; color: #667eea;">$1</strong>')
    
    // Bold time ranges like "9:00 AM - 12:00 PM"
    formatted = formatted.replace(/(\d{1,2}:\d{2}\s*(?:AM|PM)\s*-\s*\d{1,2}:\d{2}\s*(?:AM|PM))/gi, '<strong style="font-weight: 700; color: #667eea;">$1</strong>')
    
    // Bold place names - common patterns: Proper noun + keyword (Fort, Palace, Temple, etc.)
    const placeKeywords = ['Fort', 'Palace', 'Temple', 'Museum', 'Market', 'Park', 'Beach', 'Lake', 'Gate', 'Tower', 'Square', 'Garden', 'Monument', 'Stadium', 'Airport', 'Station', 'City', 'Bazaar', 'Bazar', 'Mandir', 'Mahal', 'Kund', 'Kundan', 'Village', 'Town', 'Resort', 'Hotel', 'Restaurant', 'Cafe', 'Bridge', 'Cathedral', 'Church', 'Mosque', 'Gurudwara', 'Ashram']
    
    placeKeywords.forEach(keyword => {
      // Match capitalized words before the keyword
      formatted = formatted.replace(new RegExp(`\\b([A-Z][a-z]+(?:\\s+[A-Z][a-z]+)*)\\s+${keyword}\\b`, 'g'), '<strong style="font-weight: 700; color: #1e293b;">$1 ' + keyword + '</strong>')
    })
    
    // Bold popular multi-word attractions
    const popularAttractions = [
      'Taj Mahal', 'Golden Temple', 'Gateway of India', 'India Gate', 'Hawa Mahal', 'Amber Fort', 
      'City Palace', 'Red Fort', 'Agra Fort', 'Meenakshi Temple', 'Lotus Temple', 'Qutub Minar',
      'Charminar', 'Victoria Memorial', 'Jantar Mantar', 'Laxmi Vilas Palace', 'Mysore Palace',
      'Bangalore Palace', 'Umaid Bhawan Palace', 'Lake Palace', 'Rambagh Palace'
    ]
    
    popularAttractions.forEach(attraction => {
      formatted = formatted.replace(new RegExp(`\\b(${attraction.replace(/\s+/g, '\\s+')})\\b`, 'gi'), '<strong style="font-weight: 700; color: #1e293b;">$1</strong>')
    })
    
    // Bold capitalized place names that appear after "Visit", "Explore", "Head to", etc.
    formatted = formatted.replace(/\b(?:Visit|Explore|Head to|Go to|See|Check out|Tour)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b/gi, (match, place) => {
      // Don't bold if it's too long (likely a sentence)
      if (place.split(/\s+/).length <= 4) {
        return match.replace(place, `<strong style="font-weight: 700; color: #1e293b;">${place}</strong>`)
      }
      return match
    })
    
    return <span dangerouslySetInnerHTML={{ __html: formatted }} />
  }

  return (
    <div style={{ width: '100%' }}>
      {/* Header Section */}
      <div style={{ 
        marginBottom: 32,
        paddingBottom: 24,
        borderBottom: '2px solid #e2e8f0'
      }}>
        <h2 style={{ 
          margin: 0, 
          fontSize: 32, 
          fontWeight: 700, 
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
          WebkitBackgroundClip: 'text', 
          WebkitTextFillColor: 'transparent', 
          backgroundClip: 'text',
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          marginBottom: 12
        }}>
          <span>✈️</span>
          Suggested Itinerary
        </h2>
        <p style={{ 
          fontSize: 16, 
          color: '#64748b', 
          lineHeight: 1.6, 
          margin: 0,
          maxWidth: '90%'
        }}>
          {data.summary}
        </p>
      </div>

      {/* Flights/Train Section */}
      {data.train?.available && (
        <section className="itinerary-section" style={{ marginTop: 24 }}>
          <div className="section-header">
            <span style={{ fontSize: 24, marginRight: 8 }}>🚂</span>
            <h3>Train (Estimated)</h3>
          </div>
          <div className="info-card">
            <div style={{ marginBottom: 16 }}>
              <span style={{ 
                padding: '6px 12px', 
                background: 'linear-gradient(135deg, #f0f4ff 0%, #fef0ff 100%)',
                borderRadius: 8,
                fontSize: 14,
                fontWeight: 600,
                color: '#667eea'
              }}>
                ✓ Available (India, short-distance)
              </span>
            </div>
            <div style={{ display: 'grid', gap: 12 }}>
              {Object.entries(data.train?.classes || {}).map(([cls, info]) => (
                <div key={cls} style={{
                  padding: 16,
                  background: 'linear-gradient(135deg, #ffffff 0%, #fafbfc 100%)',
                  border: '1px solid #e2e8f0',
                  borderRadius: 12,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <div>
                    <strong style={{ fontSize: 16, color: '#1e293b' }}>{cls}</strong>
                    <div style={{ fontSize: 13, color: '#64748b', marginTop: 4 }}>
                      ~{info.estDurationHours}h journey
                    </div>
                  </div>
                  <div style={{ 
                    fontSize: 18, 
                    fontWeight: 700, 
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
                    WebkitBackgroundClip: 'text', 
                    WebkitTextFillColor: 'transparent', 
                    backgroundClip: 'text'
                  }}>
                    {fmt(info.currency, info.estFarePerPerson)} per person
                  </div>
                </div>
              ))}
            </div>
            <div style={{ marginTop: 20 }}>
              <a
                href="https://www.irctc.co.in/nget/train-search"
                target="_blank"
                rel="noreferrer"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '14px 28px',
                  background: 'linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)',
                  color: 'white',
                  borderRadius: 12,
                  fontSize: '1rem',
                  fontWeight: 700,
                  textDecoration: 'none',
                  transition: 'all 0.3s ease',
                  boxShadow: '0 4px 12px rgba(220, 38, 38, 0.3)',
                  width: '100%',
                  justifyContent: 'center'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-2px)'
                  e.currentTarget.style.boxShadow = '0 6px 16px rgba(220, 38, 38, 0.4)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)'
                  e.currentTarget.style.boxShadow = '0 4px 12px rgba(220, 38, 38, 0.3)'
                }}
              >
                <span>🚂</span>
                Book Train on IRCTC
              </a>
            </div>
            {data.train?.note && (
              <div style={{ 
                marginTop: 16, 
                padding: 12, 
                background: 'linear-gradient(135deg, #f0f4ff 0%, #fef0ff 100%)',
                borderRadius: 10,
                fontSize: 14,
                color: '#475569',
                border: '1px solid #e2e8f0'
              }}>
                {data.train.note}
              </div>
            )}
          </div>
        </section>
      )}

      {!data.train?.available && (
        <section className="itinerary-section" style={{ marginTop: 24 }}>
          <div className="section-header">
            <span style={{ fontSize: 24, marginRight: 8 }}>✈️</span>
            <h3>Flights (Estimated)</h3>
          </div>
          <div className="info-card">
            <div style={{ display: 'grid', gap: 16 }}>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: 16,
                background: 'linear-gradient(135deg, #ffffff 0%, #fafbfc 100%)',
                border: '1px solid #e2e8f0',
                borderRadius: 12
              }}>
                <div>
                  <div style={{ fontSize: 13, color: '#64748b', marginBottom: 4 }}>Origin Airport</div>
                  <div style={{ fontSize: 16, fontWeight: 600, color: '#1e293b' }}>
                    {data.flights?.originAirport || '-'}
                  </div>
                </div>
                <div style={{ fontSize: 24, color: '#cbd5e1' }}>→</div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 13, color: '#64748b', marginBottom: 4 }}>Destination Airport</div>
                  <div style={{ fontSize: 16, fontWeight: 600, color: '#1e293b' }}>
                    {data.flights?.destinationAirport || '-'}
                  </div>
                </div>
              </div>
              <div style={{
                padding: 20,
                background: 'linear-gradient(135deg, #f0f4ff 0%, #fef0ff 100%)',
                border: '2px solid #667eea',
                borderRadius: 14,
                textAlign: 'center'
              }}>
                <div style={{ fontSize: 13, color: '#64748b', marginBottom: 8 }}>Round Trip per Person</div>
                <div style={{ 
                  fontSize: 28, 
                  fontWeight: 700, 
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
                  WebkitBackgroundClip: 'text', 
                  WebkitTextFillColor: 'transparent', 
                  backgroundClip: 'text',
                  marginBottom: 16
                }}>
                  {fmt(est.currency || data.flights?.currency, data.flights?.estimatedRoundTripPerPerson)}
                </div>
                {data.flights?.skyscanner_link && (
                  <a
                    href={data.flights.skyscanner_link}
                    target="_blank"
                    rel="noreferrer"
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 8,
                      padding: '14px 28px',
                      background: 'linear-gradient(135deg, #0d7377 0%, #14a085 100%)',
                      color: 'white',
                      borderRadius: 12,
                      fontSize: '1rem',
                      fontWeight: 700,
                      textDecoration: 'none',
                      transition: 'all 0.3s ease',
                      boxShadow: '0 4px 12px rgba(13, 115, 119, 0.3)',
                      width: '100%',
                      justifyContent: 'center'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.transform = 'translateY(-2px)'
                      e.currentTarget.style.boxShadow = '0 6px 16px rgba(13, 115, 119, 0.4)'
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.transform = 'translateY(0)'
                      e.currentTarget.style.boxShadow = '0 4px 12px rgba(13, 115, 119, 0.3)'
                    }}
                  >
                    <span>✈️</span>
                    Book Flights on Skyscanner
                  </a>
                )}
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Hotels Section */}
      {!data.hotels?.hotels_by_day && (
        <section className="itinerary-section" style={{ marginTop: 32 }}>
          <div className="section-header">
            <span style={{ fontSize: 24, marginRight: 8 }}>🏨</span>
            <h3>Hotels by Location</h3>
          </div>
          {data.hotels?.hotels_by_city ? (
            Object.entries(data.hotels.hotels_by_city).map(([city, cityHotels]) => (
              <div key={city} style={{ marginBottom: 32 }}>
                <h4 style={{ 
                  marginBottom: 16, 
                  fontSize: 18, 
                  fontWeight: 700,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
                  WebkitBackgroundClip: 'text', 
                  WebkitTextFillColor: 'transparent', 
                  backgroundClip: 'text',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8
                }}>
                  <span>📍</span>
                  Hotels in {city}
                </h4>
                <div className="grid grid-2" style={{ gap: 20 }}>
                  {(cityHotels || []).slice(0, 4).map(h => (
                    <div key={h.place_id} className="hotel-card">
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                        <div style={{ flex: 1 }}>
                          <h5 style={{ 
                            margin: 0, 
                            fontSize: 16, 
                            fontWeight: 700, 
                            color: '#1e293b',
                            marginBottom: 6,
                            lineHeight: 1.3
                          }}>
                            {h.name}
                          </h5>
                          {h.stars && (
                            <div style={{ color: '#fbbf24', fontSize: 14 }}>
                              {'★'.repeat(Math.round(h.stars))}
                            </div>
                          )}
                        </div>
                      </div>
                      <div style={{ 
                        fontSize: 13, 
                        color: '#64748b', 
                        marginBottom: 12,
                        lineHeight: 1.5
                      }}>
                        {truncate(h.address, 80)}
                      </div>
                      {h.rating != null && (
                        <div style={{ 
                          marginBottom: 12,
                          display: 'flex',
                          alignItems: 'center',
                          gap: 8
                        }}>
                          <span style={{ fontSize: 16 }}>⭐</span>
                          <span style={{ fontSize: 15, fontWeight: 600, color: '#1e293b' }}>
                            {h.rating.toFixed(1)}
                          </span>
                          <span style={{ fontSize: 13, color: '#64748b' }}>
                            ({h.user_ratings_total || 0} reviews)
                          </span>
                        </div>
                      )}
                      {h.price_level != null && (
                        <div style={{ 
                          marginBottom: 12,
                          fontSize: 14,
                          color: '#64748b'
                        }}>
                          Price level: <span style={{ color: '#fbbf24' }}>{'₹'.repeat(h.price_level + 1)}</span>
                        </div>
                      )}
                      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 16 }}>
                        {h.booking_links?.booking_hotel && (
                          <a
                            href={h.booking_links.booking_hotel}
                            target="_blank"
                            rel="noreferrer"
                            className="btn-booking"
                            style={{
                              padding: '10px 16px',
                              background: 'linear-gradient(135deg, #003580 0%, #004a9f 100%)',
                              color: 'white',
                              borderRadius: 10,
                              fontSize: '0.875rem',
                              fontWeight: 600,
                              textDecoration: 'none',
                              transition: 'all 0.3s ease',
                              display: 'inline-block',
                              boxShadow: '0 4px 12px rgba(0, 53, 128, 0.3)'
                            }}
                            onMouseEnter={(e) => {
                              e.currentTarget.style.transform = 'translateY(-2px)'
                              e.currentTarget.style.boxShadow = '0 6px 16px rgba(0, 53, 128, 0.4)'
                            }}
                            onMouseLeave={(e) => {
                              e.currentTarget.style.transform = 'translateY(0)'
                              e.currentTarget.style.boxShadow = '0 4px 12px rgba(0, 53, 128, 0.3)'
                            }}
                            title="Search for this hotel on Booking.com (includes city name)"
                          >
                            Book on Booking.com
                          </a>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))
          ) : (
            <div className="grid grid-2" style={{ gap: 20 }}>
              {(data.hotels?.hotels || []).map(h => (
                <div key={h.place_id} className="hotel-card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                    <div style={{ flex: 1 }}>
                      <h5 style={{ 
                        margin: 0, 
                        fontSize: 16, 
                        fontWeight: 700, 
                        color: '#1e293b',
                        marginBottom: 6
                      }}>
                        {h.name}
                      </h5>
                      {h.stars && (
                        <div style={{ color: '#fbbf24', fontSize: 14 }}>
                          {'★'.repeat(Math.round(h.stars))}
                        </div>
                      )}
                    </div>
                  </div>
                  <div style={{ fontSize: 13, color: '#64748b', marginBottom: 12 }}>
                    {truncate(h.address, 80)}
                  </div>
                  {h.rating != null && (
                    <div style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ fontSize: 16 }}>⭐</span>
                      <span style={{ fontSize: 15, fontWeight: 600, color: '#1e293b' }}>
                        {h.rating.toFixed(1)}
                      </span>
                      <span style={{ fontSize: 13, color: '#64748b' }}>
                        ({h.user_ratings_total || 0} reviews)
                      </span>
                    </div>
                  )}
                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 16 }}>
                    {h.booking_links?.booking_hotel && (
                      <a
                        href={h.booking_links.booking_hotel}
                        target="_blank"
                        rel="noreferrer"
                        className="btn-booking"
                        style={{
                          padding: '10px 16px',
                          background: 'linear-gradient(135deg, #003580 0%, #004a9f 100%)',
                          color: 'white',
                          borderRadius: 10,
                          fontSize: '0.875rem',
                          fontWeight: 600,
                          textDecoration: 'none',
                          transition: 'all 0.3s ease',
                          display: 'inline-block',
                          boxShadow: '0 4px 12px rgba(0, 53, 128, 0.3)'
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.transform = 'translateY(-2px)'
                          e.currentTarget.style.boxShadow = '0 6px 16px rgba(0, 53, 128, 0.4)'
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.transform = 'translateY(0)'
                          e.currentTarget.style.boxShadow = '0 4px 12px rgba(0, 53, 128, 0.3)'
                        }}
                      >
                        Book on Booking.com
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {/* City-level Booking Links */}
      {data.hotels?.city_links?.booking_city && (
        <section className="itinerary-section" style={{ marginTop: 32 }}>
          <div className="section-header">
            <span style={{ fontSize: 24, marginRight: 8 }}>🔍</span>
            <h3>Find Top Hotels in City</h3>
          </div>
          <div className="info-card" style={{
            background: 'linear-gradient(135deg, #f0f4ff 0%, #fef0ff 100%)',
            border: '2px solid #667eea',
            padding: 24
          }}>
            <div style={{ marginBottom: 16, fontSize: 15, color: '#475569', lineHeight: 1.6 }}>
              Browse top-rated hotels in the destination city. City name is automatically included to avoid login prompts.
            </div>
            <a
              href={data.hotels.city_links.booking_city}
              target="_blank"
              rel="noreferrer"
              className="btn-booking"
              style={{
                padding: '14px 24px',
                background: 'linear-gradient(135deg, #003580 0%, #004a9f 100%)',
                color: 'white',
                borderRadius: 12,
                fontSize: '1rem',
                fontWeight: 700,
                textDecoration: 'none',
                transition: 'all 0.3s ease',
                display: 'inline-block',
                boxShadow: '0 4px 16px rgba(0, 53, 128, 0.3)'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px)'
                e.currentTarget.style.boxShadow = '0 6px 20px rgba(0, 53, 128, 0.4)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)'
                e.currentTarget.style.boxShadow = '0 4px 16px rgba(0, 53, 128, 0.3)'
              }}
            >
              Browse Hotels on Booking.com
            </a>
          </div>
        </section>
      )}

      {/* Top Attractions */}
      {data.attractions && data.attractions.length > 0 && (
        <section className="itinerary-section" style={{ marginTop: 32 }}>
          <div className="section-header">
            <span style={{ fontSize: 24, marginRight: 8 }}>🎯</span>
            <h3>Top Attractions</h3>
          </div>
          <div className="grid grid-2" style={{ gap: 20 }}>
            {(data.attractions || []).slice(0, 8).map(a => (
              <div key={a.place_id} className="attraction-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: 12 }}>
                  <h4 style={{ 
                    margin: 0, 
                    fontSize: 16, 
                    fontWeight: 700, 
                    color: '#1e293b',
                    lineHeight: 1.3,
                    flex: 1
                  }}>
                    {a.name}
                  </h4>
                  {a.url && (
                    <a 
                      href={a.url} 
                      target="_blank" 
                      rel="noreferrer"
                      style={{
                        padding: '6px 12px',
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        color: 'white',
                        borderRadius: 8,
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        textDecoration: 'none',
                        marginLeft: 8,
                        transition: 'all 0.3s ease'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.transform = 'translateY(-2px)'
                        e.currentTarget.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.3)'
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.transform = 'translateY(0)'
                        e.currentTarget.style.boxShadow = 'none'
                      }}
                    >
                      Open
                    </a>
                  )}
                </div>
                {a.description && (
                  <div style={{ 
                    fontSize: 14, 
                    color: '#64748b', 
                    lineHeight: 1.6,
                    marginBottom: 12
                  }}>
                    {truncate(a.description, 220)}
                  </div>
                )}
                {(a.openingHours || a.bestTimeToVisit) && (
                  <div style={{ 
                    padding: 12,
                    background: 'linear-gradient(135deg, #fafbfc 0%, #f1f5f9 100%)',
                    borderRadius: 10,
                    fontSize: 13,
                    color: '#475569',
                    border: '1px solid #e2e8f0'
                  }}>
                    {a.openingHours && (
                      <div style={{ marginBottom: 6 }}>
                        <strong>Hours:</strong> {a.openingHours}
                      </div>
                    )}
                    {a.bestTimeToVisit && (
                      <div>
                        <strong>Best time:</strong> {a.bestTimeToVisit}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Daily Plan */}
      {data.dailyPlan && data.dailyPlan.length > 0 && (
        <section className="itinerary-section" style={{ marginTop: 32 }}>
          <div className="section-header">
            <span style={{ fontSize: 24, marginRight: 8 }}>📅</span>
            <h3>Daily Plan</h3>
          </div>
          <div className="grid grid-2" style={{ gap: 20 }}>
            {(data.dailyPlan || []).map(d => {
              const dayHotels = data.hotels?.hotels_by_day?.[d.day] || []
              return (
                <div key={d.day} className="day-card">
                  <div style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    height: 4,
                    background: 'linear-gradient(90deg, #667eea 0%, #764ba2 100%)',
                    borderRadius: '12px 12px 0 0'
                  }} />
                  <div style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: 8, 
                    marginBottom: 16,
                    paddingTop: 8
                  }}>
                    <span style={{ 
                      fontSize: 20, 
                      fontWeight: 700, 
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
                      WebkitBackgroundClip: 'text', 
                      WebkitTextFillColor: 'transparent', 
                      backgroundClip: 'text'
                    }}>
                      Day {d.day}
                    </span>
                  </div>
                  <ul style={{ 
                    listStyle: 'none', 
                    padding: 0, 
                    margin: 0,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 12
                  }}>
                    {(d.items || []).map((item, idx) => (
                      <li key={idx} style={{
                        padding: 14,
                        background: 'linear-gradient(135deg, #ffffff 0%, #fafbfc 100%)',
                        border: '1px solid #e2e8f0',
                        borderRadius: 10,
                        fontSize: 14,
                        color: '#475569',
                        lineHeight: 1.6
                      }}>
                        {formatDailyPlanItem(item)}
                      </li>
                    ))}
                  </ul>
                  {dayHotels.length > 0 && (
                    <div style={{ 
                      marginTop: 20, 
                      paddingTop: 20, 
                      borderTop: '2px solid #e2e8f0' 
                    }}>
                      <div style={{ 
                        marginBottom: 12, 
                        fontWeight: 700, 
                        fontSize: 15,
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
                        WebkitBackgroundClip: 'text', 
                        WebkitTextFillColor: 'transparent', 
                        backgroundClip: 'text',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6
                      }}>
                        <span>🏨</span>
                        Hotels for Day {d.day}
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                        {dayHotels.slice(0, 2).map(h => (
                          <div key={h.place_id || h.name} style={{ 
                            padding: 12, 
                            background: 'linear-gradient(135deg, #f0f4ff 0%, #fef0ff 100%)', 
                            borderRadius: 10, 
                            border: '1px solid #e2e8f0'
                          }}>
                            <div style={{ fontWeight: 600, marginBottom: 6, fontSize: 14, color: '#1e293b' }}>
                              {h.name}
                            </div>
                            {h.address && (
                              <div style={{ fontSize: 12, color: '#64748b', marginBottom: 6 }}>
                                {truncate(h.address, 60)}
                              </div>
                            )}
                            {h.rating != null && (
                              <div style={{ fontSize: 12, marginBottom: 8, color: '#475569' }}>
                                ⭐ {h.rating.toFixed(1)}
                              </div>
                            )}
                            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                              {h.booking_links?.booking_hotel && (
                                <a 
                                  href={h.booking_links.booking_hotel} 
                                  target="_blank" 
                                  rel="noreferrer" 
                                  style={{ 
                                    padding: '6px 12px', 
                                    background: 'linear-gradient(135deg, #003580 0%, #004a9f 100%)', 
                                    color: 'white', 
                                    borderRadius: 8, 
                                    fontSize: '0.7rem', 
                                    fontWeight: 600,
                                    textDecoration: 'none',
                                    transition: 'all 0.3s ease'
                                  }}
                                  onMouseEnter={(e) => {
                                    e.currentTarget.style.transform = 'translateY(-1px)'
                                    e.currentTarget.style.boxShadow = '0 2px 8px rgba(0, 53, 128, 0.3)'
                                  }}
                                  onMouseLeave={(e) => {
                                    e.currentTarget.style.transform = 'translateY(0)'
                                    e.currentTarget.style.boxShadow = 'none'
                                  }}
                                >
                                  Booking.com
                                </a>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </section>
      )}

      {/* Estimated Totals */}
      {est && (
        <section className="itinerary-section" style={{ marginTop: 32 }}>
          <div className="section-header">
            <span style={{ fontSize: 24, marginRight: 8 }}>💰</span>
            <h3>Estimated Totals</h3>
          </div>
          <div className="grid grid-2" style={{ gap: 16 }}>
            {est.flights != null && est.flights !== 0 && (
              <div className="cost-card">
                <div style={{ fontSize: 13, color: '#64748b', marginBottom: 6 }}>Flights</div>
                <div style={{ fontSize: 20, fontWeight: 700, color: '#1e293b' }}>
                  {fmt(est.currency, est.flights)}
                </div>
              </div>
            )}
            {est.train != null && est.train !== 0 && (
              <div className="cost-card">
                <div style={{ fontSize: 13, color: '#64748b', marginBottom: 6 }}>Train</div>
                <div style={{ fontSize: 20, fontWeight: 700, color: '#1e293b' }}>
                  {fmt(est.currency, est.train)}
                </div>
              </div>
            )}
            <div className="cost-card">
              <div style={{ fontSize: 13, color: '#64748b', marginBottom: 6 }}>Hotels</div>
              <div style={{ fontSize: 20, fontWeight: 700, color: '#1e293b' }}>
                {fmt(est.currency, est.hotels)}
              </div>
            </div>
            <div className="cost-card">
              <div style={{ fontSize: 13, color: '#64748b', marginBottom: 6 }}>Activities</div>
              <div style={{ fontSize: 20, fontWeight: 700, color: '#1e293b' }}>
                {fmt(est.currency, est.activities)}
              </div>
            </div>
            <div className="cost-card">
              <div style={{ fontSize: 13, color: '#64748b', marginBottom: 6 }}>Food/Transport/Misc</div>
              <div style={{ fontSize: 20, fontWeight: 700, color: '#1e293b' }}>
                {fmt(est.currency, est.foodTransportMisc)}
              </div>
            </div>
            <div className="cost-card" style={{
              background: 'linear-gradient(135deg, #f0f4ff 0%, #fef0ff 100%)',
              border: '2px solid #667eea'
            }}>
              <div style={{ fontSize: 13, color: '#667eea', marginBottom: 6, fontWeight: 600 }}>Grand Total</div>
              <div style={{ 
                fontSize: 24, 
                fontWeight: 700, 
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
                WebkitBackgroundClip: 'text', 
                WebkitTextFillColor: 'transparent', 
                backgroundClip: 'text'
              }}>
                {fmt(est.currency, est.grandTotal)}
              </div>
            </div>
          </div>
        </section>
      )}
    </div>
  )
}
