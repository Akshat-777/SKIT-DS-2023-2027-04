import React, { useState } from 'react';
import { Info, Lightbulb, ChevronDown, ChevronUp, CheckCircle2, AlertTriangle, AlertCircle, Sparkles } from 'lucide-react';
import { BREAKDOWN_METRIC_CONFIG, getAtsScoreTier, SCORE_TIERS } from '../../utils/scoreThresholds';
import Badge from '../ui/Badge';

/**
 * BreakdownCard Component
 * Displays one ATS breakdown dimension with:
 * - Metric title & weight
 * - Numeric score & tier badge (Poor/Fair/Good/Excellent)
 * - Mini progress bar
 * - Plain-English accessible tooltip
 * - "Improve this" hint callout
 */
export default function BreakdownCard({
  metricKey,
  score = 0,
  className = '',
}) {
  const [showTooltip, setShowTooltip] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  const config = BREAKDOWN_METRIC_CONFIG[metricKey] || {
    key: metricKey,
    label: metricKey.replace(/_/g, ' '),
    weight: '15%',
    tooltip: 'Evaluates resume relevance for target job specifications.',
    improveHint: 'Optimize this section to match target job requirements.',
  };

  const normalizedScore = Math.min(100, Math.max(0, Math.round(Number(score) || 0)));
  const tier = getAtsScoreTier(normalizedScore);

  const getTierIcon = () => {
    switch (tier.tier) {
      case SCORE_TIERS.EXCELLENT:
        return <CheckCircle2 className="w-3 h-3 text-emerald-500 shrink-0" aria-hidden="true" />;
      case SCORE_TIERS.GOOD:
        return <Sparkles className="w-3 h-3 text-blue-500 shrink-0" aria-hidden="true" />;
      case SCORE_TIERS.FAIR:
        return <AlertTriangle className="w-3 h-3 text-amber-500 shrink-0" aria-hidden="true" />;
      case SCORE_TIERS.POOR:
      default:
        return <AlertCircle className="w-3 h-3 text-rose-500 shrink-0" aria-hidden="true" />;
    }
  };

  return (
    <div
      data-testid={`breakdown-card-${metricKey}`}
      className={`p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-sm transition-all hover:border-slate-300 dark:hover:border-slate-700 flex flex-col justify-between ${className}`}
    >
      <div>
        {/* Header: Title, Weight & Tooltip */}
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="flex items-center gap-1.5 flex-wrap">
            <h4 className="text-xs sm:text-sm font-bold text-slate-900 dark:text-slate-100 leading-tight">
              {config.label}
            </h4>
            <span
              className="text-2xs font-mono font-medium px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400"
              title={`Factor weight in final ATS score calculation: ${config.weight}`}
            >
              {config.weight}
            </span>
          </div>

          {/* Plain-English Tooltip Trigger */}
          <div className="relative">
            <button
              type="button"
              aria-label={`Plain-English explanation for ${config.label}`}
              aria-expanded={showTooltip}
              aria-describedby={`tooltip-${metricKey}`}
              onMouseEnter={() => setShowTooltip(true)}
              onMouseLeave={() => setShowTooltip(false)}
              onFocus={() => setShowTooltip(true)}
              onBlur={() => setShowTooltip(false)}
              onClick={() => setShowTooltip(!showTooltip)}
              className="p-1 rounded-full text-slate-400 hover:text-brand-600 dark:hover:text-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <Info className="w-3.5 h-3.5" />
            </button>

            {/* Tooltip Popup */}
            {showTooltip && (
              <div
                id={`tooltip-${metricKey}`}
                role="tooltip"
                className="absolute right-0 bottom-full mb-2 z-30 w-64 p-2.5 rounded-lg bg-slate-900 text-white dark:bg-slate-800 dark:border dark:border-slate-700 text-xs shadow-xl animate-fade-in"
              >
                <div className="font-semibold text-brand-300 mb-1 flex items-center gap-1">
                  <Info className="w-3 h-3" />
                  What this measures:
                </div>
                <p className="text-2xs text-slate-200 leading-relaxed">
                  {config.tooltip}
                </p>
                <div className="mt-1.5 pt-1.5 border-t border-slate-700/80 text-3xs text-slate-400">
                  Weight: {config.weight} of composite ATS score
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Score & Tier Badge */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-baseline gap-1">
            <span
              data-testid={`score-value-${metricKey}`}
              className="text-xl sm:text-2xl font-black font-mono text-slate-900 dark:text-slate-100"
            >
              {normalizedScore}%
            </span>
            <span className="text-2xs text-slate-400 font-mono">/ 100%</span>
          </div>

          <div
            data-testid={`tier-badge-${metricKey}`}
            className={`inline-flex items-center gap-1 text-2xs font-bold px-2 py-0.5 rounded-md border ${tier.bgClass} ${tier.textClass} ${tier.borderClass}`}
          >
            {getTierIcon()}
            <span>{tier.tier}</span>
          </div>
        </div>

        {/* Mini Progress Bar with ARIA attributes */}
        <div
          role="progressbar"
          aria-label={`${config.label} progress`}
          aria-valuenow={normalizedScore}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuetext={`${normalizedScore}% - ${tier.tier}`}
          className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden"
        >
          <div
            className="h-full rounded-full transition-all duration-700 ease-out"
            style={{
              width: `${normalizedScore}%`,
              backgroundColor: tier.color,
            }}
          />
        </div>
      </div>

      {/* "Improve This" Hint Section */}
      <div className="mt-3 pt-2.5 border-t border-slate-100 dark:border-slate-800/80">
        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          aria-expanded={isExpanded}
          className="w-full flex items-center justify-between text-2xs font-semibold text-brand-600 dark:text-brand-400 hover:text-brand-700 dark:hover:text-brand-300 py-0.5 focus:outline-none"
        >
          <span className="flex items-center gap-1">
            <Lightbulb className="w-3.5 h-3.5 text-amber-500 shrink-0" />
            <span>How to improve this</span>
          </span>
          {isExpanded ? (
            <ChevronUp className="w-3.5 h-3.5" />
          ) : (
            <ChevronDown className="w-3.5 h-3.5" />
          )}
        </button>

        {/* Collapsible / Expandable Hint Body */}
        {isExpanded && (
          <div
            data-testid={`improve-hint-${metricKey}`}
            className="mt-2 p-2.5 rounded-lg bg-amber-50/70 dark:bg-amber-950/30 border border-amber-200/70 dark:border-amber-900/50 text-2xs text-slate-700 dark:text-slate-300 space-y-1 animate-fade-in"
          >
            <p className="font-semibold text-amber-900 dark:text-amber-200 flex items-center gap-1">
              ⚡ Actionable ATS Tip:
            </p>
            <p className="leading-relaxed">
              {config.improveHint}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
