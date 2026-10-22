import React, { useState } from 'react';
import {
  Target,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  TrendingUp,
  Sparkles,
  BarChart2,
  PieChart as PieIcon,
  Table as TableIcon,
  RefreshCw,
  Award,
  Layers,
  ChevronRight,
  Flame,
  Info,
} from 'lucide-react';
import Card, { CardHeader, CardTitle, CardContent, CardFooter, CardDescription } from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import ScoreRing from '../ui/ScoreRing';
import Skeleton from '../ui/Skeleton';
import ErrorState from '../ui/ErrorState';
import EmptyState from '../ui/EmptyState';
import BreakdownGrid from '../score/BreakdownGrid';
import MissingSkillsBarChart from '../charts/MissingSkillsBarChart';
import SkillGapDonutChart from '../charts/SkillGapDonutChart';
import TrendingSkillsList from '../skills/TrendingSkillsList';
import SkillFiltersBar from '../skills/SkillFiltersBar';
import SkillDetailSidePanel from '../skills/SkillDetailSidePanel';
import AccessibleDataTable from '../score/AccessibleDataTable';
import { mockScoreResult } from '../../data/mockData';
import { mockRoleFixtures } from '../../data/mockScoreFixtures';
import { getAtsScoreTier, SCORE_TIERS } from '../../utils/scoreThresholds';

/**
 * AtsSkillGapScreen Component
 * Consumes the ScoreResult contract:
 * {
 *   ats_score: number,
 *   target_role: string,
 *   breakdown: { keyword_match, semantic_similarity, section_completeness, formatting, experience_relevance, quantified_impact },
 *   skill_gap: { matched, missing: [{skill, demand_pct}], weak, trending }
 * }
 */
export default function AtsSkillGapScreen({
  state = 'success',
  data = mockScoreResult,
  onRetry,
  initialRole = 'Data Scientist / ML Engineer',
}) {
  // Current active role & data state
  const [currentRole, setCurrentRole] = useState(data?.target_role || initialRole);
  const activeData =
    mockRoleFixtures[currentRole] && data === mockScoreResult
      ? mockRoleFixtures[currentRole]
      : data || mockScoreResult;

  // Filter & interaction states
  const [activeFilter, setActiveFilter] = useState('all'); // 'all' | 'missing' | 'weak' | 'trending' | 'matched'
  const [selectedSkill, setSelectedSkill] = useState(null);
  const [selectedSkillStatus, setSelectedSkillStatus] = useState('missing');
  const [viewMode, setViewMode] = useState('visual'); // 'visual' | 'table'
  const [isRetrying, setIsRetrying] = useState(false);

  // Loading Skeleton State
  if (state === 'loading') {
    return (
      <div
        data-testid="ats-loading-skeleton"
        className="space-y-6 w-full max-w-full overflow-x-hidden"
      >
        {/* Top Header Skeleton */}
        <div className="flex flex-col sm:flex-row justify-between gap-4 p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
          <div className="space-y-2">
            <Skeleton variant="text" width="240px" height="28px" />
            <Skeleton variant="text" width="340px" height="16px" />
          </div>
          <div className="flex gap-2">
            <Skeleton variant="rectangular" width="100px" height="32px" />
            <Skeleton variant="rectangular" width="120px" height="32px" />
          </div>
        </div>

        {/* Overview Row Skeleton: Score Ring & 6 Breakdown Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex flex-col items-center justify-center space-y-4">
            <Skeleton variant="circular" width="150px" height="150px" />
            <Skeleton variant="text" width="160px" height="20px" />
            <Skeleton variant="text" width="220px" height="14px" />
          </div>
          <div className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <div
                key={i}
                className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-3"
              >
                <Skeleton variant="text" width="70%" height="16px" />
                <Skeleton variant="text" width="40%" height="24px" />
                <Skeleton variant="rectangular" width="100%" height="8px" />
              </div>
            ))}
          </div>
        </div>

        {/* Charts Grid Skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-4">
            <Skeleton variant="text" width="50%" height="20px" />
            <Skeleton variant="rectangular" width="100%" height="220px" />
          </div>
          <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-4">
            <Skeleton variant="text" width="50%" height="20px" />
            <Skeleton variant="rectangular" width="100%" height="220px" />
          </div>
        </div>
      </div>
    );
  }

  // Error State with Retry
  if (state === 'error') {
    const handleRetryClick = () => {
      setIsRetrying(true);
      setTimeout(() => {
        setIsRetrying(false);
        if (onRetry) onRetry();
      }, 750);
    };

    return (
      <div data-testid="ats-error-state" className="py-8">
        <ErrorState
          error={{
            code: 'ML_SCORING_SERVICE_TIMEOUT',
            message:
              'Failed to retrieve ATS score evaluation and live job-market demand vectors. ChromaDB semantic index or job scraper connection was interrupted.',
          }}
          onRetry={handleRetryClick}
          actionLabel={isRetrying ? 'Retrying scoring analysis...' : 'Retry ATS Analysis'}
        />
      </div>
    );
  }

  // Check empty state
  const rawMissing = activeData?.skill_gap?.missing || [];
  const rawMatched = activeData?.skill_gap?.matched || [];
  const rawWeak = activeData?.skill_gap?.weak || [];
  const rawTrending = activeData?.skill_gap?.trending || [];
  const isZeroGaps = rawMissing.length === 0 && rawWeak.length === 0;

  if (state === 'empty' || isZeroGaps) {
    return (
      <div data-testid="ats-empty-state" className="space-y-6">
        <EmptyState
          icon={Award}
          title="No Skill Gaps Found — 100% Fit!"
          description={`Your resume matches all core competencies and high-demand skills tracked for "${currentRole}". Your ATS pass probability is in the top percentile.`}
          action={{
            label: 'Benchmark Another Target Role',
            onClick: () => {
              const roles = Object.keys(mockRoleFixtures);
              const nextRole = roles.find((r) => r !== currentRole) || roles[0];
              setCurrentRole(nextRole);
            },
          }}
        />
        {/* Quick option to switch roles directly */}
        <div className="flex justify-center">
          <SkillFiltersBar
            selectedRole={currentRole}
            onRoleChange={setCurrentRole}
            activeFilter={activeFilter}
            onFilterChange={setActiveFilter}
            counts={{
              missing: 0,
              weak: 0,
              trending: rawTrending.length,
              matched: rawMatched.length,
            }}
          />
        </div>
      </div>
    );
  }

  // Derived metrics
  const atsScore = Number(activeData?.ats_score) || 0;
  const tierInfo = getAtsScoreTier(atsScore);
  const breakdown = activeData?.breakdown || {
    keyword_match: 0,
    semantic_similarity: 0,
    section_completeness: 0,
    formatting: 0,
    experience_relevance: 0,
    quantified_impact: 0,
  };

  const handleOpenSkill = (skill, status = 'missing') => {
    setSelectedSkill(skill);
    setSelectedSkillStatus(status);
  };

  const counts = {
    missing: rawMissing.length,
    weak: rawWeak.length,
    trending: rawTrending.length,
    matched: rawMatched.length,
  };

  return (
    <div
      data-testid="ats-skill-gap-screen"
      className="space-y-6 w-full max-w-full overflow-x-hidden text-slate-900 dark:text-slate-100"
    >
      {/* 1. Header with Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <Badge variant="primary" size="sm">
              FR-003
            </Badge>
            <span className="text-2xs font-mono text-slate-500">
              Live ATS Benchmark: {currentRole}
            </span>
          </div>
          <h1 className="text-xl sm:text-2xl lg:text-3xl font-extrabold tracking-tight">
            ATS Score Cards & Skill-Gap Analysis
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1 max-w-2xl">
            Calculated across 6 recruiter-weighted dimensions and benchmarked against 25,000+ live
            engineering job descriptions.
          </p>
        </div>

        {/* View Toggle: Visual Charts vs Accessible Table */}
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <div
            role="group"
            aria-label="View representation mode"
            className="inline-flex rounded-lg p-1 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700"
          >
            <button
              type="button"
              aria-pressed={viewMode === 'visual'}
              onClick={() => setViewMode('visual')}
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold rounded-md transition-colors ${
                viewMode === 'visual'
                  ? 'bg-white dark:bg-slate-700 text-brand-600 dark:text-brand-300 shadow-xs'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
              }`}
            >
              <BarChart2 className="w-3.5 h-3.5" />
              <span>Visual Dashboard</span>
            </button>
            <button
              type="button"
              aria-pressed={viewMode === 'table'}
              onClick={() => setViewMode('table')}
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold rounded-md transition-colors ${
                viewMode === 'table'
                  ? 'bg-white dark:bg-slate-700 text-brand-600 dark:text-brand-300 shadow-xs'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
              }`}
            >
              <TableIcon className="w-3.5 h-3.5" />
              <span>Accessible Table</span>
            </button>
          </div>
        </div>
      </div>

      {/* 2. Target Role & Filter Bar */}
      <SkillFiltersBar
        selectedRole={currentRole}
        onRoleChange={setCurrentRole}
        activeFilter={activeFilter}
        onFilterChange={setActiveFilter}
        counts={counts}
      />

      {/* 3. Accessible Table View Mode */}
      {viewMode === 'table' ? (
        <AccessibleDataTable scoreResult={activeData} />
      ) : (
        /* 4. Visual Dashboard View Mode */
        <div className="space-y-6">
          {/* Top Row: Overall Score Ring (1/3) + 6 Breakdown Cards Grid (2/3) */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-stretch">
            {/* Overall Score Ring Card */}
            <Card
              variant="elevated"
              className="flex flex-col items-center justify-center p-6 text-center border-slate-200/90 dark:border-slate-800"
            >
              <ScoreRing
                score={atsScore}
                size={160}
                strokeWidth={14}
                label="Overall ATS Fit Score"
                sublabel={`Weighted recruiter fit for ${currentRole}`}
                showThresholdBadge={true}
                showTierLegend={true}
              />
              <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 text-2xs text-slate-500 max-w-xs">
                {tierInfo.description}
              </div>
            </Card>

            {/* 6-Factor Breakdown Cards Grid */}
            <div className="lg:col-span-2">
              <Card variant="default" className="h-full">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm sm:text-base flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-brand-500" />
                      6-Dimension Recruiter Scoring Breakdown
                    </CardTitle>
                    <span className="text-2xs font-mono text-slate-400">100% Sum Weight</span>
                  </div>
                  <CardDescription>
                    Each dimension evaluated via NLP entity extraction and ChromaDB semantic
                    similarity.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <BreakdownGrid breakdown={breakdown} />
                </CardContent>
              </Card>
            </div>
          </div>

          {/* Middle Row: Skill Gap Charts (Missing Bar Chart & Summary Donut) */}
          {(activeFilter === 'all' || activeFilter === 'missing') && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* Missing Skills Horizontal Bar Chart (2 columns on lg) */}
              <Card variant="default" className="lg:col-span-2 min-w-0">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm sm:text-base flex items-center gap-2 text-rose-600 dark:text-rose-400">
                      <XCircle className="w-4 h-4 text-rose-500" />
                      Missing Skills Ranked by Market Demand
                    </CardTitle>
                    <Badge variant="danger" size="sm">
                      {rawMissing.length} Critical Gaps
                    </Badge>
                  </div>
                  <CardDescription>
                    High-demand technologies frequently appearing in target job postings but missing
                    from your resume.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <MissingSkillsBarChart
                    missing={rawMissing}
                    onSelectSkill={(skill) => handleOpenSkill(skill, 'missing')}
                  />
                </CardContent>
              </Card>

              {/* Matched vs Missing vs Weak Donut Summary (1 column on lg) */}
              <Card variant="default" className="min-w-0">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm sm:text-base flex items-center gap-2">
                      <PieIcon className="w-4 h-4 text-brand-500" />
                      Competency Distribution
                    </CardTitle>
                    <span className="text-2xs font-mono text-slate-400">
                      {counts.matched + counts.missing + counts.weak} Skills
                    </span>
                  </div>
                  <CardDescription>
                    Summary ratio of verified matches versus actionable gaps.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <SkillGapDonutChart
                    matched={rawMatched}
                    missing={rawMissing}
                    weak={rawWeak}
                    onSelectCategory={(cat) => setActiveFilter(cat)}
                  />
                </CardContent>
              </Card>
            </div>
          )}

          {/* Conditional Sections based on Active Filter: Weak Evidence */}
          {(activeFilter === 'all' || activeFilter === 'weak') && rawWeak.length > 0 && (
            <Card variant="default">
              <CardHeader className="bg-amber-50/40 dark:bg-amber-950/20 border-b border-amber-100/60 dark:border-amber-900/40">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm sm:text-base text-amber-800 dark:text-amber-300 flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-500" />
                    Weak or Under-Quantified Evidence ({rawWeak.length})
                  </CardTitle>
                  <Badge variant="warning" size="sm">
                    Action Required
                  </Badge>
                </div>
                <CardDescription>
                  These skills or sections are mentioned passively without concrete metrics or
                  standard action verbs.
                </CardDescription>
              </CardHeader>
              <CardContent className="p-4 sm:p-6">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {rawWeak.map((w, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => handleOpenSkill(w, 'weak')}
                      className="p-3.5 rounded-xl bg-amber-50/50 dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-900/40 text-left hover:bg-amber-100/60 transition-colors group flex items-start justify-between gap-3 focus:outline-none focus:ring-2 focus:ring-amber-500"
                    >
                      <div className="space-y-1">
                        <span className="text-xs font-bold text-slate-900 dark:text-slate-100 group-hover:text-amber-700 dark:group-hover:text-amber-300 block">
                          {w}
                        </span>
                        <p className="text-2xs text-slate-500">
                          Click to view Google XYZ format bullet point rewrite recommendation.
                        </p>
                      </div>
                      <ChevronRight className="w-4 h-4 text-amber-500 shrink-0 group-hover:translate-x-0.5 transition-transform" />
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Conditional Sections based on Active Filter: Matched Skills */}
          {(activeFilter === 'all' || activeFilter === 'matched') && rawMatched.length > 0 && (
            <Card variant="default">
              <CardHeader className="bg-emerald-50/40 dark:bg-emerald-950/20 border-b border-emerald-100/60 dark:border-emerald-900/40">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm sm:text-base text-emerald-800 dark:text-emerald-300 flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                    Verified Matched Core Competencies ({rawMatched.length})
                  </CardTitle>
                  <Badge variant="success" size="sm">
                    Screening Pass
                  </Badge>
                </div>
                <CardDescription>
                  Keywords and semantic clusters successfully extracted and validated against the
                  target benchmark.
                </CardDescription>
              </CardHeader>
              <CardContent className="p-4 sm:p-6">
                <div className="flex flex-wrap gap-2">
                  {rawMatched.map((skill, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => handleOpenSkill(skill, 'matched')}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-200 hover:bg-emerald-100/80 transition-colors focus:outline-none focus:ring-2 focus:ring-emerald-500 cursor-pointer"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                      <span>{skill}</span>
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Conditional Sections based on Active Filter: Trending Industry Signals */}
          {(activeFilter === 'all' || activeFilter === 'trending') && (
            <Card variant="default">
              <CardHeader className="bg-indigo-50/40 dark:bg-indigo-950/20 border-b border-indigo-100/60 dark:border-indigo-900/40">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm sm:text-base text-indigo-800 dark:text-indigo-300 flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-indigo-500" />
                    Trending 2026 Industry Signals & High-Velocity Skills
                  </CardTitle>
                  <Badge variant="primary" size="sm">
                    {rawTrending.length} Emerging Signals
                  </Badge>
                </div>
                <CardDescription>
                  Emerging skills experiencing explosive growth in 2026 job scrapers for {currentRole}.
                </CardDescription>
              </CardHeader>
              <CardContent className="p-4 sm:p-6">
                <TrendingSkillsList
                  trending={rawTrending}
                  onSelectSkill={(skill) => handleOpenSkill(skill, 'trending')}
                />
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* 5. Interactive Skill Detail Side Panel Drawer */}
      <SkillDetailSidePanel
        isOpen={Boolean(selectedSkill)}
        skillName={selectedSkill}
        status={selectedSkillStatus}
        onClose={() => setSelectedSkill(null)}
      />
    </div>
  );
}
