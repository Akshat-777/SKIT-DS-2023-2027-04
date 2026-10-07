import React from 'react';
import { AlertOctagon, RotateCw } from 'lucide-react';
import Button from './Button';

/**
 * CareerLens ErrorState Component
 * Formatted directly for the shared API error contract:
 * { "error": { "code": str, "message": str } }
 */
export default function ErrorState({
  error = null,
  title = 'An unexpected error occurred',
  onRetry = null,
  actionLabel = 'Try Again',
  className = '',
}) {
  // Support both direct string, raw object or nested {"error": { code, message }}
  const errorObj = error?.error || error || {};
  const errorCode = typeof errorObj === 'object' ? errorObj.code : null;
  const errorMessage =
    typeof errorObj === 'object'
      ? errorObj.message || 'Unable to connect to the CareerLens microservices. Please verify your connection.'
      : typeof error === 'string'
      ? error
      : 'Something went wrong while processing your career analytics.';

  return (
    <div
      role="alert"
      className={`flex flex-col items-center justify-center text-center p-8 sm:p-10 rounded-2xl border border-rose-200 dark:border-rose-900/60 bg-rose-50/40 dark:bg-rose-950/20 ${className}`}
    >
      <div className="w-12 h-12 rounded-2xl bg-rose-100 dark:bg-rose-900/60 text-rose-600 dark:text-rose-400 flex items-center justify-center mb-3.5 shadow-subtle">
        <AlertOctagon className="w-6 h-6" />
      </div>

      {errorCode && (
        <span className="font-mono text-2xs uppercase tracking-wider px-2 py-0.5 rounded bg-rose-200/60 dark:bg-rose-900/80 text-rose-800 dark:text-rose-300 font-bold mb-2">
          ERROR_CODE: {errorCode}
        </span>
      )}

      <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 mb-1.5">
        {title}
      </h3>

      <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 max-w-md mb-5 leading-relaxed">
        {errorMessage}
      </p>

      {onRetry && (
        <Button
          variant="danger"
          size="sm"
          icon={<RotateCw className="w-4 h-4" />}
          onClick={onRetry}
        >
          {actionLabel}
        </Button>
      )}
    </div>
  );
}
