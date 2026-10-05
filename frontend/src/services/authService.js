/**
 * CareerLens Auth Service
 * Interfaces with the Node.js + Express Authentication Microservice
 * Issues & verifies JWTs, handles session recovery, and provides mock fallback.
 */

import { authClient, IS_MOCK_MODE } from './apiClient';
import { tokenStorage } from '../utils/tokenStorage';

const MOCK_DELAY = 350;

export const authService = {
  /**
   * Log in user with email & password
   * @param {{ email: string, password: string }} credentials
   * @returns {Promise<{ user: object, token: string }>}
   */
  async login({ email, password }) {
    if (IS_MOCK_MODE) {
      await new Promise((resolve) => setTimeout(resolve, MOCK_DELAY));

      // Mock validation
      if (!email || !password) {
        const err = new Error('Email and password are required.');
        err.code = 'VALIDATION_ERROR';
        throw err;
      }

      const mockUser = {
        id: 'usr_skit_2026_01',
        name: email.includes('recruiter') ? 'Akshat Agarwal (Recruiter Demo)' : 'Aarav Sharma',
        email: email,
        role: email.includes('recruiter') ? 'recruiter' : 'candidate',
        college: 'SKIT Jaipur',
        department: 'B.Tech CSE (Data Science)',
        avatarUrl: null,
      };

      const mockToken = `mock_jwt_token_${Date.now()}`;
      tokenStorage.setToken(mockToken);
      tokenStorage.setUser(mockUser);

      return { user: mockUser, token: mockToken };
    }

    try {
      const data = await authClient.post('/login', { email, password });
      if (data?.token) {
        tokenStorage.setToken(data.token);
      }
      if (data?.user) {
        tokenStorage.setUser(data.user);
      }
      return data;
    } catch (err) {
      console.error('authService.login error:', err);
      throw err;
    }
  },

  /**
   * Register new user account
   * @param {{ name: string, email: string, password: string, role?: string }} payload
   * @returns {Promise<{ user: object, token: string }>}
   */
  async register({ name, email, password, role = 'candidate' }) {
    if (IS_MOCK_MODE) {
      await new Promise((resolve) => setTimeout(resolve, MOCK_DELAY));

      if (!name || !email || !password) {
        const err = new Error('Full name, email, and password are required.');
        err.code = 'VALIDATION_ERROR';
        throw err;
      }

      const mockUser = {
        id: `usr_${Date.now()}`,
        name,
        email,
        role,
        college: 'SKIT Jaipur',
        department: 'B.Tech CSE (Data Science)',
        avatarUrl: null,
      };

      const mockToken = `mock_jwt_token_${Date.now()}`;
      tokenStorage.setToken(mockToken);
      tokenStorage.setUser(mockUser);

      return { user: mockUser, token: mockToken };
    }

    try {
      const data = await authClient.post('/register', { name, email, password, role });
      if (data?.token) {
        tokenStorage.setToken(data.token);
      }
      if (data?.user) {
        tokenStorage.setUser(data.user);
      }
      return data;
    } catch (err) {
      console.error('authService.register error:', err);
      throw err;
    }
  },

  /**
   * Retrieve current authenticated user profile
   * @returns {Promise<object>}
   */
  async getCurrentUser() {
    const cached = tokenStorage.getUser();
    const token = tokenStorage.getToken();

    if (!token) return null;

    if (IS_MOCK_MODE) {
      return (
        cached || {
          id: 'usr_skit_2026_01',
          name: 'Aarav Sharma',
          email: 'aarav.sharma@skit.ac.in',
          role: 'candidate',
          college: 'SKIT Jaipur',
          department: 'B.Tech CSE (Data Science)',
        }
      );
    }

    try {
      const data = await authClient.get('/me');
      const user = data.user || data;
      tokenStorage.setUser(user);
      return user;
    } catch (err) {
      console.warn('Failed to verify token with auth service:', err.message);
      // If network is offline, keep cached user
      return cached;
    }
  },

  /**
   * Log out user and destroy session storage
   */
  async logout() {
    try {
      if (!IS_MOCK_MODE) {
        await authClient.post('/logout').catch(() => {});
      }
    } finally {
      tokenStorage.clearAuth();
    }
  },
};

export default authService;
