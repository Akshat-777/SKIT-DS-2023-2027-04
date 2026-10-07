import React, { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from '../components/layout/ProtectedRoute';
import Spinner from '../components/ui/Spinner';
import { Sparkles } from 'lucide-react';

// Lazy-loaded page components for code-splitting and optimized loading
const LoginPage = lazy(() => import('../pages/LoginPage'));
const RegisterPage = lazy(() => import('../pages/RegisterPage'));
const UploadPage = lazy(() => import('../pages/UploadPage'));
const AnalysisPage = lazy(() => import('../pages/AnalysisPage'));
const MarketFitPage = lazy(() => import('../pages/MarketFitPage'));
const RoadmapPage = lazy(() => import('../pages/RoadmapPage'));
const CritiquePage = lazy(() => import('../pages/CritiquePage'));
const HistoryPage = lazy(() => import('../pages/HistoryPage'));
const NotFoundPage = lazy(() => import('../pages/NotFoundPage'));
const DemoPage = lazy(() => import('../components/DemoPage'));

/**
 * Branded Suspense fallback displayed during lazy chunk resolution
 */
function SuspenseFallback() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 dark:bg-slate-925 space-y-4">
      <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-brand-600 to-indigo-600 text-white flex items-center justify-center shadow-glow-brand animate-pulse">
        <Sparkles className="w-6 h-6" />
      </div>
      <div className="flex items-center gap-2">
        <Spinner size="md" variant="primary" />
        <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
          Loading CareerLens Workspace...
        </span>
      </div>
    </div>
  );
}

export default function AppRoutes() {
  return (
    <Suspense fallback={<SuspenseFallback />}>
      <Routes>
        {/* Public Authentication Routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Protected Application Routes */}
        <Route
          path="/upload"
          element={
            <ProtectedRoute>
              <UploadPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/analysis/:resumeId"
          element={
            <ProtectedRoute>
              <AnalysisPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/market-fit/:resumeId"
          element={
            <ProtectedRoute>
              <MarketFitPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/roadmap/:resumeId"
          element={
            <ProtectedRoute>
              <RoadmapPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/critique/:resumeId"
          element={
            <ProtectedRoute>
              <CritiquePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/history"
          element={
            <ProtectedRoute>
              <HistoryPage />
            </ProtectedRoute>
          }
        />

        {/* UI Component Showcase & Wireframes (Preserved for review) */}
        <Route path="/demo" element={<DemoPage />} />

        {/* Root Redirect to /upload */}
        <Route path="/" element={<Navigate to="/upload" replace />} />

        {/* 404 Catch-All */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Suspense>
  );
}
