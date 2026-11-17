import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiClient } from './api-client';
import sharedConfig from '../../../shared_config.json';

interface User {
  id: string;
  username: string;
  email: string | null;
  display_name: string | null;
  scope: string;
  customer_party_id: string | null;
  brand: string | null;
}

interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_at: string;
  inactivity_timeout_seconds: number;
  session_id: string;
  user: User;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string, channel?: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  // Check for existing session on mount
  useEffect(() => {
    const token = localStorage.getItem(sharedConfig.auth.storage_key);
    const sessionId = localStorage.getItem('session_id');
    
    if (token && sessionId) {
      // Verify token with /auth/me endpoint
      apiClient
        .get<{ user: User }>(`/auth/me?session_id=${sessionId}`)
        .then((response) => {
          setUser(response.user);
        })
        .catch(() => {
          // Token invalid, clear it
          localStorage.removeItem(sharedConfig.auth.storage_key);
          localStorage.removeItem('session_id');
        })
        .finally(() => {
          setIsLoading(false);
        });
    } else {
      setIsLoading(false);
    }
  }, []);
  
  const login = async (username: string, password: string, channel = 'mobile_app') => {
    const fieldNames = sharedConfig.auth.login_request.field_names;
    const payload = {
      [fieldNames[0]]: username,
      [fieldNames[1]]: password,
      channel,
    };
    
    const response = await apiClient.post<LoginResponse>(
      '/auth/login',
      payload,
    );
    
    // Extract token and user from response
    const token = response[sharedConfig.auth.login_response.token_field as keyof LoginResponse] as string;
    const userData = response[sharedConfig.auth.login_response.user_field as keyof LoginResponse] as User;
    
    // Store token and session_id
    localStorage.setItem(sharedConfig.auth.storage_key, token);
    localStorage.setItem('session_id', response.session_id);
    
    // Update state
    setUser(userData);
  };
  
  const logout = async () => {
    const sessionId = localStorage.getItem('session_id');
    try {
      // Call logout endpoint if available
      if (sessionId) {
        await apiClient.post(`/auth/logout?session_id=${sessionId}`);
      }
    } catch {
      // Ignore errors on logout
    } finally {
      // Always clear local state
      localStorage.removeItem(sharedConfig.auth.storage_key);
      localStorage.removeItem('session_id');
      setUser(null);
    }
  };
  
  const refresh = async () => {
    const sessionId = localStorage.getItem('session_id');
    if (!sessionId) {
      await logout();
      throw new Error('No session ID');
    }
    
    try {
      const response = await apiClient.post<{ access_token: string }>(`/auth/refresh?session_id=${sessionId}`);
      localStorage.setItem(sharedConfig.auth.storage_key, response.access_token);
    } catch (error) {
      // Refresh failed, logout
      await logout();
      throw error;
    }
  };
  
  const value: AuthContextType = {
    user,
    isAuthenticated: user !== null,
    isLoading,
    login,
    logout,
    refresh,
  };
  
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
