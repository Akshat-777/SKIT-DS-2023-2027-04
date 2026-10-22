import React from 'react';
import { BREAKDOWN_METRIC_CONFIG, getAtsScoreTier } from '../../utils/scoreThresholds';
import Badge from '../ui/Badge';

/**
 * AccessibleDataTable Component
 * Renders complete tabular representation of chart data for screen readers
 * and keyboard/table users following WCAG 2.1 AA accessibility guidelines.
 */
export default function AccessibleDataTable({
  scoreResult,
  className = '',
}) {
  if (!scoreResult) return null;

  const { ats_score, breakdown = {}, skill_gap = {} } = scoreResult;
  const missing = skill_gap.missing || [];
  const matched = skill_gap.matched || [];
  const weak = skill_gap.weak || [];
  const trending = skill_gap.trending || [];

  const totalSkills = matched.length + missing.length + weak.length;

  return (
    <div
      role="region"
      aria-label="Accessible Data Tables for ATS Scores and Skill Gaps"
      className={`space-y-6 ${className}`}
    >
      {/* 1. Missing Skills Accessible Table */}
      <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
        <table className="w-full text-left text-xs">
          <caption className="p-3 text-sm font-bold text-slate-900 dark:text-slate-100 bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-left">
            Table 1: Missing Skills Ranked by Live Market Demand
          </caption>
          <thead>
            <tr className="border-b border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-800/40 text-slate-600 dark:text-slate-300">
              <th scope="col" className="p-3 font-semibold">Priority Rank</th>
              <th scope="col" className="p-3 font-semibold">Missing Skill</th>
              <th scope="col" className="p-3 font-semibold">Market Demand</th>
              <th scope="col" className="p-3 font-semibold">Urgency Status</th>
              <th scope="col" className="p-3 font-semibold">Recommended ATS Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {missing.length === 0 ? (
              <tr>
                <td colSpan="5" className="p-4 text-center text-slate-500 italic">
                  No missing skills found. All core competencies matched.
                </td>
              </tr>
            ) : (
              missing.map((item, idx) => {
                const skillName = typeof item === 'string' ? item : item.skill;
                const demand = typeof item === 'string' ? 75 : item.demand_pct;
                const isCritical = demand >= 80;
                return (
                  <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                    <th scope="row" className="p-3 font-mono font-bold text-slate-500">
                      #{idx + 1}
                    </th>
                    <td className="p-3 font-bold text-slate-900 dark:text-slate-100">
                      {skillName}
                    </td>
                    <td className="p-3 font-mono font-semibold text-rose-600 dark:text-rose-400">
                      {demand}%
                    </td>
                    <td className="p-3">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-2xs font-bold ${
                          isCritical
                            ? 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300'
                            : 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
                        }`}
                      >
                        {isCritical ? 'Critical Priority' : 'High Priority'}
                      </span>
                    </td>
                    <td className="p-3 text-slate-600 dark:text-slate-300 max-w-xs">
                      Add hands-on evidence and Google XYZ bullet points to resume.
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* 2. ATS 6-Dimension Score Breakdown Table */}
      <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
        <table className="w-full text-left text-xs">
          <caption className="p-3 text-sm font-bold text-slate-900 dark:text-slate-100 bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-left">
            Table 2: 6-Dimension Recruiter ATS Score Matrix
          </caption>
          <thead>
            <tr className="border-b border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-800/40 text-slate-600 dark:text-slate-300">
              <th scope="col" className="p-3 font-semibold">Evaluation Dimension</th>
              <th scope="col" className="p-3 font-semibold">Weight</th>
              <th scope="col" className="p-3 font-semibold">Score</th>
              <th scope="col" className="p-3 font-semibold">Tier Classification</th>
              <th scope="col" className="p-3 font-semibold">Plain-English Metric Description</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {Object.entries(BREAKDOWN_METRIC_CONFIG).map(([key, config]) => {
              const val = breakdown[key] ?? 0;
              const tier = getAtsScoreTier(val);
              return (
                <tr key={key} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                  <th scope="row" className="p-3 font-bold text-slate-900 dark:text-slate-100">
                    {config.label}
                  </th>
                  <td className="p-3 font-mono text-slate-500 font-semibold">{config.weight}</td>
                  <td className="p-3 font-mono font-bold text-slate-900 dark:text-slate-100">
                    {val}%
                  </td>
                  <td className="p-3">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-2xs font-bold ${tier.bgClass} ${tier.textClass}`}
                    >
                      {tier.tier} ({tier.shortDesc})
                    </span>
                  </td>
                  <td className="p-3 text-slate-600 dark:text-slate-300 max-w-sm">
                    {config.tooltip}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* 3. Skill Competency Portfolio Distribution Table */}
      <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
        <table className="w-full text-left text-xs">
          <caption className="p-3 text-sm font-bold text-slate-900 dark:text-slate-100 bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-left">
            Table 3: Skill Portfolio Summary Distribution
          </caption>
          <thead>
            <tr className="border-b border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-800/40 text-slate-600 dark:text-slate-300">
              <th scope="col" className="p-3 font-semibold">Skill Category</th>
              <th scope="col" className="p-3 font-semibold">Count</th>
              <th scope="col" className="p-3 font-semibold">Share of Profile</th>
              <th scope="col" className="p-3 font-semibold">Evaluation Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            <tr>
              <th scope="row" className="p-3 font-bold text-emerald-700 dark:text-emerald-300">
                Matched Core Competencies
              </th>
              <td className="p-3 font-mono font-bold">{matched.length}</td>
              <td className="p-3 font-mono">
                {totalSkills > 0 ? Math.round((matched.length / totalSkills) * 100) : 0}%
              </td>
              <td className="p-3 text-emerald-600 font-semibold">✓ Verified in resume</td>
            </tr>
            <tr>
              <th scope="row" className="p-3 font-bold text-rose-700 dark:text-rose-300">
                Missing High-Demand Skills
              </th>
              <td className="p-3 font-mono font-bold">{missing.length}</td>
              <td className="p-3 font-mono">
                {totalSkills > 0 ? Math.round((missing.length / totalSkills) * 100) : 0}%
              </td>
              <td className="p-3 text-rose-600 font-semibold">✗ Missing keyword gap</td>
            </tr>
            <tr>
              <th scope="row" className="p-3 font-bold text-amber-700 dark:text-amber-300">
                Weak / Under-Quantified Evidence
              </th>
              <td className="p-3 font-mono font-bold">{weak.length}</td>
              <td className="p-3 font-mono">
                {totalSkills > 0 ? Math.round((weak.length / totalSkills) * 100) : 0}%
              </td>
              <td className="p-3 text-amber-600 font-semibold">⚠️ Needs quantifiable metrics</td>
            </tr>
            <tr>
              <th scope="row" className="p-3 font-bold text-indigo-700 dark:text-indigo-300">
                Emerging 2026 Trending Signals
              </th>
              <td className="p-3 font-mono font-bold">{trending.length}</td>
              <td className="p-3 font-mono">External Signal</td>
              <td className="p-3 text-indigo-600 font-semibold">🔥 Market radar</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
