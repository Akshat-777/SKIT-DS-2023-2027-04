import React from 'react';

/**
 * CareerLens ProgressBar Component
 * Provides visual bar tracking with automatic ATS score color assignment
 * (Red: 0-49, Amber: 50-74, Green: 75-100) and accessibility progressbar roles.
 */
export default function ProgressBar({
  value = 0,
  max = 100,
  label = '',
  showValue = false,
  variant = 'ats',
  size = 'md',
  striped = false,
  animated = false,
  className = '',
}) {
  const percentage = Math.min(100, Math.max(0, Math.round((value / max) * 100)));

  // Resolve color dynamically if variant is 'ats'
  let resolvedColor = 'bg-brand-600';
  let badgeColor = 'text-brand-600 dark:text-brand-400';

  if (variant === 'ats') {
    if (percentage >= 75) {
      resolvedColor = 'bg-emerald-500';
      badgeColor = 'text-emerald-600 dark:text-emerald-400';
    } else if (percentage >= 50) {
      resolvedColor = 'bg-amber-500';
      badgeColor = 'text-amber-600 dark:text-amber-400';
    } else {
      resolvedColor = 'bg-rose-500';
      badgeColor = 'text-rose-600 dark:text-rose-400';
    }
  } else if (variant === 'success') {
    resolvedColor = 'bg-emerald-500';
    badgeColor = 'text-emerald-600';
  } else if (variant === 'warning') {
    resolvedColor = 'bg-amber-500';
    badgeColor = 'text-amber-600';
  } else if (variant === 'danger') {
    resolvedColor = 'bg-rose-500';
    badgeColor = 'text-rose-600';
  } else if (variant === 'gradient') {
    resolvedColor = 'bg-gradient-to-r from-brand-500 via-purple-500 to-market-lpa';
    badgeColor = 'text-brand-600';
  }

  const heightClasses = {
    xs: 'h-1.5',
    sm: 'h-2',
    md: 'h-2.5',
    lg: 'h-4',
  };

  return (
    <div className={`w-full ${className}`}>
      {(label || showValue) && (
        <div className="flex justify-between items-center mb-1.5 text-xs font-semibold">
          {label && (
            <span className="text-slate-700 dark:text-slate-300">{label}</span>
          )}
          {showValue && (
            <span className={`font-mono font-bold ${badgeColor}`}>
              {percentage}%
            </span>
          )}
        </div>
      )}

      <div
        role="progressbar"
        aria-valuenow={percentage}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label || `${percentage}% completed`}
        className={`w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden ${
          heightClasses[size] || heightClasses.md
        }`}
      >
        <div
          className={`h-full transition-all duration-500 ease-out rounded-full ${resolvedColor} ${
            striped
              ? 'bg-[linear-gradient(45deg,rgba(255,255,255,0.15)_25%,transparent_25%,transparent_50%,rgba(255,255,255,0.15)_50%,rgba(255,255,255,0.15)_75%,transparent_75%,transparent)] bg-[length:1rem_1rem]'
              : ''
          } ${animated ? 'animate-[pulse_2s_infinite]' : ''}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
