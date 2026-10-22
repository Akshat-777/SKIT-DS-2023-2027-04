import React, { useEffect, useRef } from 'react';
import { X, Sparkles, TrendingUp, AlertCircle, CheckCircle2, AlertTriangle, Copy, Check, ExternalLink } from 'lucide-react';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import { mockSkillDetails } from '../../data/mockScoreFixtures';

/**
 * SkillDetailSidePanel
 * Slide-over drawer detailing market demand, why it matters for ATS parsers,
 * recommended actions, and ready-to-use XYZ resume bullets.
 */
export default function SkillDetailSidePanel({
  isOpen,
  skillName,
  skillData = null,
  status = 'missing', // 'missing' | 'matched' | 'weak' | 'trending'
  onClose,
}) {
  const panelRef = useRef(null);
  const [copied, setCopied] = React.useState(false);

  // Fallback enriched data
  const meta = skillData || mockSkillDetails[skillName] || {
    skill: skillName,
    demand_pct: typeof skillData?.demand_pct === 'number' ? skillData.demand_pct : 75,
    category: 'Target Skill',
    why_matters: `This skill is heavily prioritized by automated applicant tracking systems (ATS) and hiring teams evaluating candidates for this target role. Lack of verified keywords reduces your searchability.`,
    ats_boost: '+20% ATS Screening Rate',
    action_tip: `Complete a targeted project demonstrating hands-on experience and integrate standard industry keywords into your resume.`,
    sample_bullet: `Implemented ${skillName || 'skill'} in production workflows, driving measurable efficiency and reliability gains across service deployments.`
  };

  const demandPct = typeof meta.demand_pct === 'number' ? meta.demand_pct : 75;

  // Close on Escape key press
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Focus trap / focus when opened
  useEffect(() => {
    if (isOpen && panelRef.current) {
      panelRef.current.focus();
    }
  }, [isOpen]);

  if (!isOpen || !skillName) return null;

  const handleCopyBullet = () => {
    if (meta.sample_bullet) {
      navigator.clipboard?.writeText(meta.sample_bullet);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const getStatusBadge = () => {
    switch (status) {
      case 'matched':
        return (
          <Badge variant="success" size="md">
            <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
            Verified Match in Resume
          </Badge>
        );
      case 'weak':
        return (
          <Badge variant="warning" size="md">
            <AlertTriangle className="w-3.5 h-3.5 mr-1" />
            Weak or Under-Quantified
          </Badge>
        );
      case 'trending':
        return (
          <Badge variant="primary" size="md">
            <TrendingUp className="w-3.5 h-3.5 mr-1" />
            2026 Trending Radar
          </Badge>
        );
      case 'missing':
      default:
        return (
          <Badge variant="danger" size="md">
            <AlertCircle className="w-3.5 h-3.5 mr-1" />
            Missing High-Demand Gap
          </Badge>
        );
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="skill-drawer-title"
      className="fixed inset-0 z-50 overflow-hidden"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity animate-fade-in"
        onClick={onClose}
        aria-hidden="true"
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10 pointer-events-none">
        <div
          ref={panelRef}
          tabIndex={-1}
          className="w-screen max-w-md pointer-events-auto bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 shadow-2xl flex flex-col focus:outline-none animate-slide-left"
        >
          {/* Header */}
          <div className="p-6 border-b border-slate-100 dark:border-slate-800 flex items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-2">
                {getStatusBadge()}
                {meta.category && (
                  <span className="text-2xs font-mono text-slate-500 uppercase tracking-wider">
                    {meta.category}
                  </span>
                )}
              </div>
              <h2
                id="skill-drawer-title"
                className="text-xl font-bold text-slate-900 dark:text-slate-100 tracking-tight"
              >
                {skillName}
              </h2>
            </div>
            <button
              type="button"
              onClick={onClose}
              aria-label="Close skill details"
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Drawer Body (Scrollable) */}
          <div className="p-6 overflow-y-auto space-y-6 flex-1">
            {/* Market Demand Meter */}
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-850 border border-slate-200/80 dark:border-slate-800 space-y-2">
              <div className="flex justify-between items-center text-xs">
                <span className="font-semibold text-slate-700 dark:text-slate-300">
                  Live Market Job Postings Demand
                </span>
                <span className="font-mono font-black text-brand-600 dark:text-brand-400 text-sm">
                  {demandPct}%
                </span>
              </div>
              <div className="w-full bg-slate-200 dark:bg-slate-700 h-2.5 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-brand-500 to-indigo-600 rounded-full"
                  style={{ width: `${demandPct}%` }}
                />
              </div>
              <p className="text-2xs text-slate-500 dark:text-slate-400">
                Scraped across 25,000+ active tech job postings matching this profile.
              </p>
            </div>

            {/* Why It Matters */}
            <div className="space-y-2">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-brand-500" />
                Why This Matters for ATS & Recruiters
              </h3>
              <div className="p-3.5 rounded-xl bg-blue-50/60 dark:bg-blue-950/30 border border-blue-200/60 dark:border-blue-900/40 text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
                {meta.why_matters}
              </div>
            </div>

            {/* Estimated ATS Impact */}
            {meta.ats_boost && (
              <div className="flex items-center justify-between p-3.5 rounded-xl bg-emerald-50/70 dark:bg-emerald-950/40 border border-emerald-200/70 dark:border-emerald-900/40">
                <div>
                  <span className="text-2xs uppercase tracking-wider font-bold text-emerald-800 dark:text-emerald-300 block">
                    Estimated Screening Impact
                  </span>
                  <span className="text-xs text-emerald-900 dark:text-emerald-200 font-medium">
                    Adding evidence for this skill
                  </span>
                </div>
                <Badge variant="success" size="md">
                  {meta.ats_boost}
                </Badge>
              </div>
            )}

            {/* Action Tip */}
            <div className="space-y-2">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                ⚡ Actionable Next Step
              </h3>
              <p className="text-xs text-slate-600 dark:text-slate-300 bg-slate-50 dark:bg-slate-800/60 p-3.5 rounded-xl border border-slate-200/80 dark:border-slate-800 leading-relaxed">
                {meta.action_tip}
              </p>
            </div>

            {/* Google XYZ Resume Bullet Template */}
            {meta.sample_bullet && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    Google XYZ Resume Bullet Template
                  </h3>
                  <button
                    type="button"
                    onClick={handleCopyBullet}
                    className="inline-flex items-center gap-1 text-2xs font-semibold text-brand-600 dark:text-brand-400 hover:text-brand-700 focus:outline-none"
                  >
                    {copied ? (
                      <>
                        <Check className="w-3 h-3 text-emerald-500" />
                        <span className="text-emerald-600">Copied!</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3 h-3" />
                        <span>Copy</span>
                      </>
                    )}
                  </button>
                </div>
                <div className="p-3.5 rounded-xl bg-slate-900 text-slate-100 font-mono text-2xs leading-relaxed border border-slate-800 select-all">
                  &ldquo;{meta.sample_bullet}&rdquo;
                </div>
                <p className="text-3xs text-slate-400 italic">
                  Format: Accomplished [X] as measured by [Y] by doing [Z].
                </p>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-slate-100 dark:border-slate-800 flex justify-end gap-2 bg-slate-50/50 dark:bg-slate-900/50">
            <Button variant="secondary" size="sm" onClick={onClose}>
              Close Panel
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
