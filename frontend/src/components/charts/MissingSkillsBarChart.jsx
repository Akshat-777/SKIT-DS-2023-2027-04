import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
  CartesianGrid,
} from 'recharts';
import { AlertCircle, ChevronRight, ExternalLink } from 'lucide-react';

/**
 * Custom Tooltip for Missing Skills Bar Chart
 */
function CustomBarTooltip({ active, payload }) {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="p-3 bg-slate-900 text-white rounded-xl shadow-xl border border-slate-700 text-xs space-y-1">
        <p className="font-bold text-white flex items-center gap-1.5">
          <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
          {data.skill}
        </p>
        <p className="text-slate-300">
          Market Demand:{' '}
          <span className="font-mono font-bold text-rose-400">{data.demand_pct}%</span>
        </p>
        <p className="text-3xs text-slate-400 pt-1 border-t border-slate-800">
          💡 Click bar or row to view why this matters for ATS
        </p>
      </div>
    );
  }
  return null;
}

/**
 * MissingSkillsBarChart Component
 * Horizontal bar chart of missing skills ranked by market demand_pct
 */
export default function MissingSkillsBarChart({
  missing = [],
  onSelectSkill,
  height = 280,
}) {
  // Normalize and rank missing skills descending by demand_pct
  const rankedData = [...missing]
    .map((item) => {
      if (typeof item === 'string') {
        return { skill: item, demand_pct: 75 };
      }
      return {
        skill: item.skill,
        demand_pct: Number(item.demand_pct) || 0,
      };
    })
    .sort((a, b) => b.demand_pct - a.demand_pct);

  if (rankedData.length === 0) {
    return (
      <div className="h-48 flex flex-col items-center justify-center text-center p-6 bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-dashed border-slate-200 dark:border-slate-700">
        <span className="text-2xl mb-1">🎉</span>
        <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">
          No Missing Skills Detected!
        </p>
        <p className="text-xs text-slate-500 max-w-sm mt-1">
          Your profile matches all high-demand competencies tracked for this target role.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Chart container with min-w-0 to prevent flex/grid container overflow */}
      <div
        className="w-full min-w-0"
        style={{ height }}
        role="img"
        aria-label="Horizontal bar chart showing missing skills ranked by market demand percentage"
      >
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={rankedData}
            layout="vertical"
            margin={{ top: 10, right: 30, left: 10, bottom: 5 }}
            onClick={(state) => {
              if (state && state.activePayload && state.activePayload.length) {
                const clickedItem = state.activePayload[0].payload;
                if (onSelectSkill) onSelectSkill(clickedItem.skill, 'missing');
              }
            }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              horizontal={false}
              className="stroke-slate-200 dark:stroke-slate-800"
            />
            <XAxis
              type="number"
              domain={[0, 100]}
              unit="%"
              tick={{ fontSize: 11 }}
              tickLine={false}
              axisLine={{ stroke: '#94a3b8' }}
              className="text-slate-500"
            />
            <YAxis
              type="category"
              dataKey="skill"
              width={130}
              tick={{ fontSize: 11, fill: 'currentColor' }}
              tickLine={false}
              axisLine={{ stroke: '#94a3b8' }}
              className="text-slate-700 dark:text-slate-300 font-medium"
            />
            <Tooltip content={<CustomBarTooltip />} cursor={{ fill: 'rgba(244, 63, 94, 0.08)' }} />
            <Bar
              dataKey="demand_pct"
              name="Market Demand"
              radius={[0, 6, 6, 0]}
              className="cursor-pointer transition-opacity hover:opacity-85"
            >
              {rankedData.map((entry, index) => {
                // Color variation based on urgency
                const fill =
                  entry.demand_pct >= 85
                    ? '#EF4444' // Rose / High Alert
                    : entry.demand_pct >= 75
                    ? '#F43F5E'
                    : '#FB7185';
                return <Cell key={`cell-${index}`} fill={fill} />;
              })}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Interactive Quick-Click List */}
      <div className="space-y-1.5 pt-2 border-t border-slate-100 dark:border-slate-800">
        <span className="text-2xs font-bold uppercase tracking-wider text-slate-400 block mb-1">
          Missing Gaps (Click to open actionable ATS guide):
        </span>
        {rankedData.map((item, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => onSelectSkill && onSelectSkill(item.skill, 'missing')}
            className="w-full flex items-center justify-between p-2 rounded-lg text-left text-xs bg-rose-50/50 dark:bg-rose-950/20 border border-rose-100 dark:border-rose-900/40 hover:bg-rose-100/70 dark:hover:bg-rose-950/40 transition-colors group focus:outline-none focus:ring-2 focus:ring-rose-500"
          >
            <span className="font-semibold text-slate-800 dark:text-slate-200 group-hover:text-rose-600 dark:group-hover:text-rose-400 flex items-center gap-1.5">
              <span className="text-rose-500 font-bold">•</span>
              {item.skill}
            </span>
            <div className="flex items-center gap-2">
              <span className="font-mono text-2xs text-rose-600 dark:text-rose-400 font-bold">
                {item.demand_pct}% Demand
              </span>
              <ChevronRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-rose-500 transition-transform group-hover:translate-x-0.5" />
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
