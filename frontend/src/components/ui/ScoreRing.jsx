import React from 'react';

/**
 * CareerLens ScoreRing Component
 * Recruiter-grade circular score indicator with dynamic color thresholding:
 * - Red (0-49): Critical Gaps / Needs Improvement
 * - Amber (50-74): Moderate Fit / Competitive
 * - Green (75-100): Exceptional / Recruiter-Ready
 * Accessible via role="meter" and aria values.
 */
export default function ScoreRing({
  score = 0,
  max = 100,
  size = 140,
  strokeWidth = 10,
  label = 'ATS Score',
  sublabel = null,
  showThresholdBadge = true,
  className = '',
}) {
  const normalizedScore = Math.min(100, Math.max(0, Math.round((score / max) * 100)));
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (normalizedScore / 100) * circumference;

  // Determine threshold level
  let thresholdConfig = {
    color: '#10B981', // green
    textColor: 'text-emerald-600 dark:text-emerald-400',
    bgColor: 'bg-emerald-50 dark:bg-emerald-950/60',
    borderColor: 'border-emerald-200 dark:border-emerald-800',
    status: 'Recruiter-Ready',
    glow: 'rgba(16, 185, 129, 0.25)',
  };

  if (normalizedScore < 50) {
    thresholdConfig = {
      color: '#EF4444', // red
      textColor: 'text-rose-600 dark:text-rose-400',
      bgColor: 'bg-rose-50 dark:bg-rose-950/60',
      borderColor: 'border-rose-200 dark:border-rose-800',
      status: 'Needs Polish',
      glow: 'rgba(239, 68, 68, 0.25)',
    };
  } else if (normalizedScore < 75) {
    thresholdConfig = {
      color: '#F59E0B', // amber
      textColor: 'text-amber-600 dark:text-amber-400',
      bgColor: 'bg-amber-50 dark:bg-amber-950/60',
      borderColor: 'border-amber-200 dark:border-amber-800',
      status: 'Moderate Fit',
      glow: 'rgba(245, 158, 11, 0.25)',
    };
  }

  return (
    <div
      role="meter"
      aria-label={label}
      aria-valuenow={normalizedScore}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuetext={`${normalizedScore} out of 100 - ${thresholdConfig.status}`}
      className={`inline-flex flex-col items-center justify-center ${className}`}
    >
      <div className="relative inline-flex items-center justify-center">
        <svg
          width={size}
          height={size}
          className="transform -rotate-90 origin-center drop-shadow-sm"
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
            stroke={thresholdConfig.color}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-out"
          />
        </svg>

        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <span className="text-3xl font-extrabold tracking-tight font-mono text-slate-900 dark:text-slate-100">
            {normalizedScore}
          </span>
          <span className="text-2xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
            / 100
          </span>
        </div>
      </div>

      {label && (
        <span className="mt-2 text-xs font-semibold text-slate-700 dark:text-slate-300">
          {label}
        </span>
      )}

      {showThresholdBadge && (
        <span
          className={`mt-1 text-2xs font-bold px-2 py-0.5 rounded-full border ${thresholdConfig.bgColor} ${thresholdConfig.textColor} ${thresholdConfig.borderColor}`}
        >
          {thresholdConfig.status}
        </span>
      )}

      {sublabel && (
        <span className="text-2xs text-slate-400 dark:text-slate-500 mt-0.5">
          {sublabel}
        </span>
      )}
    </div>
  );
}
