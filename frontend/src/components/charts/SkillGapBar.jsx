import React from 'react';
import Badge from '../ui/Badge';
import ProgressBar from '../ui/ProgressBar';

/**
 * SkillGapBar
 * Displays individual skill with live market demand percentage, matching status, and trend indicator.
 */
export default function SkillGapBar({
  skill,
  demandPct = 80,
  status = 'matched', // 'matched' | 'missing' | 'weak' | 'trending'
}) {
  const getStatusBadge = () => {
    switch (status) {
      case 'matched':
        return (
          <Badge variant="success" size="sm">
            In Resume
          </Badge>
        );
      case 'missing':
        return (
          <Badge variant="danger" size="sm">
            Missing Gap
          </Badge>
        );
      case 'weak':
        return (
          <Badge variant="warning" size="sm">
            Weak Signal
          </Badge>
        );
      case 'trending':
        return (
          <Badge variant="primary" size="sm">
            Trending Market
          </Badge>
        );
      default:
        return (
          <Badge variant="neutral" size="sm">
            {status}
          </Badge>
        );
    }
  };

  const getProgressVariant = () => {
    switch (status) {
      case 'matched':
        return 'success';
      case 'missing':
        return 'danger';
      case 'weak':
        return 'warning';
      default:
        return 'primary';
    }
  };

  return (
    <div className="p-3 bg-white dark:bg-slate-800/80 rounded-xl border border-slate-200/80 dark:border-slate-700/80 space-y-2 hover:border-brand-300 dark:hover:border-slate-600 transition-colors">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-900 dark:text-slate-100">{skill}</span>
        <div className="flex items-center gap-2">
          {getStatusBadge()}
          <span className="text-2xs font-mono text-slate-500">{demandPct}% demand</span>
        </div>
      </div>
      <ProgressBar value={demandPct} variant={getProgressVariant()} showValue={false} />
    </div>
  );
}
