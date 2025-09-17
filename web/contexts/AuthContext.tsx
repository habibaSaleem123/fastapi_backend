'use client';

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { User, ApiResponse } from '@/lib/api-types';
import { authService } from '@/services/auth';
import { userService } from '@/services/user';
import { setAccessToken, getAccessToken } from '@/lib/api-client';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<ApiResponse<any>>;
  logout: () => Promise<void>;
  signup: (email: string, password: string, full_name: string) => Promise<ApiResponse<any>>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check for existing token and restore session on app load
  const restoreSession = async () => {
    try {
      setIsLoading(true);

      // Check if we have a stored access token
      const storedToken = localStorage.getItem('access_token');
      if (storedToken) {
        setAccessToken(storedToken);

        // Try to get user profile to validate token
        const response = await userService.getProfile();
        if (response.ok && response.data) {
          setUser({
            id: response.data.id,
            email: response.data.email,
            name: response.data.full_name,
            roles: response.data.roles,
            permissions: response.data.permissions,
            verified: !!response.data.email_verified_at,
          });
        } else {
          // Token is invalid, clear it
          localStorage.removeItem('access_token');
          setAccessToken(null);
        }
      }
    } catch (error) {
      console.error('Failed to restore session:', error);
      localStorage.removeItem('access_token');
      setAccessToken(null);
    } finally {
      setIsLoading(false);
    }
  };

  // Login function
  const login = async (email: string, password: string): Promise<ApiResponse<any>> => {
    const response = await authService.login(email, password);

    if (response.ok && response.data) {
      const { access_token, user: userData } = response.data;

      // Store token
      localStorage.setItem('access_token', access_token);
      setAccessToken(access_token);

      // Set user data
      setUser(userData);
    }

    return response;
  };

  // Signup function
  const signup = async (email: string, password: string, full_name: string): Promise<ApiResponse<any>> => {
    return await authService.signup(email, password, full_name);
  };

  // Logout function
  const logout = async () => {
    try {
      await authService.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local state regardless of API response
      setUser(null);
      localStorage.removeItem('access_token');
      setAccessToken(null);

      // Redirect to login page
      if (typeof window !== 'undefined') {
        window.location.href = '/signin';
      }
    }
  };

  // Refresh user data
  const refreshUser = async () => {
    try {
      const response = await userService.getProfile();
      if (response.ok && response.data) {
        setUser({
          id: response.data.id,
          email: response.data.email,
          name: response.data.full_name,
          roles: response.data.roles,
          permissions: response.data.permissions,
          verified: !!response.data.email_verified_at,
        });
      }
    } catch (error) {
      console.error('Failed to refresh user:', error);
    }
  };

  // Initialize auth state on mount
  useEffect(() => {
    restoreSession();
  }, []);

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    signup,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};