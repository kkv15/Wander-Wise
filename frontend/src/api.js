const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

function authHeader() {
  try {
    const token = localStorage.getItem('ww_token')
    return token ? { Authorization: `Bearer ${token}` } : {}
  } catch {
    return {}
  }
}

export async function planTrip(payload) {
  const res = await fetch(`${API_BASE}/api/plan-trip`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeader() },
    body: JSON.stringify(payload)
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || 'Request failed')
  }
  return res.json()
}

export async function login(email, password) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || 'Login failed')
  }
  return res.json()
}

export async function register(email, password) {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || 'Register failed')
  }
  return res.json()
}

export async function fetchMyTrips(limit = 20) {
  const res = await fetch(`${API_BASE}/me/trips?limit=${encodeURIComponent(limit)}`, {
    headers: { ...authHeader() }
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || 'Failed to load trips')
  }
  return res.json()
}


