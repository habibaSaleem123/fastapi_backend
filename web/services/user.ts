import { apiClient, makeApiCall } from '@/lib/api-client';
import { API_CONFIG } from '@/config/api';
import { UserProfile, ApiResponse } from '@/lib/api-types';

export const userService = {
  /**
   * Get current user profile
   */
  async getProfile(): Promise<ApiResponse<UserProfile>> {
    return makeApiCall<UserProfile>(() =>
      apiClient.get(API_CONFIG.ENDPOINTS.USERS.ME)
    );
  },

  /**
   * Update user profile
   */
  async updateProfile(data: Partial<UserProfile>): Promise<ApiResponse<UserProfile>> {
    return makeApiCall<UserProfile>(() =>
      apiClient.put(API_CONFIG.ENDPOINTS.USERS.ME, data)
    );
  },
};