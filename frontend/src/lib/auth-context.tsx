/**
 * Authentication context and provider
 * - Token storage (localStorage + in-memory)
 * - Session state management
 * - Login/logout flows
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { apiClient } from './api-client'
import sharedConfig from '../../../shared_config.json'

interface User {
  customer_id: string
  username: string
  profile_id?: string
  auth_level: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  updateAuthLevel: (level: string) => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface LoginResponse {
  access_token: string
  token_type: string
  user: User
}

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // Initialize auth state from localStorage
  useEffect(() => {
    const storedToken = localStorage.getItem(sharedConfig.auth_storage_key)
    if (storedToken) {
      setToken(storedToken)
      // In a real app, we'd validate the token and fetch user info
      // For now, we'll rely on the token being set
    }
    setIsLoading(false)
  }, [])

  const login = async (username: string, password: string): Promise<void> => {
    try {
      const response = await apiClient.post<LoginResponse>(
        '/auth/sign-in',
        { username, password },
        { skipAuth: true }
      )

      const { access_token, user: userData } = response

      // Store token
      localStorage.setItem(sharedConfig.auth_storage_key, access_token)
      setToken(access_token)
      setUser(userData)
    } catch (error) {
      // Clear any stale auth state
      localStorage.removeItem(sharedConfig.auth_storage_key)
      setToken(null)
      setUser(null)
      throw error
    }
  }

  const logout = () => {
    // Clear token and user state
    localStorage.removeItem(sharedConfig.auth_storage_key)
    setToken(null)
    setUser(null)

    // Optionally call backend logout endpoint
    // apiClient.post('/auth/logout').catch(() => {})
  }

  const updateAuthLevel = (level: string) => {
    if (user) {
      setUser({ ...user, auth_level: level })
    }
  }

  const value: AuthContextType = {
    user,
    token,
    isAuthenticated: !!token,
    isLoading,
    login,
    logout,
    updateAuthLevel,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
