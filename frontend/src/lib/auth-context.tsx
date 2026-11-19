/**
 * Authentication context provider with login, logout, and token management
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import sharedConfig from '../../../shared_config.json';
import { apiClient } from './api-client';
import type { LoginRequest, LoginResponse, User } from '../types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  activeProfileId: number | null;
  isAuthenticated: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [activeProfileId, setActiveProfileId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  // Initialize auth state from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem(sharedConfig.auth.tokenStorageKey);
    if (storedToken) {
      setToken(storedToken);
      // In a real app, you might validate the token or fetch user details here
      // For now, we'll mark as loaded
    }
    
    const storedProfileId = localStorage.getItem('lbg_ftr_active_profile_id');
    if (storedProfileId) {
      setActiveProfileId(Number(storedProfileId));
    }
    
    setLoading(false);

    // Listen for token changes (when LoginPage stores a token directly)
    const checkToken = () => {
      const currentToken = localStorage.getItem(sharedConfig.auth.tokenStorageKey);
      setToken(currentToken);
      
      const storedProfileId = localStorage.getItem('lbg_ftr_active_profile_id');
      if (storedProfileId) {
        setActiveProfileId(Number(storedProfileId));
      }
    };

    // Check periodically for token changes (handles case where LoginPage stores token)
    const interval = setInterval(checkToken, 100);

    // Also listen for custom event that LoginPage can dispatch
    window.addEventListener('auth-token-changed', checkToken);

    return () => {
      clearInterval(interval);
      window.removeEventListener('auth-token-changed', checkToken);
    };
  }, []);

  const login = async (credentials: LoginRequest) => {
    try {
      const response = await apiClient.post<LoginResponse>('/auth/login', credentials);
      
      // Store token
      const accessToken = response.access_token;
      localStorage.setItem(sharedConfig.auth.tokenStorageKey, accessToken);
      setToken(accessToken);
      
      // Store user info
      setUser(response.user);
      
      // Store active profile ID
      if (response.active_profile_id) {
        setActiveProfileId(response.active_profile_id);
      }
    } catch (error) {
      // Clear any stale auth state on login failure
      localStorage.removeItem(sharedConfig.auth.tokenStorageKey);
      setToken(null);
      setUser(null);
      setActiveProfileId(null);
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem(sharedConfig.auth.tokenStorageKey);
    setToken(null);
    setUser(null);
    setActiveProfileId(null);
  };

  // Check authentication from localStorage directly to handle cases where
  // token is stored outside the context (e.g., in LoginPage)
  const currentToken = token || localStorage.getItem(sharedConfig.auth.tokenStorageKey);

  const value: AuthContextType = {
    user,
    token: currentToken,
    activeProfileId,
    isAuthenticated: !!currentToken,
    login,
    logout,
    loading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
