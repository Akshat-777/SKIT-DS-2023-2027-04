import React from 'react';
import Button from './Button';

/**
 * CareerLens EmptyState Component
 * Displays helpful illustrations, guidance, and primary actions when no data is available
 * (e.g., initial resume upload, empty search filters, or no roadmaps generated).
 */
export default function EmptyState({
  icon: Icon = null,
  title = 'No records found',
  description = 'There is currently no data available to display.',
  action = null,
  secondaryAction = null,
  className = '',
}) {
  return (
    <div
      className={`flex flex-col items-center justify-center text-center p-8 sm:p-12 rounded-2xl border-2 border-dashed border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/40 ${className}`}
    >
      {Icon && (
        <div className="w-14 h-14 rounded-2xl bg-brand-50 dark:bg-brand-950/60 border border-brand-200 dark:border-brand-800/80 text-brand-600 dark:text-brand-400 flex items-center justify-center mb-4 shadow-subtle">
          {React.isValidElement(Icon) ? Icon : <Icon className="w-7 h-7" />}
        </div>
      )}

      <h3 className="text-base sm:text-lg font-bold text-slate-900 dark:text-slate-100 mb-1.5">
        {title}
      </h3>

      <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 max-w-md mb-6 leading-relaxed">
        {description}
      </p>

      {(action || secondaryAction) && (
        <div className="flex flex-wrap items-center justify-center gap-3">
          {action && (
            <Button
              variant={action.variant || 'primary'}
              size={action.size || 'md'}
              icon={action.icon}
              onClick={action.onClick}
            >
              {action.label}
            </Button>
          )}

          {secondaryAction && (
            <Button
              variant="outline"
              size={secondaryAction.size || 'md'}
              icon={secondaryAction.icon}
              onClick={secondaryAction.onClick}
            >
              {secondaryAction.label}
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
