// API Configuration
export const API_CONFIG = {
  BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  PREFIX: process.env.NEXT_PUBLIC_API_PREFIX || '',
  ENDPOINTS: {
    AUTH: {
      LOGIN: '/auth/login',
      SIGNUP: '/auth/signup',
      REFRESH: '/auth/refresh',
      LOGOUT: '/auth/logout',
      FORGOT_PASSWORD: '/auth/password/forgot',
      RESET_PASSWORD: '/auth/password/reset',
      VERIFY_EMAIL: '/auth/verify/confirm',
      VERIFY_REQUEST: '/auth/verify/request',
      GOOGLE_START: '/auth/google/start',
      GOOGLE_CALLBACK: '/auth/google/callback',
    },
    USERS: {
      ME: '/users/me',
    },
    ADMIN: {
      ROLES: '/admin/roles',
      USERS: '/admin/users',
    }
  },
  TIMEOUT: 10000, // 10 seconds
} as const;

// Helper to build full API URL
export const buildApiUrl = (endpoint: string): string => {
  const baseUrl = API_CONFIG.BASE_URL.replace(/\/$/, ''); // Remove trailing slash
  const prefix = API_CONFIG.PREFIX.replace(/^\/|\/$/g, ''); // Remove leading/trailing slashes
  const path = endpoint.replace(/^\//, ''); // Remove leading slash

  if (prefix) {
    return `${baseUrl}/${prefix}/${path}`;
  }
  return `${baseUrl}/${path}`;
};

// Environment check
export const isProduction = process.env.NODE_ENV === 'production';
export const isDevelopment = process.env.NODE_ENV === 'development';