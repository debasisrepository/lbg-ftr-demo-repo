import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiClient, ApiError } from './api-client';

interface User {
  id: string;
  display_name: string;
  profile_type: string;
}

interface LoginRequest {
  device_identifier: string;
  mobile_platform: 'iOS' | 'Android';
  passcode: string;
}

interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  expires_at: string;
  inactivity_timeout_seconds: number;
  session_id: string;
  user: User;
}

interface SessionResponse {
  session_id: string;
  customer_id: string;
  display_name: string;
  profile_type: string;
  expires_at: string;
  inactivity_timeout_seconds: number;
  is_active: boolean;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  error: string | null;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Restore session from token on mount
  useEffect(() => {
    const restoreSession = async () => {
      const token = sessionStorage.getItem('auth_token');
      if (!token) {
        setIsLoading(false);
        return;
      }

      try {
        const session = await apiClient.get<SessionResponse>('/v1/auth/session');
        setUser({
          id: session.customer_id,
          display_name: session.display_name,
          profile_type: session.profile_type,
        });
      } catch (err) {
        // Token is invalid or expired, clear it
        sessionStorage.removeItem('auth_token');
        console.error('Session restore failed:', err);
      } finally {
        setIsLoading(false);
      }
    };

    restoreSession();
  }, []);

  const login = async (credentials: LoginRequest) => {
    setError(null);
    setIsLoading(true);
    
    try {
      const response = await apiClient.post<LoginResponse>('/v1/auth/login', credentials);
      
      // Store token in sessionStorage
      sessionStorage.setItem('auth_token', response.access_token);
      setUser(response.user);
    } catch (err) {
      const message = err instanceof ApiError 
        ? err.detail || err.message 
        : 'Login failed';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setError(null);
    
    try {
      await apiClient.post('/v1/auth/logout');
    } catch (err) {
      // Even if logout fails on server, clear local state
      console.error('Logout error:', err);
    } finally {
      // Always clear local state
      sessionStorage.removeItem('auth_token');
      setUser(null);
    }
  };

  const clearError = () => {
    setError(null);
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    error,
    clearError,
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
