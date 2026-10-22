import React from 'react';
import BreakdownCard from './BreakdownCard';

const METRIC_KEYS = [
  'keyword_match',
  'semantic_similarity',
  'section_completeness',
  'formatting',
  'experience_relevance',
  'quantified_impact',
];

/**
 * BreakdownGrid Component
 * Renders the 6 breakdown metrics in an accessible, responsive grid:
 * 3 columns on desktop, 2 on tablet, 1 on mobile.
 */
export default function BreakdownGrid({
  breakdown = {},
  className = '',
}) {
  return (
    <div
      role="region"
      aria-label="ATS 6-Factor Breakdown Metrics"
      className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 ${className}`}
    >
      {METRIC_KEYS.map((key) => (
        <BreakdownCard
          key={key}
          metricKey={key}
          score={breakdown[key] ?? 0}
        />
      ))}
    </div>
  );
}
