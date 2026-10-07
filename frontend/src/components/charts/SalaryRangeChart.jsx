import React from 'react';
import { TrendingUp, Award, DollarSign } from 'lucide-react';
import Badge from '../ui/Badge';
import { formatSalary } from '../../utils/formatters';

/**
 * SalaryRangeChart
 * Renders LightGBM predicted salary range in INR LPA with market benchmarks
 */
export default function SalaryRangeChart({
  min = 14.5,
  max = 22.0,
  currency = 'INR',
  unit = 'LPA',
  topFactors = [],
}) {
  const mid = ((Number(min) + Number(max)) / 2).toFixed(1);

  return (
    <div className="space-y-6">
      {/* Primary KPI Card */}
      <div className="bg-gradient-to-br from-brand-500/10 via-brand-500/5 to-transparent dark:from-brand-950/40 dark:via-slate-900 rounded-2xl p-6 border border-brand-200 dark:border-brand-900/50">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-brand-600 dark:text-brand-400 flex items-center gap-1.5">
            <TrendingUp className="w-3.5 h-3.5" />
            LightGBM Market Predictor
          </span>
          <Badge variant="primary" size="sm">
            95% Confidence
          </Badge>
        </div>

        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white tracking-tight">
            {formatSalary(min, max, currency, unit)}
          </span>
        </div>

        <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">
          Midpoint estimate is{' '}
          <strong className="text-slate-700 dark:text-slate-300">₹{mid} LPA</strong> based on
          current candidate profile, NLP extracted skill tags, and active Indian tech hiring feeds.
        </p>

        {/* Visual Range Bar */}
        <div className="mt-6 space-y-2">
          <div className="flex justify-between text-2xs font-semibold text-slate-500 dark:text-slate-400">
            <span>Entry (₹8 LPA)</span>
            <span className="text-brand-600 dark:text-brand-400 font-bold">Predicted Range</span>
            <span>Senior Cap (₹35 LPA)</span>
          </div>

          <div className="relative h-4 bg-slate-200 dark:bg-slate-700/60 rounded-full overflow-hidden">
            {/* Shaded predicted region */}
            <div
              className="absolute top-0 bottom-0 bg-gradient-to-r from-brand-500 to-indigo-600 rounded-full shadow-glow-brand"
              style={{
                left: `${Math.max(10, Math.min(80, (min / 35) * 100))}%`,
                width: `${Math.max(15, Math.min(50, ((max - min) / 35) * 100))}%`,
              }}
            />
          </div>

          <div className="flex justify-between text-2xs text-slate-400">
            <span>Market Low</span>
            <span>Indian Tech Industry Benchmarks</span>
            <span>Market Top 10%</span>
          </div>
        </div>
      </div>

      {/* Top Value Drivers */}
      {topFactors && topFactors.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Key LightGBM Feature Importances
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {topFactors.map((factor, idx) => (
              <div
                key={idx}
                className="flex items-center gap-2 p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200/80 dark:border-slate-700/80 text-xs text-slate-700 dark:text-slate-300"
              >
                <div className="w-1.5 h-1.5 rounded-full bg-brand-500" />
                <span className="font-medium">{factor}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
