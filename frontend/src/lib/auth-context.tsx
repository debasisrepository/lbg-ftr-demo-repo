/* eslint-disable react-refresh/only-export-components */
import { createContext, useState, useEffect, ReactNode } from 'react'
import { apiClient } from './api-client'
import type { User, RoleContext, LoginRequest, TokenResponse, SessionResponse } from '../types/auth'

export interface AuthContextValue {
  user: User | null
  activeRole: RoleContext | null
  availableRoles: RoleContext[]
  isAuthenticated: boolean
  isLoading: boolean
  login: (credentials: LoginRequest) => Promise<void>
  logout: () => Promise<void>
  checkSession: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [activeRole, setActiveRole] = useState<RoleContext | null>(null)
  const [availableRoles, setAvailableRoles] = useState<RoleContext[]>([])
  const [isLoading, setIsLoading] = useState(true)

  const isAuthenticated = !!user && !!activeRole

  async function checkSession(): Promise<void> {
    setIsLoading(true)
    try {
      const token = apiClient.getToken()
      if (!token) {
        setUser(null)
        setActiveRole(null)
        setAvailableRoles([])
        return
      }

      const session = await apiClient.get<SessionResponse>('/v1/auth/session')
      setUser(session.user)
      setActiveRole(
        session.available_roles.find(r => r.role_code === session.active_role_code) || null
      )
      setAvailableRoles(session.available_roles)
    } catch {
      // Session invalid or expired
      setUser(null)
      setActiveRole(null)
      setAvailableRoles([])
      apiClient.clearToken()
    } finally {
      setIsLoading(false)
    }
  }

  // Check session on mount
  useEffect(() => {
    checkSession()
  }, []) // checkSession is stable; this effect should run only once

  async function login(credentials: LoginRequest): Promise<void> {
    setIsLoading(true)
    try {
      const response = await apiClient.post<TokenResponse>(
        '/v1/auth/login',
        credentials,
        { skipAuth: true }
      )

      // Store token
      apiClient.setToken(response.access_token)

      // Set user and role state
      setUser(response.user)
      setActiveRole(
        response.available_roles.find(r => r.role_code === response.active_role_code) || null
      )
      setAvailableRoles(response.available_roles)
    } finally {
      setIsLoading(false)
    }
  }

  async function logout(): Promise<void> {
    try {
      await apiClient.post('/v1/auth/logout')
    } catch {
      // Ignore logout errors
    } finally {
      apiClient.clearToken()
      setUser(null)
      setActiveRole(null)
      setAvailableRoles([])
    }
  }

  const value: AuthContextValue = {
    user,
    activeRole,
    availableRoles,
    isAuthenticated,
    isLoading,
    login,
    logout,
    checkSession,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
