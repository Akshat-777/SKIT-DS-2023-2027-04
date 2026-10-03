import React from 'react';

/**
 * CareerLens Accessible Spinner Component
 * Displays an animated SVG loader with screen-reader text for accessibility.
 */
export default function Spinner({
  size = 'md',
  color = 'brand',
  label = 'Loading...',
  className = '',
}) {
  const sizeMap = {
    xs: 'w-3.5 h-3.5',
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-8 h-8',
    xl: 'w-12 h-12',
  };

  const colorMap = {
    brand: 'text-brand-600 dark:text-brand-400',
    white: 'text-white',
    slate: 'text-slate-600 dark:text-slate-300',
    'ats-green': 'text-emerald-500',
    'ats-amber': 'text-amber-500',
    'ats-red': 'text-rose-500',
  };

  const sizeClass = sizeMap[size] || sizeMap.md;
  const colorClass = colorMap[color] || colorMap.brand;

  return (
    <div role="status" className={`inline-flex items-center justify-center ${className}`}>
      <svg
        className={`animate-spin ${sizeClass} ${colorClass}`}
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
      <span className="sr-only">{label}</span>
    </div>
  );
}
