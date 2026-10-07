import React, { useRef } from 'react';

/**
 * CareerLens Accessible Tabs Component
 * Supports keyboard navigation (Left/Right/Home/End arrows),
 * ARIA tablist/tab roles, and 'underline' or 'pills' visual variants.
 */
export default function Tabs({
  tabs,
  activeTab,
  onChange,
  variant = 'underline',
  className = '',
}) {
  const tabRefs = useRef([]);

  const handleKeyDown = (e, index) => {
    let newIndex = index;
    if (e.key === 'ArrowRight') {
      newIndex = (index + 1) % tabs.length;
    } else if (e.key === 'ArrowLeft') {
      newIndex = (index - 1 + tabs.length) % tabs.length;
    } else if (e.key === 'Home') {
      newIndex = 0;
    } else if (e.key === 'End') {
      newIndex = tabs.length - 1;
    } else {
      return;
    }

    e.preventDefault();
    if (!tabs[newIndex]?.disabled) {
      onChange(tabs[newIndex].id);
      tabRefs.current[newIndex]?.focus();
    }
  };

  const isUnderline = variant === 'underline';

  return (
    <div
      role="tablist"
      aria-orientation="horizontal"
      className={`flex items-center gap-1.5 ${
        isUnderline
          ? 'border-b border-slate-200 dark:border-slate-800'
          : 'bg-slate-100 dark:bg-slate-800/60 p-1 rounded-xl'
      } ${className}`}
    >
      {tabs.map((tab, idx) => {
        const isActive = activeTab === tab.id;
        const Icon = tab.icon;

        return (
          <button
            key={tab.id}
            ref={(el) => (tabRefs.current[idx] = el)}
            role="tab"
            id={`tab-${tab.id}`}
            aria-selected={isActive}
            aria-controls={`panel-${tab.id}`}
            tabIndex={isActive ? 0 : -1}
            disabled={tab.disabled}
            onClick={() => !tab.disabled && onChange(tab.id)}
            onKeyDown={(e) => handleKeyDown(e, idx)}
            className={`
              inline-flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-lg transition-all duration-150 whitespace-nowrap
              focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-1 dark:focus:ring-offset-slate-900
              ${tab.disabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'}
              ${
                isUnderline
                  ? isActive
                    ? 'text-brand-600 dark:text-brand-400 border-b-2 border-brand-600 dark:border-brand-400 rounded-b-none pb-[calc(0.5rem-2px)]'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:border-b-2 hover:border-slate-300 dark:hover:border-slate-700'
                  : isActive
                  ? 'bg-white dark:bg-slate-900 text-brand-600 dark:text-brand-400 shadow-xs'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
              }
            `}
          >
            {Icon && <span className="w-4 h-4">{Icon}</span>}
            <span>{tab.label}</span>
            {tab.badge !== undefined && (
              <span
                className={`ml-1 text-2xs px-1.5 py-0.5 rounded-full font-bold ${
                  isActive
                    ? 'bg-brand-100 text-brand-700 dark:bg-brand-950 dark:text-brand-300'
                    : 'bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-300'
                }`}
              >
                {tab.badge}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
