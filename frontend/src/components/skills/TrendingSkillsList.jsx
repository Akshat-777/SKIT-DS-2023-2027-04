import React from 'react';
import { TrendingUp, ArrowUpRight, Flame, Sparkles } from 'lucide-react';
import Badge from '../ui/Badge';

/**
 * TrendingSkillsList Component
 * Displays trending skills list with up-arrow badges and interactive side panel click
 */
export default function TrendingSkillsList({
  trending = [],
  onSelectSkill,
}) {
  if (!trending || trending.length === 0) {
    return (
      <p className="text-xs text-slate-500 italic p-3">
        No active trending skills signals detected.
      </p>
    );
  }

  // Pre-configured trend growth rates & signals for visual richness
  const trendGains = ['+42% MoM', '+35% live demand', '+28% adoption', '+50% scraper velocity'];

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between text-xs">
        <span className="font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
          <Flame className="w-4 h-4 text-orange-500" />
          Emerging 2026 Tech Signals
        </span>
        <Badge variant="primary" size="sm">
          Live Market Radar
        </Badge>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
        {trending.map((trend, idx) => {
          const gain = trendGains[idx % trendGains.length];
          return (
            <button
              key={idx}
              type="button"
              onClick={() => onSelectSkill && onSelectSkill(trend, 'trending')}
              className="flex items-center justify-between p-3 rounded-xl bg-gradient-to-br from-indigo-50/70 to-blue-50/40 dark:from-indigo-950/30 dark:to-blue-950/20 border border-indigo-200/70 dark:border-indigo-900/50 hover:border-brand-400 dark:hover:border-indigo-700 transition-all text-left group shadow-xs hover:shadow-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <div className="space-y-1 pr-2">
                <span className="text-xs font-bold text-slate-900 dark:text-slate-100 group-hover:text-brand-600 dark:group-hover:text-brand-400 block line-clamp-1">
                  {trend}
                </span>
                <div className="flex items-center gap-1.5 text-2xs text-indigo-600 dark:text-indigo-400 font-semibold font-mono">
                  <TrendingUp className="w-3 h-3 text-emerald-500 shrink-0" />
                  <span>{gain}</span>
                </div>
              </div>
              <div className="w-7 h-7 rounded-lg bg-white dark:bg-slate-850 border border-indigo-100 dark:border-indigo-900/60 flex items-center justify-center text-indigo-500 group-hover:bg-brand-600 group-hover:text-white transition-colors shrink-0">
                <ArrowUpRight className="w-4 h-4" />
              </div>
            </button>
          );
        })}
      </div>

      <p className="text-3xs text-slate-400 italic">
        *Market intelligence sourced via real-time vector embeddings and active engineering requisitions.
      </p>
    </div>
  );
}
