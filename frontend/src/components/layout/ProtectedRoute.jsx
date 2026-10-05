import React from 'react';
import { Navigate, useLocation, Outlet } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import Spinner from '../ui/Spinner';

/**
 * ProtectedRoute Component
 * Guards private platform routes.
 * If authentication check is pending, displays a branded spinner.
 * If unauthenticated, redirects to /login preserving the requested return URL.
 */
export default function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 dark:bg-slate-925">
        <Spinner size="lg" variant="primary" />
        <p className="mt-4 text-xs font-medium text-slate-500 dark:text-slate-400 animate-pulse">
          Verifying CareerLens session credentials...
        </p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children ? children : <Outlet />;
}
