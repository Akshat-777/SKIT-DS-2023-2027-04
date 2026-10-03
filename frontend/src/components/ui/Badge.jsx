import React from 'react';

/**
 * CareerLens Badge Component
 * Categorical indicators for skill types (explicit vs implicit),
 * ATS score threshold tags (Red: 0-49, Amber: 50-74, Green: 75-100),
 * and status chips.
 */
export default function Badge({
  children,
  variant = 'default',
  size = 'md',
  dot = false,
  score = null,
  className = '',
}) {
  // If score is provided, automatically determine ATS variant
  let resolvedVariant = variant;
  if (score !== null && score !== undefined) {
    if (score >= 75) resolvedVariant = 'success';
    else if (score >= 50) resolvedVariant = 'warning';
    else resolvedVariant = 'danger';
  }

  const variantStyles = {
    default: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border-slate-200 dark:border-slate-700',
    primary: 'bg-brand-50 text-brand-700 dark:bg-brand-950/60 dark:text-brand-300 border-brand-200 dark:border-brand-800',
    success: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800',
    warning: 'bg-amber-50 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 border-amber-200 dark:border-amber-800',
    danger: 'bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300 border-rose-200 dark:border-rose-800',
    info: 'bg-sky-50 text-sky-700 dark:bg-sky-950/60 dark:text-sky-300 border-sky-200 dark:border-sky-800',
    role: 'bg-purple-50 text-purple-700 dark:bg-purple-950/60 dark:text-purple-300 border-purple-200 dark:border-purple-800 font-semibold',
    outline: 'bg-transparent text-slate-700 dark:text-slate-300 border-slate-300 dark:border-slate-600',
  };

  const dotStyles = {
    default: 'bg-slate-500',
    primary: 'bg-brand-500',
    success: 'bg-emerald-500',
    warning: 'bg-amber-500',
    danger: 'bg-rose-500',
    info: 'bg-sky-500',
    role: 'bg-purple-500',
    outline: 'bg-slate-400',
  };

  const sizeStyles = {
    sm: 'text-2xs px-2 py-0.5 gap-1 font-medium',
    md: 'text-xs px-2.5 py-1 gap-1.5 font-medium',
  };

  return (
    <span
      className={`inline-flex items-center rounded-full border ${variantStyles[resolvedVariant] || variantStyles.default} ${sizeStyles[size] || sizeStyles.md} ${className}`}
    >
      {dot && (
        <span
          className={`w-1.5 h-1.5 rounded-full ${dotStyles[resolvedVariant] || dotStyles.default} animate-pulse`}
          aria-hidden="true"
        />
      )}
      <span>{children}</span>
    </span>
  );
}
