/**
 * CareerLens Token & Storage Management Utility
 *
 * ARCHITECTURAL TRADEOFF ANALYSIS: localStorage vs. In-Memory Token Storage
 * -------------------------------------------------------------------------
 * 1. In-Memory Storage (Variables / React Context / Closure):
 *    - Pros: Highly resilient against Cross-Site Scripting (XSS). Malicious third-party scripts
 *      or XSS payloads cannot directly dump memory without executing specialized hooks.
 *    - Cons: State is wiped clean on every hard page refresh, browser reload, or multi-tab
 *      navigation. Requires a persistent silent refresh flow (e.g. HttpOnly, SameSite cookies)
 *      with an active auth-service backend to issue a new access token on reload.
 *
 * 2. LocalStorage Persistence (Chosen Strategy for Client SPA):
 *    - Pros: Survives page reloads, tab duplication, and browser restarts. Allows an instant,
 *      seamless developer & evaluation experience where authenticated sessions persist
 *      during navigation, prototyping, and offline mock demos without requiring an active
 *      refresh-token cookie endpoint daemon.
 *    - Cons: Vulnerable to XSS if untrusted scripts are injected.
 *    - Mitigation: Combine strict input sanitization, CSP headers, short-lived JWT lifetimes,
 *      and production-grade HttpOnly refresh cookies when deploying to live cloud servers.
 */

const TOKEN_KEY = 'careerlens_jwt_token';
const REFRESH_TOKEN_KEY = 'careerlens_refresh_token';
const USER_KEY = 'careerlens_user';

export const tokenStorage = {
  /**
   * Retrieve JWT access token
   * @returns {string|null}
   */
  getToken() {
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch (e) {
      console.error('Failed to read auth token from localStorage:', e);
      return null;
    }
  },

  /**
   * Persist JWT access token
   * @param {string} token
   */
  setToken(token) {
    try {
      if (token) {
        localStorage.setItem(TOKEN_KEY, token);
      } else {
        localStorage.removeItem(TOKEN_KEY);
      }
    } catch (e) {
      console.error('Failed to set auth token in localStorage:', e);
    }
  },

  /**
   * Retrieve refresh token (if present)
   * @returns {string|null}
   */
  getRefreshToken() {
    try {
      return localStorage.getItem(REFRESH_TOKEN_KEY);
    } catch (_e) {
      return null;
    }
  },

  /**
   * Persist refresh token
   * @param {string} refreshToken
   */
  setRefreshToken(refreshToken) {
    try {
      if (refreshToken) {
        localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
      } else {
        localStorage.removeItem(REFRESH_TOKEN_KEY);
      }
    } catch (e) {
      console.error('Failed to set refresh token in localStorage:', e);
    }
  },

  /**
   * Retrieve cached user profile
   * @returns {object|null}
   */
  getUser() {
    try {
      const data = localStorage.getItem(USER_KEY);
      return data ? JSON.parse(data) : null;
    } catch (e) {
      console.error('Failed to parse user profile from localStorage:', e);
      return null;
    }
  },

  /**
   * Persist cached user profile
   * @param {object} user
   */
  setUser(user) {
    try {
      if (user) {
        localStorage.setItem(USER_KEY, JSON.stringify(user));
      } else {
        localStorage.removeItem(USER_KEY);
      }
    } catch (e) {
      console.error('Failed to set user in localStorage:', e);
    }
  },

  /**
   * Clear all auth session data
   */
  clearAuth() {
    try {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(REFRESH_TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
    } catch (e) {
      console.error('Failed to clear auth from localStorage:', e);
    }
  },
};

export default tokenStorage;
