import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ToastProvider } from './components/ui/Toast';
import AppRoutes from './routes/AppRoutes';

/**
 * CareerLens Main Application
 *
 * Provider Hierarchy:
 * 1. BrowserRouter (React Router v6 routing)
 * 2. AuthProvider (JWT authentication, session persistence, login/logout)
 * 3. ToastProvider (Non-blocking notification system)
 * 4. AppRoutes (Lazy-loaded route views guarded by ProtectedRoute)
 */
export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
          <AppRoutes />
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
