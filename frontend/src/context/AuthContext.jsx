import React, { createContext, useContext, useState, useCallback } from 'react'
import api from '../lib/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('token'))
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('user')
    return saved ? JSON.parse(saved) : null
  })

  const login = useCallback(async (email, password) => {
    // DRF's built-in obtain-auth-token style endpoint. If your backend uses
    // a different path, this is the one place to change it.
    const { data } = await api.post('/auth-token/', { username: email, password })
    localStorage.setItem('token', data.token)
    setToken(data.token)
    try {
      const me = await api.get('/users/', { headers: { Authorization: `Token ${data.token}` } })
      const matched = me.data.results?.find(u => u.email === email)
      if (matched) {
        localStorage.setItem('user', JSON.stringify(matched))
        setUser(matched)
      }
    } catch {
      // Non-fatal: login still succeeds even if we can't resolve the profile.
    }
    return data.token
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setToken(null)
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ token, user, login, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider')
  return ctx
}
