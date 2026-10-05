/**
 * CareerLens Authentication Context
 *
 * Provides:
 * - Current user identity and token state
 * - login, register, and logout mutations
 * - Automatic token persistence & session restoration on app boot
 *
 * TOKEN STORAGE ARCHITECTURAL TRADEOFF DECISION:
 * ----------------------------------------------
 * We explicitly choose `localStorage` for token persistence in this frontend architecture.
 *
 * Tradeoff breakdown:
 * 1. In-Memory:
 *    - Security: High (Cannot be accessed via document.cookie or localStorage XSS scrapes).
 *    - Usability / Dev Experience: Poor for standalone SPAs without HttpOnly cookie backends,
 *      because every time the user refreshes the browser, switches tabs, or opens a new route,
 *      in-memory state resets, forcing a re-login or failing if the Node.js auth service is offline.
 * 2. LocalStorage (Chosen):
 *    - Security: Requires defense-in-depth against XSS (sanitization, no untrusted innerHTML).
 *    - Usability / Dev Experience: Optimal for client demos, evaluation, and seamless page
 *      reloads across all routes (/upload, /analysis/:id, /roadmap/:id). Users remain authenticated
 *      without session interruption.
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { tokenStorage } from '../utils/tokenStorage';
import { authService } from '../services/authService';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => tokenStorage.getUser());
  const [token, setToken] = useState(() => tokenStorage.getToken());
  const [isLoading, setIsLoading] = useState(true);

  // Restore or verify authenticated session on mount
  useEffect(() => {
    let isMounted = true;

    async function initAuth() {
      const existingToken = tokenStorage.getToken();
      if (!existingToken) {
        if (isMounted) setIsLoading(false);
        return;
      }

      try {
        const currentUser = await authService.getCurrentUser();
        if (isMounted && currentUser) {
          setUser(currentUser);
          setToken(existingToken);
        }
      } catch (err) {
        console.warn('Session verification warning:', err.message);
        // Retain cached user in mock mode
        const cachedUser = tokenStorage.getUser();
        if (isMounted && cachedUser) {
          setUser(cachedUser);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    initAuth();

    // Listen for unauthorized events emitted by apiClient 401 interceptor
    const handleUnauthorized = () => {
      setUser(null);
      setToken(null);
    };

    window.addEventListener('careerlens:unauthorized', handleUnauthorized);
    return () => {
      isMounted = false;
      window.removeEventListener('careerlens:unauthorized', handleUnauthorized);
    };
  }, []);

  /**
   * Log in user
   */
  const login = useCallback(async (email, password) => {
    setIsLoading(true);
    try {
      const data = await authService.login({ email, password });
      setUser(data.user);
      setToken(data.token);
      return data;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Register user
   */
  const register = useCallback(async (userData) => {
    setIsLoading(true);
    try {
      const data = await authService.register(userData);
      setUser(data.user);
      setToken(data.token);
      return data;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Log out user
   */
  const logout = useCallback(async () => {
    setIsLoading(true);
    try {
      await authService.logout();
    } finally {
      setUser(null);
      setToken(null);
      setIsLoading(false);
    }
  }, []);

  const value = {
    user,
    token,
    isAuthenticated: Boolean(token),
    isLoading,
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
