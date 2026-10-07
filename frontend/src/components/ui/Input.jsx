import React, { forwardRef } from 'react';
import { AlertCircle } from 'lucide-react';

/**
 * CareerLens Accessible Form Input
 * Supports floating/top labels, helper messages, error validation feedback,
 * leading/trailing icons, and full aria attributes.
 */
const Input = forwardRef(function Input(
  {
    id,
    label,
    type = 'text',
    error,
    helperText,
    leadingIcon: LeadingIcon = null,
    trailingIcon: TrailingIcon = null,
    disabled = false,
    required = false,
    className = '',
    inputClassName = '',
    ...props
  },
  ref
) {
  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);
  const helperId = inputId ? `${inputId}-helper` : undefined;
  const errorId = inputId ? `${inputId}-error` : undefined;

  const hasError = Boolean(error);

  return (
    <div className={`w-full ${className}`}>
      {label && (
        <label
          htmlFor={inputId}
          className="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1.5"
        >
          {label}
          {required && <span className="text-rose-500 ml-1" aria-hidden="true">*</span>}
        </label>
      )}

      <div className="relative rounded-lg shadow-xs">
        {LeadingIcon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400 dark:text-slate-500">
            {LeadingIcon}
          </div>
        )}

        <input
          ref={ref}
          id={inputId}
          type={type}
          disabled={disabled}
          required={required}
          aria-invalid={hasError}
          aria-describedby={hasError ? errorId : helperText ? helperId : undefined}
          className={`
            block w-full rounded-lg text-sm transition-all duration-150
            bg-white dark:bg-slate-900 
            text-slate-900 dark:text-slate-100 
            placeholder-slate-400 dark:placeholder-slate-500
            border ${
              hasError
                ? 'border-rose-500 focus:border-rose-500 focus:ring-rose-500'
                : 'border-slate-300 dark:border-slate-700 focus:border-brand-500 focus:ring-brand-500'
            }
            focus:outline-none focus:ring-2 focus:ring-offset-1 dark:focus:ring-offset-slate-900
            disabled:bg-slate-100 dark:disabled:bg-slate-800 disabled:text-slate-400 disabled:cursor-not-allowed
            ${LeadingIcon ? 'pl-10' : 'pl-3.5'}
            ${TrailingIcon || hasError ? 'pr-10' : 'pr-3.5'}
            py-2.5
            ${inputClassName}
          `}
          {...props}
        />

        {hasError ? (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none text-rose-500">
            <AlertCircle className="w-4 h-4" aria-hidden="true" />
          </div>
        ) : TrailingIcon ? (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none text-slate-400 dark:text-slate-500">
            {TrailingIcon}
          </div>
        ) : null}
      </div>

      {hasError && (
        <p id={errorId} className="mt-1.5 text-xs text-rose-600 dark:text-rose-400 flex items-center gap-1 font-medium">
          <span>{error}</span>
        </p>
      )}

      {!hasError && helperText && (
        <p id={helperId} className="mt-1.5 text-xs text-slate-500 dark:text-slate-400">
          {helperText}
        </p>
      )}
    </div>
  );
});

export default Input;
