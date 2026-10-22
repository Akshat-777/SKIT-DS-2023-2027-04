import React from 'react';
import { Target, Filter, Briefcase, CheckCircle2, AlertCircle, AlertTriangle, TrendingUp, Layers } from 'lucide-react';
import Badge from '../ui/Badge';

export const TARGET_ROLES = [
  'Data Scientist / ML Engineer',
  'Full Stack AI Engineer',
  'DevOps & Cloud Architect',
  'Data Platform Engineer',
];

/**
 * SkillFiltersBar Component
 * Target role switcher and interactive gap category toggle (Missing, Weak, Trending, Matched, All)
 */
export default function SkillFiltersBar({
  selectedRole,
  onRoleChange,
  activeFilter = 'all', // 'all' | 'missing' | 'weak' | 'trending' | 'matched'
  onFilterChange,
  counts = { missing: 0, weak: 0, trending: 0, matched: 0 },
  className = '',
}) {
  const filterTabs = [
    {
      id: 'all',
      label: 'All Insights',
      icon: Layers,
      count: counts.missing + counts.weak + counts.trending + counts.matched,
    },
    {
      id: 'missing',
      label: 'Missing Gaps',
      icon: AlertCircle,
      count: counts.missing,
      color: 'text-rose-600 dark:text-rose-400',
    },
    {
      id: 'weak',
      label: 'Weak Evidence',
      icon: AlertTriangle,
      count: counts.weak,
      color: 'text-amber-600 dark:text-amber-400',
    },
    {
      id: 'trending',
      label: 'Trending Signals',
      icon: TrendingUp,
      count: counts.trending,
      color: 'text-indigo-600 dark:text-indigo-400',
    },
    {
      id: 'matched',
      label: 'Matched Skills',
      icon: CheckCircle2,
      count: counts.matched,
      color: 'text-emerald-600 dark:text-emerald-400',
    },
  ];

  return (
    <div
      className={`p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-sm flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 ${className}`}
    >
      {/* Target Role Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-2.5">
        <label
          htmlFor="target-role-select"
          className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5 shrink-0"
        >
          <Target className="w-4 h-4 text-brand-500" />
          <span>Target Role:</span>
        </label>
        <div className="relative">
          <select
            id="target-role-select"
            value={selectedRole}
            onChange={(e) => onRoleChange && onRoleChange(e.target.value)}
            className="w-full sm:w-auto pl-3 pr-8 py-1.5 text-xs font-semibold rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500 cursor-pointer"
          >
            {TARGET_ROLES.map((role) => (
              <option key={role} value={role}>
                {role}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Category Toggle: All, Missing, Weak, Trending, Matched */}
      <div
        role="tablist"
        aria-label="Skill Gap Category Filter"
        className="flex items-center gap-1 overflow-x-auto pb-1 md:pb-0 scrollbar-none"
      >
        {filterTabs.map((tab) => {
          const isActive = activeFilter === tab.id;
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              role="tab"
              id={`filter-tab-${tab.id}`}
              aria-selected={isActive}
              aria-controls={`panel-${tab.id}`}
              onClick={() => onFilterChange && onFilterChange(tab.id)}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all focus:outline-none focus:ring-2 focus:ring-brand-500 ${
                isActive
                  ? 'bg-brand-600 text-white shadow-xs'
                  : 'bg-slate-100 dark:bg-slate-800/80 text-slate-600 dark:text-slate-300 hover:bg-slate-200/80 dark:hover:bg-slate-700'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
              {typeof tab.count === 'number' && (
                <span
                  className={`text-2xs font-mono font-bold px-1.5 py-0.2 rounded-full ${
                    isActive
                      ? 'bg-white/25 text-white'
                      : 'bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300'
                  }`}
                >
                  {tab.count}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
