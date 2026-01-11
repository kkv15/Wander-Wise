import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../auth/AuthProvider'

export default function SignInPage() {
  const { signIn, signUp } = useAuth()
  const nav = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [mode, setMode] = useState('login') // 'login' | 'register'
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const onSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (mode === 'login') {
        await signIn(email, password)
      } else {
        await signUp(email, password)
      }
      // Redirect to plan page or to the redirect URL if specified
      const params = new URLSearchParams(window.location.search)
      const redirect = params.get('redirect') || '/plan'
      nav(redirect)
    } catch (e) {
      setError(e?.message || 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

  // return (
  //   <main className="container">
  //     <div className="card" style={{ maxWidth: 520, margin: '40px auto', padding: 24 }}>
  //       <h2 style={{ marginTop: 0, marginBottom: 8 }}>{mode === 'login' ? 'Sign in' : 'Create account'}</h2>
  //       <p className="muted" style={{ marginTop: 0 }}>
  //         {mode === 'login' ? 'Welcome back! Enter your credentials.' : 'Create a free account to save your trips.'}
  //       </p>
  //       <form onSubmit={onSubmit} style={{ display: 'grid', gap: 12 }}>
  //         <div className="field">
  //           <label>Email</label>
  //           <input type="email" value={email} onChange={e => setEmail(e.target.value)} required placeholder="you@example.com" />
  //         </div>
  //         <div className="field">
  //           <label>Password</label>
  //           <input type="password" value={password} onChange={e => setPassword(e.target.value)} required minLength={6} />
  //         </div>
  //         {error && <div className="muted" style={{ color: '#b11' }}>{error}</div>}
  //         <div className="planner-actions" style={{ display: 'flex', gap: 10 }}>
  //           <button className="btn-primary" type="submit" disabled={loading}>
  //             {loading ? 'Please wait…' : (mode === 'login' ? 'Sign in' : 'Create account')}
  //           </button>
  //           <button type="button" className="btn-secondary" onClick={() => setMode(mode === 'login' ? 'register' : 'login')}>
  //             {mode === 'login' ? 'Need an account?' : 'Have an account? Sign in'}
  //           </button>
  //         </div>
  //       </form>
  //       <div style={{ marginTop: 16 }}>
  //         <Link className="muted" to="/">← Back to home</Link>
  //       </div>
  //     </div>
  //   </main>
  // )/
  
// }
return (
  <main
    className="container"
    style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px',
    }}
  >
    <div
      className="card"
      style={{
        width: '100%',
        maxWidth: 440,
        padding: '32px',
        borderRadius: 16,
      }}
    >
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <h2
          style={{
            margin: 0,
            fontSize: 28,
            fontWeight: 700,
            fontFamily: 'Poppins, Inter, system-ui',
          }}
        >
          {mode === 'login' ? 'Sign in' : 'Create account'}
        </h2>
        <p
          className="muted"
          style={{ marginTop: 6, fontSize: 15 }}
        >
          {mode === 'login'
            ? 'Welcome back! Enter your credentials.'
            : 'Create a free account to save your trips.'}
        </p>
      </div>

      {/* Form */}
      <form onSubmit={onSubmit} style={{ display: 'grid', gap: 16 }}>
        <div className="field">
          <label style={{ fontWeight: 600, marginBottom: 6, display: 'block' }}>
            Email
          </label>
          <input
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            required
            placeholder="you@example.com"
            style={{ width: '100%' }}
          />
        </div>

        <div className="field">
          <label style={{ fontWeight: 600, marginBottom: 6, display: 'block' }}>
            Password
          </label>
          <input
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
            minLength={6}
            style={{ width: '100%' }}
          />
        </div>

        {error && (
          <div
            style={{
              background: '#fff1f2',
              color: '#b11',
              padding: '10px 12px',
              borderRadius: 10,
              fontSize: 14,
            }}
          >
            {error}
          </div>
        )}

        {/* Actions */}
        <div style={{ display: 'grid', gap: 12, marginTop: 8 }}>
          <button
            className="btn-primary"
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '14px',
              fontSize: 16,
              borderRadius: 12,
            }}
          >
            {loading
              ? 'Please wait…'
              : mode === 'login'
              ? 'Sign in'
              : 'Create account'}
          </button>

          <button
            type="button"
            className="btn-secondary"
            onClick={() =>
              setMode(mode === 'login' ? 'register' : 'login')
            }
            style={{
              width: '100%',
              padding: '12px',
              borderRadius: 12,
            }}
          >
            {mode === 'login'
              ? 'Need an account?'
              : 'Have an account? Sign in'}
          </button>
        </div>
      </form>

      {/* Footer */}
      <div
        style={{
          marginTop: 20,
          textAlign: 'center',
        }}
      >
        <Link
          className="muted"
          to="/"
          style={{ textDecoration: 'none', fontSize: 14 }}
        >
          ← Back to home
        </Link>
      </div>
    </div>
  </main>
)
}


