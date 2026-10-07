import React from 'react';
import Spinner from './Spinner';

/**
 * CareerLens Button Component
 * Supports variants: primary, secondary, outline, ghost, danger
 * Supports sizes: sm, md, lg
 * Supports loading and disabled states with full accessibility (aria, keyboard, focus rings).
 */
export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  disabled = false,
  icon: Icon = null,
  iconPosition = 'left',
  type = 'button',
  className = '',
  onClick,
  ...props
}) {
  const baseStyles = 'inline-flex items-center justify-center font-medium rounded-lg transition-all duration-150 select-none focus:outline-none focus:ring-2 focus:ring-offset-2 dark:focus:ring-offset-slate-900 disabled:opacity-60 disabled:cursor-not-allowed disabled:pointer-events-none active:scale-[0.98]';

  const sizeStyles = {
    sm: 'text-xs px-3 py-1.5 gap-1.5 shadow-xs',
    md: 'text-sm px-4 py-2 gap-2 shadow-subtle',
    lg: 'text-base px-5 py-2.5 gap-2.5 shadow-card',
  };

  const variantStyles = {
    primary: 'bg-brand-600 hover:bg-brand-700 text-white focus:ring-brand-500 shadow-brand-500/20 shadow-md hover:shadow-brand-500/30',
    secondary: 'bg-slate-100 hover:bg-slate-200 text-slate-800 dark:bg-slate-800 dark:hover:bg-slate-700 dark:text-slate-100 focus:ring-slate-400',
    outline: 'border border-slate-300 hover:bg-slate-50 text-slate-700 dark:border-slate-700 dark:hover:bg-slate-800 dark:text-slate-200 focus:ring-brand-500',
    ghost: 'hover:bg-slate-100 text-slate-700 dark:hover:bg-slate-800 dark:text-slate-200 focus:ring-brand-500',
    danger: 'bg-rose-600 hover:bg-rose-700 text-white focus:ring-rose-500 shadow-rose-500/20 shadow-md',
  };

  const spinnerColors = {
    primary: 'white',
    secondary: 'slate',
    outline: 'brand',
    ghost: 'brand',
    danger: 'white',
  };

  return (
    <button
      type={type}
      disabled={disabled || isLoading}
      aria-busy={isLoading}
      aria-disabled={disabled || isLoading}
      onClick={onClick}
      className={`${baseStyles} ${sizeStyles[size] || sizeStyles.md} ${variantStyles[variant] || variantStyles.primary} ${className}`}
      {...props}
    >
      {isLoading && (
        <Spinner size={size === 'lg' ? 'md' : 'xs'} color={spinnerColors[variant]} className="-ml-0.5" />
      )}
      
      {!isLoading && Icon && iconPosition === 'left' && (
        <span className="flex-shrink-0" aria-hidden="true">{Icon}</span>
      )}

      <span>{children}</span>

      {!isLoading && Icon && iconPosition === 'right' && (
        <span className="flex-shrink-0" aria-hidden="true">{Icon}</span>
      )}
    </button>
  );
}
