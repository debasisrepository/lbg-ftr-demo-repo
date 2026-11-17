import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiClient } from './api-client';
import { LoginRequest, LoginResponse, User } from '../types/auth';
import sharedConfig from '../../../shared_config.json';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem(sharedConfig.auth.storage_key);
    if (token) {
      // Fetch current user
      apiClient
        .get<User>('/v1/auth/me')
        .then((userData) => {
          setUser(userData);
        })
        .catch(() => {
          // Token invalid, clear it
          localStorage.removeItem(sharedConfig.auth.storage_key);
        })
        .finally(() => {
          setIsLoading(false);
        });
    } else {
      setIsLoading(false);
    }
  }, []);

  const login = async (credentials: LoginRequest) => {
    // Skip auth redirect for login endpoint
    const response = await apiClient.post<LoginResponse>('/v1/auth/login', credentials, true);
    localStorage.setItem(sharedConfig.auth.storage_key, response.access_token);
    
    // Fetch user data
    const userData = await apiClient.get<User>('/v1/auth/me');
    setUser(userData);
  };

  const logout = async () => {
    try {
      await apiClient.post('/v1/auth/logout');
    } catch (error) {
      // Continue with logout even if the API call fails
      console.error('Logout API call failed:', error);
    }
    localStorage.removeItem(sharedConfig.auth.storage_key);
    setUser(null);
    window.location.href = '/login';
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
