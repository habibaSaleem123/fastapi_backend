import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { API_CONFIG, buildApiUrl } from '@/config/api';

// Types for API responses
export interface ApiResponse<T = any> {
  data: T | null;
  message?: string;
  ok: boolean;
}

export interface ApiError {
  message: string;
  details?: Record<string, any>;
  code?: number;
}

// Token management
let accessToken: string | null = null;
let refreshPromise: Promise<string> | null = null;

export const setAccessToken = (token: string | null) => {
  accessToken = token;
};

export const getAccessToken = (): string | null => {
  return accessToken;
};

export const clearTokens = () => {
  accessToken = null;
  // Clear refresh token cookie will be handled by logout API call
};

// Create axios instance
const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: API_CONFIG.BASE_URL,
    timeout: API_CONFIG.TIMEOUT,
    withCredentials: true, // Important for httpOnly cookies (refresh token)
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor - add access token to headers
  client.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      if (accessToken) {
        config.headers.Authorization = `Bearer ${accessToken}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  // Response interceptor - handle token refresh
  client.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
      const originalRequest = error.config;

      // If we get 401 and haven't already tried to refresh
      if (
        error.response?.status === 401 &&
        originalRequest &&
        !originalRequest._retry
      ) {
        originalRequest._retry = true;

        try {
          // Prevent multiple refresh attempts
          if (!refreshPromise) {
            refreshPromise = refreshAccessToken();
          }

          const newToken = await refreshPromise;
          refreshPromise = null;

          if (newToken) {
            setAccessToken(newToken);
            originalRequest.headers = originalRequest.headers || {};
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            return client(originalRequest);
          }
        } catch (refreshError) {
          refreshPromise = null;
          // Refresh failed, clear tokens and redirect to login
          clearTokens();
          if (typeof window !== 'undefined') {
            window.location.href = '/signin';
          }
          return Promise.reject(refreshError);
        }
      }

      return Promise.reject(error);
    }
  );

  return client;
};

// Refresh token function
const refreshAccessToken = async (): Promise<string> => {
  try {
    const response = await axios.post(
      buildApiUrl(API_CONFIG.ENDPOINTS.AUTH.REFRESH),
      {},
      {
        withCredentials: true, // Send refresh token cookie
        timeout: API_CONFIG.TIMEOUT,
      }
    );

    const { access_token } = response.data;
    if (!access_token) {
      throw new Error('No access token received');
    }

    return access_token;
  } catch (error) {
    console.error('Token refresh failed:', error);
    throw error;
  }
};

// Create and export the API client instance
export const apiClient = createApiClient();

// Helper function for making API calls with better error handling
export const makeApiCall = async <T = any>(
  request: () => Promise<any>
): Promise<ApiResponse<T>> => {
  try {
    const response = await request();
    return {
      data: response.data,
      ok: true,
    };
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const apiError: ApiError = {
        message: error.response?.data?.detail || error.response?.data?.message || error.message,
        details: error.response?.data,
        code: error.response?.status,
      };

      return {
        data: null,
        message: apiError.message,
        ok: false,
      };
    }

    return {
      data: null,
      message: error instanceof Error ? error.message : 'An unexpected error occurred',
      ok: false,
    };
  }
};

// Utility type for request configuration
declare module 'axios' {
  interface InternalAxiosRequestConfig {
    _retry?: boolean;
  }
}