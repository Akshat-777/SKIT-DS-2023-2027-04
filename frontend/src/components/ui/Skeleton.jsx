import React from 'react';

/**
 * CareerLens Skeleton Loading Placeholder
 * Shimmering placeholder components for asynchronous loading states.
 */
export default function Skeleton({
  variant = 'text',
  width,
  height,
  count = 1,
  className = '',
  animated = true,
}) {
  const baseClasses = `bg-slate-200 dark:bg-slate-800 ${
    animated ? 'animate-pulse' : ''
  }`;

  const renderSingle = (key) => {
    if (variant === 'circular') {
      return (
        <div
          key={key}
          aria-hidden="true"
          className={`${baseClasses} rounded-full flex-shrink-0 ${className}`}
          style={{
            width: width || '40px',
            height: height || width || '40px',
          }}
        />
      );
    }

    if (variant === 'card') {
      return (
        <div
          key={key}
          aria-hidden="true"
          className={`p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-850 space-y-4 ${className}`}
        >
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-full ${baseClasses}`} />
            <div className="space-y-1.5 flex-1">
              <div className={`h-4 w-1/3 rounded ${baseClasses}`} />
              <div className={`h-3 w-1/2 rounded ${baseClasses}`} />
            </div>
          </div>
          <div className="space-y-2">
            <div className={`h-3 w-full rounded ${baseClasses}`} />
            <div className={`h-3 w-5/6 rounded ${baseClasses}`} />
            <div className={`h-3 w-2/3 rounded ${baseClasses}`} />
          </div>
          <div className="pt-2 flex justify-between">
            <div className={`h-5 w-20 rounded-full ${baseClasses}`} />
            <div className={`h-5 w-16 rounded ${baseClasses}`} />
          </div>
        </div>
      );
    }

    if (variant === 'rectangular') {
      return (
        <div
          key={key}
          aria-hidden="true"
          className={`${baseClasses} rounded-lg ${className}`}
          style={{
            width: width || '100%',
            height: height || '120px',
          }}
        />
      );
    }

    // Default 'text'
    return (
      <div
        key={key}
        aria-hidden="true"
        className={`${baseClasses} rounded h-3.5 my-1.5 ${className}`}
        style={{
          width: width || '100%',
          height: height || undefined,
        }}
      />
    );
  };

  if (count > 1) {
    return (
      <div className="space-y-2" aria-hidden="true">
        {Array.from({ length: count }).map((_, i) => renderSingle(i))}
      </div>
    );
  }

  return renderSingle(0);
}
