import React from 'react';
import { getAtsScoreTier, SCORE_TIERS } from '../../utils/scoreThresholds';
import { CheckCircle2, AlertTriangle, AlertCircle, Sparkles } from 'lucide-react';

/**
 * CareerLens ScoreRing Component
 * Recruiter-grade circular score indicator with dynamic 4-tier color thresholding:
 * - Poor (< 50): Critical Gaps (Red)
 * - Fair (50-69): Moderate Fit (Amber)
 * - Good (70-84): Competitive (Blue)
 * - Excellent (85-100): Recruiter-Ready (Emerald)
 * 
 * Accessible via role="meter" and aria values.
 * Colors are never the only signal: displays numeric value, text tier, and icon.
 */
export default function ScoreRing({
  score = 0,
  max = 100,
  size = 150,
  strokeWidth = 12,
  label = 'Overall ATS Fit Score',
  sublabel = null,
  showThresholdBadge = true,
  showTierLegend = false,
  className = '',
}) {
  const normalizedScore = Math.min(100, Math.max(0, Math.round((Number(score) / max) * 100)));
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (normalizedScore / 100) * circumference;

  const tierInfo = getAtsScoreTier(normalizedScore);

  const getTierIcon = () => {
    switch (tierInfo.tier) {
      case SCORE_TIERS.EXCELLENT:
        return <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" aria-hidden="true" />;
      case SCORE_TIERS.GOOD:
        return <Sparkles className="w-3.5 h-3.5 text-blue-500 shrink-0" aria-hidden="true" />;
      case SCORE_TIERS.FAIR:
        return <AlertTriangle className="w-3.5 h-3.5 text-amber-500 shrink-0" aria-hidden="true" />;
      case SCORE_TIERS.POOR:
      default:
        return <AlertCircle className="w-3.5 h-3.5 text-rose-500 shrink-0" aria-hidden="true" />;
    }
  };

  return (
    <div
      role="meter"
      aria-label={label}
      aria-valuenow={normalizedScore}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuetext={`${normalizedScore} out of 100 - ${tierInfo.tier}: ${tierInfo.shortDesc}`}
      className={`inline-flex flex-col items-center justify-center text-center ${className}`}
    >
      <div className="relative inline-flex items-center justify-center">
        <svg
          width={size}
          height={size}
          className="transform -rotate-90 origin-center drop-shadow-sm"
          aria-hidden="true"
        >
          {/* Background track circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="transparent"
            stroke="currentColor"
            strokeWidth={strokeWidth}
            className="text-slate-100 dark:text-slate-800 transition-colors"
          />

          {/* Value stroke circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="transparent"
            stroke={tierInfo.color}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-out"
          />
        </svg>

        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center pointer-events-none select-none">
          <span
            className="text-3xl sm:text-4xl font-extrabold tracking-tight font-mono text-slate-900 dark:text-slate-100"
            data-testid="score-value"
          >
            {normalizedScore}
          </span>
          <span className="text-2xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
            / 100
          </span>
        </div>
      </div>

      {/* Label */}
      {label && (
        <span className="mt-3 text-sm font-semibold text-slate-800 dark:text-slate-200">
          {label}
        </span>
      )}

      {/* Threshold Badge with Icon & Text */}
      {showThresholdBadge && (
        <div
          data-testid="score-tier-badge"
          className={`mt-1.5 inline-flex items-center gap-1.5 text-xs font-bold px-2.5 py-1 rounded-full border ${tierInfo.bgClass} ${tierInfo.textClass} ${tierInfo.borderClass}`}
        >
          {getTierIcon()}
          <span>{tierInfo.tier}</span>
          <span className="text-2xs font-normal opacity-85">({tierInfo.shortDesc})</span>
        </div>
      )}

      {/* Sublabel */}
      {sublabel && (
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-[220px]">
          {sublabel}
        </p>
      )}

      {/* Color Threshold Zone Scale (Ensures accessible visual calibration) */}
      {showTierLegend && (
        <div
          aria-label="Score threshold tiers"
          className="mt-4 w-full pt-3 border-t border-slate-100 dark:border-slate-800 grid grid-cols-4 gap-1 text-center text-2xs"
        >
          <div className={`p-1 rounded ${normalizedScore < 50 ? 'bg-rose-100/70 dark:bg-rose-950/80 font-bold' : ''}`}>
            <span className="text-slate-400 block font-mono">POOR</span>
            <span className="font-bold text-rose-500">&lt;50</span>
          </div>
          <div className={`p-1 rounded ${normalizedScore >= 50 && normalizedScore < 70 ? 'bg-amber-100/70 dark:bg-amber-950/80 font-bold' : ''}`}>
            <span className="text-slate-400 block font-mono">FAIR</span>
            <span className="font-bold text-amber-500">50-69</span>
          </div>
          <div className={`p-1 rounded ${normalizedScore >= 70 && normalizedScore < 85 ? 'bg-blue-100/70 dark:bg-blue-950/80 font-bold' : ''}`}>
            <span className="text-slate-400 block font-mono">GOOD</span>
            <span className="font-bold text-blue-500">70-84</span>
          </div>
          <div className={`p-1 rounded ${normalizedScore >= 85 ? 'bg-emerald-100/70 dark:bg-emerald-950/80 font-bold' : ''}`}>
            <span className="text-slate-400 block font-mono">EXCELLENT</span>
            <span className="font-bold text-emerald-500">85+</span>
          </div>
        </div>
      )}
    </div>
  );
}
