import React from 'react';

/**
 * CareerLens Card Component System
 * Clean, modern surface cards with flexible header, title, description, content, and footer subcomponents.
 */
export function Card({
  children,
  variant = 'default',
  className = '',
  onClick,
  ...props
}) {
  const isInteractive = variant === 'interactive' || Boolean(onClick);

  const variantStyles = {
    default: 'bg-white dark:bg-slate-850 border border-slate-200 dark:border-slate-800 shadow-subtle',
    elevated: 'bg-white dark:bg-slate-850 border border-slate-100 dark:border-slate-800 shadow-card',
    outline: 'bg-transparent border border-slate-300 dark:border-slate-700',
    interactive: 'bg-white dark:bg-slate-850 border border-slate-200 dark:border-slate-800 shadow-subtle hover:shadow-card-hover hover:border-brand-500/40 dark:hover:border-brand-500/40 cursor-pointer transition-all duration-200 hover:-translate-y-0.5',
  };

  const Component = isInteractive ? 'div' : 'article';

  return (
    <Component
      onClick={onClick}
      role={isInteractive ? 'button' : undefined}
      tabIndex={isInteractive ? 0 : undefined}
      onKeyDown={
        isInteractive
          ? (e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                onClick && onClick(e);
              }
            }
          : undefined
      }
      className={`rounded-xl overflow-hidden ${variantStyles[variant] || variantStyles.default} ${
        isInteractive ? 'focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2 dark:focus:ring-offset-slate-900' : ''
      } ${className}`}
      {...props}
    >
      {children}
    </Component>
  );
}

export function CardHeader({ children, className = '' }) {
  return (
    <div className={`p-5 pb-3 border-b border-slate-100 dark:border-slate-800/80 ${className}`}>
      {children}
    </div>
  );
}

export function CardTitle({ children, className = '', as: Component = 'h3' }) {
  return (
    <Component className={`text-base font-semibold text-slate-900 dark:text-slate-100 tracking-tight flex items-center justify-between gap-2 ${className}`}>
      {children}
    </Component>
  );
}

export function CardDescription({ children, className = '' }) {
  return (
    <p className={`text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed ${className}`}>
      {children}
    </p>
  );
}

export function CardContent({ children, className = '', noPadding = false }) {
  return (
    <div className={`${noPadding ? '' : 'p-5'} ${className}`}>
      {children}
    </div>
  );
}

export function CardFooter({ children, className = '' }) {
  return (
    <div className={`p-4 px-5 bg-slate-50/50 dark:bg-slate-900/50 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between gap-3 text-xs text-slate-500 dark:text-slate-400 ${className}`}>
      {children}
    </div>
  );
}

export default Card;
