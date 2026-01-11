import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { login as apiLogin, register as apiRegister } from '../api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    try {
      const t = localStorage.getItem('ww_token')
      const u = localStorage.getItem('ww_user')
      if (t && u) {
        setToken(t)
        setUser(JSON.parse(u))
      }
    } catch {}
    setTimeout(() => setReady(true), 0)
  }, [])

  const signIn = async (email, password) => {
    const res = await apiLogin(email, password)
    setUser(res.user)
    setToken(res.data ? res.data.accessToken : res.accessToken)
    try {
      localStorage.setItem('ww_token', res.accessToken || (res.data && res.data.accessToken) || '')
      localStorage.setItem('ww_user', JSON.stringify(res.user))
    } catch {}
    return res
  }

  const signUp = async (email, password) => {
    const res = await apiRegister(email, password)
    setUser(res.user)
    setToken(res.accessToken)
    try {
      localStorage.setItem('ww_token', res.accessToken)
      localStorage.setItem('ww_user', JSON.stringify(res.user))
    } catch {}
    return res
  }

  const signOut = () => {
    setUser(null)
    setToken(null)
    try {
      localStorage.removeItem('ww_token')
      localStorage.removeItem('ww_user')
    } catch {}
  }

  const value = useMemo(() => ({ user, token, ready, signIn, signUp, signOut }), [user, token, ready])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  return useContext(AuthContext)
}


