import React from 'react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
} from 'recharts';
import { CheckCircle2, AlertCircle, AlertTriangle } from 'lucide-react';

/**
 * Custom Tooltip for Donut Chart
 */
function CustomDonutTooltip({ active, payload }) {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="p-2.5 bg-slate-900 text-white rounded-xl shadow-xl border border-slate-700 text-xs space-y-1">
        <p className="font-bold flex items-center gap-1.5" style={{ color: data.color }}>
          {data.name}
        </p>
        <p className="text-slate-300">
          Count: <span className="font-mono font-bold text-white">{data.value} skills</span>
        </p>
        <p className="text-slate-400 text-2xs">
          Share: <span className="font-mono font-bold text-white">{data.percent}%</span> of total
        </p>
      </div>
    );
  }
  return null;
}

/**
 * SkillGapDonutChart Component
 * Displays matched vs missing vs weak summary donut chart using Recharts
 */
export default function SkillGapDonutChart({
  matched = [],
  missing = [],
  weak = [],
  onSelectCategory,
  height = 240,
}) {
  const matchedCount = Array.isArray(matched) ? matched.length : Number(matched) || 0;
  const missingCount = Array.isArray(missing) ? missing.length : Number(missing) || 0;
  const weakCount = Array.isArray(weak) ? weak.length : Number(weak) || 0;
  const total = matchedCount + missingCount + weakCount;

  const matchedPct = total > 0 ? Math.round((matchedCount / total) * 100) : 0;
  const missingPct = total > 0 ? Math.round((missingCount / total) * 100) : 0;
  const weakPct = total > 0 ? Math.round((weakCount / total) * 100) : 0;

  const data = [
    {
      id: 'matched',
      name: 'Matched Competencies',
      value: matchedCount,
      percent: matchedPct,
      color: '#10B981', // Emerald
      icon: CheckCircle2,
      ariaLabel: `${matchedCount} Matched competencies, ${matchedPct}% of evaluated skills`,
    },
    {
      id: 'missing',
      name: 'Missing Gaps',
      value: missingCount,
      percent: missingPct,
      color: '#EF4444', // Rose / Red
      icon: AlertCircle,
      ariaLabel: `${missingCount} Missing high-demand gaps, ${missingPct}% of evaluated skills`,
    },
    {
      id: 'weak',
      name: 'Weak / Under-Quantified',
      value: weakCount,
      percent: weakPct,
      color: '#F59E0B', // Amber
      icon: AlertTriangle,
      ariaLabel: `${weakCount} Weak or under-quantified skills, ${weakPct}% of evaluated skills`,
    },
  ].filter((item) => item.value > 0);

  return (
    <div className="flex flex-col items-center justify-center space-y-4">
      {/* Donut Chart with Center Metric */}
      <div
        className="relative w-full min-w-0 flex items-center justify-center"
        style={{ height }}
        role="img"
        aria-label={`Donut chart showing skill distribution: ${matchedCount} matched, ${missingCount} missing, ${weakCount} weak.`}
      >
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Tooltip content={<CustomDonutTooltip />} />
            <Pie
              data={data.length > 0 ? data : [{ name: 'None', value: 1, color: '#94a3b8' }]}
              cx="50%"
              cy="50%"
              innerRadius={55}
              outerRadius={85}
              paddingAngle={3}
              dataKey="value"
              className="cursor-pointer"
              onClick={(entry) => {
                if (entry && onSelectCategory) onSelectCategory(entry.id);
              }}
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} stroke="transparent" />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>

        {/* Center Summary Label */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none select-none">
          <span className="text-2xl font-black font-mono text-slate-900 dark:text-slate-100">
            {matchedPct}%
          </span>
          <span className="text-3xs uppercase font-bold tracking-wider text-slate-400">
            Matched Fit
          </span>
        </div>
      </div>

      {/* Accessible Interactive Legend with Counts & Percentages */}
      <div className="w-full grid grid-cols-1 sm:grid-cols-3 gap-2 pt-2 border-t border-slate-100 dark:border-slate-800 text-xs">
        {/* Matched */}
        <button
          type="button"
          onClick={() => onSelectCategory && onSelectCategory('matched')}
          className="p-2 rounded-lg bg-emerald-50/70 dark:bg-emerald-950/30 border border-emerald-200/60 dark:border-emerald-900/40 text-left hover:bg-emerald-100/60 transition-colors focus:outline-none focus:ring-2 focus:ring-emerald-500"
        >
          <div className="flex items-center gap-1.5 text-emerald-700 dark:text-emerald-300 font-bold text-2xs">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
            <span>Matched</span>
          </div>
          <div className="flex items-baseline justify-between mt-1">
            <span className="text-sm font-black font-mono text-emerald-900 dark:text-emerald-100">
              {matchedCount}
            </span>
            <span className="text-2xs text-emerald-600 dark:text-emerald-400 font-semibold font-mono">
              {matchedPct}%
            </span>
          </div>
        </button>

        {/* Missing */}
        <button
          type="button"
          onClick={() => onSelectCategory && onSelectCategory('missing')}
          className="p-2 rounded-lg bg-rose-50/70 dark:bg-rose-950/30 border border-rose-200/60 dark:border-rose-900/40 text-left hover:bg-rose-100/60 transition-colors focus:outline-none focus:ring-2 focus:ring-rose-500"
        >
          <div className="flex items-center gap-1.5 text-rose-700 dark:text-rose-300 font-bold text-2xs">
            <AlertCircle className="w-3.5 h-3.5 text-rose-500" />
            <span>Missing</span>
          </div>
          <div className="flex items-baseline justify-between mt-1">
            <span className="text-sm font-black font-mono text-rose-900 dark:text-rose-100">
              {missingCount}
            </span>
            <span className="text-2xs text-rose-600 dark:text-rose-400 font-semibold font-mono">
              {missingPct}%
            </span>
          </div>
        </button>

        {/* Weak */}
        <button
          type="button"
          onClick={() => onSelectCategory && onSelectCategory('weak')}
          className="p-2 rounded-lg bg-amber-50/70 dark:bg-amber-950/30 border border-amber-200/60 dark:border-amber-900/40 text-left hover:bg-amber-100/60 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500"
        >
          <div className="flex items-center gap-1.5 text-amber-700 dark:text-amber-300 font-bold text-2xs">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
            <span>Weak</span>
          </div>
          <div className="flex items-baseline justify-between mt-1">
            <span className="text-sm font-black font-mono text-amber-900 dark:text-amber-100">
              {weakCount}
            </span>
            <span className="text-2xs text-amber-600 dark:text-amber-400 font-semibold font-mono">
              {weakPct}%
            </span>
          </div>
        </button>
      </div>
    </div>
  );
}
