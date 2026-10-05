/**
 * CareerLens Central Axios Client Configuration
 *
 * Configures:
 * 1. FastAPI Gateway Client (Resumes, ATS scoring, LightGBM market-fit, RAG roadmap, Recruiter critique)
 * 2. Node.js Express Auth Client (JWT issuance, refresh, profile verification)
 * 3. Request interceptors injecting Authorization: Bearer <token>
 * 4. Response interceptors handling 401 unauthenticated states and standardizing
 *    error schemas: {"error": {"code": str, "message": str}}
 */

import axios from 'axios';
import { tokenStorage } from '../utils/tokenStorage';

// Base URLs from Vite environment
export const FASTAPI_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
export const AUTH_BASE_URL = import.meta.env.VITE_AUTH_BASE_URL || 'http://localhost:5000/api/auth';
export const IS_MOCK_MODE =
  import.meta.env.VITE_USE_MOCK === 'true' || import.meta.env.VITE_USE_MOCK === true;

/**
 * Configure standard interceptors on an Axios instance
 * @param {import('axios').AxiosInstance} instance
 * @param {string} serviceName
 */
function applyInterceptors(instance, serviceName = 'API') {
  // Request Interceptor: Attach JWT Bearer Token
  instance.interceptors.request.use(
    (config) => {
      const token = tokenStorage.getToken();
      if (token) {
        config.headers = config.headers || {};
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  // Response Interceptor: 401 handling & Error standardizer
  instance.interceptors.response.use(
    (response) => {
      // Direct data unwrap for caller convenience
      return response.data;
    },
    async (error) => {
      const originalRequest = error.config;
      const status = error.response ? error.response.status : null;

      // Handle 401 Unauthorized (Expired or invalid token)
      if (status === 401 && !originalRequest._retry) {
        console.warn(`[${serviceName}] 401 Unauthorized encountered. Session expired.`);
        tokenStorage.clearAuth();

        // Dispatch a custom window event for decoupled auth state sync
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent('careerlens:unauthorized'));
          // In non-auth routes, redirect to login
          if (
            !window.location.pathname.startsWith('/login') &&
            !window.location.pathname.startsWith('/register')
          ) {
            window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`;
          }
        }
      }

      // Standardize error body to {"error": {"code": str, "message": str}}
      let standardizedError = {
        code: 'UNKNOWN_ERROR',
        message: 'An unexpected network error occurred. Please try again.',
      };

      if (error.response && error.response.data) {
        if (error.response.data.error) {
          standardizedError = error.response.data.error;
        } else if (typeof error.response.data === 'string') {
          standardizedError = {
            code: `HTTP_${status}`,
            message: error.response.data,
          };
        } else if (error.response.data.detail) {
          // FastAPI default exception detail format
          standardizedError = {
            code: `FASTAPI_ERROR_${status}`,
            message:
              typeof error.response.data.detail === 'string'
                ? error.response.data.detail
                : JSON.stringify(error.response.data.detail),
          };
        }
      } else if (error.message) {
        standardizedError = {
          code: 'NETWORK_FAILURE',
          message: error.message,
        };
      }

      const formattedError = new Error(standardizedError.message);
      formattedError.code = standardizedError.code;
      formattedError.status = status;
      formattedError.raw = error;

      return Promise.reject(formattedError);
    }
  );
}

// 1. Python FastAPI Client instance
export const apiClient = axios.create({
  baseURL: FASTAPI_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});
applyInterceptors(apiClient, 'FastAPI');

// 2. Node.js Auth Service Client instance
export const authClient = axios.create({
  baseURL: AUTH_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});
applyInterceptors(authClient, 'AuthService');

export default apiClient;
