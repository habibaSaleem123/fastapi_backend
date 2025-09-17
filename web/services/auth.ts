import { apiClient, makeApiCall, setAccessToken, clearTokens } from '@/lib/api-client';
import { API_CONFIG, buildApiUrl } from '@/config/api';
import {
  LoginRequest,
  SignupRequest,
  LoginResponse,
  SignupResponse,
  ForgotPasswordRequest,
  ResetPasswordRequest,
  VerifyEmailRequest,
  GoogleOAuthStartResponse,
  ApiResponse,
} from '@/lib/api-types';

export const authService = {
  /**
   * Login user with email and password
   */
  async login(email: string, password: string): Promise<ApiResponse<LoginResponse>> {
    const result = await makeApiCall<LoginResponse>(() =>
      apiClient.post(API_CONFIG.ENDPOINTS.AUTH.LOGIN, {
        email,
        password,
      } as LoginRequest)
    );

    // Store access token if login successful
    if (result.ok && result.data?.access_token) {
      setAccessToken(result.data.access_token);
    }

    return result;
  },

  /**
   * Register new user
   */
  async signup(email: string, password: string, full_name: string): Promise<ApiResponse<SignupResponse>> {
    return makeApiCall<SignupResponse>(() =>
      apiClient.post(API_CONFIG.ENDPOINTS.AUTH.SIGNUP, {
        email,
        password,
        full_name,
      } as SignupRequest)
    );
  },

  /**
   * Logout user (clears tokens)
   */
  async logout(): Promise<ApiResponse<void>> {
    const result = await makeApiCall<void>(() =>
      apiClient.post(API_CONFIG.ENDPOINTS.AUTH.LOGOUT)
    );

    // Clear tokens regardless of API response
    clearTokens();

    return result;
  },

  /**
   * Refresh access token (handled automatically by interceptor)
   */
  async refresh(): Promise<ApiResponse<{ access_token: string }>> {
    return makeApiCall<{ access_token: string }>(() =>
      apiClient.post(API_CONFIG.ENDPOINTS.AUTH.REFRESH)
    );
  },

  /**
   * Request password reset email
   */
  async forgotPassword(email: string): Promise<ApiResponse<{ ok: boolean }>> {
    return makeApiCall<{ ok: boolean }>(() =>
      apiClient.post(API_CONFIG.ENDPOINTS.AUTH.FORGOT_PASSWORD, {
        email,
      } as ForgotPasswordRequest)
    );
  },

  /**
   * Reset password with token
   */
  async resetPassword(token: string, new_password: string): Promise<ApiResponse<{ reset: boolean }>> {
    return makeApiCall<{ reset: boolean }>(() =>
      apiClient.post(API_CONFIG.ENDPOINTS.AUTH.RESET_PASSWORD, {
        token,
        new_password,
      } as ResetPasswordRequest)
    );
  },

  /**
   * Request email verification resend
   */
  async requestVerification(email: string): Promise<ApiResponse<{ ok: boolean }>> {
    return makeApiCall<{ ok: boolean }>(() =>
      apiClient.post(API_CONFIG.ENDPOINTS.AUTH.VERIFY_REQUEST, {
        email,
      } as VerifyEmailRequest)
    );
  },

  /**
   * Verify email with token (usually called from email link)
   */
  async verifyEmail(token: string): Promise<ApiResponse<{ verified: boolean }>> {
    return makeApiCall<{ verified: boolean }>(() =>
      apiClient.get(`${API_CONFIG.ENDPOINTS.AUTH.VERIFY_EMAIL}?token=${token}`)
    );
  },

  /**
   * Start Google OAuth flow
   */
  async startGoogleAuth(): Promise<ApiResponse<GoogleOAuthStartResponse>> {
    return makeApiCall<GoogleOAuthStartResponse>(() =>
      apiClient.get(API_CONFIG.ENDPOINTS.AUTH.GOOGLE_START)
    );
  },

  /**
   * Check if user is authenticated (has valid token)
   */
  isAuthenticated(): boolean {
    if (typeof window === 'undefined') return false;
    return !!localStorage.getItem('access_token');
  },

  /**
   * Get current access token
   */
  getAccessToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('access_token');
  },

  /**
   * Manually set access token (used during auth flows)
   */
  setToken(token: string): void {
    setAccessToken(token);
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', token);
    }
  },

  /**
   * Clear all authentication data
   */
  clearAuth(): void {
    clearTokens();
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
    }
  },
};