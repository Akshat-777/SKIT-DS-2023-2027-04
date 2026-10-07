import React from 'react';
import { Target, CheckCircle2, XCircle, AlertTriangle, TrendingUp, Sparkles, Database, BarChart2 } from 'lucide-react';
import Card, { CardHeader, CardTitle, CardContent, CardFooter } from '../ui/Card';
import Badge from '../ui/Badge';
import ScoreRing from '../ui/ScoreRing';
import ProgressBar from '../ui/ProgressBar';
import Skeleton from '../ui/Skeleton';
import ErrorState from '../ui/ErrorState';
import EmptyState from '../ui/EmptyState';
import { mockScoreResult } from '../../data/mockData';

export default function AtsSkillGapScreen({ state = 'success', data = mockScoreResult }) {
  if (state === 'empty') {
    return (
      <EmptyState
        icon={Target}
        title="No ATS Score Generated"
        description="Please parse a resume first to evaluate ATS compatibility and live job market gaps."
        action={{ label: "Upload Resume", onClick: () => {} }}
      />
    );
  }

  if (state === 'loading') {
    return (
      <div className="space-y-6">
        <div className="p-8 rounded-2xl bg-white dark:bg-slate-850 border border-slate-200 dark:border-slate-800 flex flex-col items-center justify-center space-y-4">
          <Skeleton variant="circular" width="140px" height="140px" />
          <Skeleton variant="text" width="220px" height="20px" />
          <Skeleton variant="text" width="340px" height="14px" />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <Skeleton variant="card" count={3} />
        </div>
      </div>
    );
  }

  if (state === 'error') {
    return (
      <ErrorState
        error={{
          code: 'JOB_BOARD_API_TIMEOUT',
          message: 'Upstream job-board API rate limit reached. Re-routing request to local ChromaDB cached market demand index.'
        }}
        onRetry={() => {}}
        actionLabel="Switch to Cached Index"
      />
    );
  }

  const breakdownMetrics = [
    { label: 'Keyword Match', value: data.breakdown.keyword_match, weight: '20%' },
    { label: 'Semantic Similarity (ChromaDB)', value: data.breakdown.semantic_similarity, weight: '25%' },
    { label: 'Section Completeness', value: data.breakdown.section_completeness, weight: '15%' },
    { label: 'ATS Formatting & Cleanliness', value: data.breakdown.formatting, weight: '10%' },
    { label: 'Experience Relevance', value: data.breakdown.experience_relevance, weight: '15%' },
    { label: 'Quantified Impact (Metrics)', value: data.breakdown.quantified_impact, weight: '15%' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight flex items-center gap-2">
            ATS Score & Live Skill-Gap Analysis
            <Badge variant="primary" size="sm">FR-003</Badge>
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            Benchmarked against <span className="font-semibold text-brand-600 dark:text-brand-400">{data.target_role}</span> using live job-board intelligence.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="success" size="sm" dot>Live Feed Active</Badge>
          <Badge variant="outline" size="sm">ChromaDB Indexed</Badge>
        </div>
      </div>

      {/* Top Overview Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recruiter-Grade ATS Score Ring */}
        <Card variant="elevated" className="flex flex-col items-center justify-center p-6 text-center">
          <ScoreRing
            score={data.ats_score}
            size={160}
            strokeWidth={12}
            label="Overall ATS Fit Score"
            sublabel="Based on 6 Weighted Recruiter Factors"
          />
          <div className="mt-5 w-full pt-4 border-t border-slate-100 dark:border-slate-800 flex justify-around text-2xs">
            <div>
              <span className="text-slate-400 block font-mono">RED ZONE</span>
              <span className="font-bold text-rose-500">&lt; 50</span>
            </div>
            <div>
              <span className="text-slate-400 block font-mono">AMBER ZONE</span>
              <span className="font-bold text-amber-500">50 - 74</span>
            </div>
            <div>
              <span className="text-slate-400 block font-mono">GREEN ZONE</span>
              <span className="font-bold text-emerald-500">75 - 100</span>
            </div>
          </div>
        </Card>

        {/* 6-Factor Weighted Breakdown */}
        <Card variant="default" className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart2 className="w-4 h-4 text-brand-500" />
              Recruiter-Grade Score Breakdown
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3.5">
            {breakdownMetrics.map((item, idx) => (
              <div key={idx} className="space-y-1">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-medium text-slate-700 dark:text-slate-300">
                    {item.label} <span className="text-2xs text-slate-400 font-mono">({item.weight})</span>
                  </span>
                  <span className="font-mono font-bold text-slate-900 dark:text-slate-100">
                    {item.value}%
                  </span>
                </div>
                <ProgressBar value={item.value} size="sm" variant="ats" />
              </div>
            ))}
          </CardContent>
          <CardFooter>
            <span className="text-2xs text-slate-500">
              *Scored by ML scoring service & ChromaDB vector similarity index.
            </span>
          </CardFooter>
        </Card>
      </div>

      {/* 4-Quadrant Skill Gap Analysis */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Matched Skills */}
        <Card variant="default">
          <CardHeader className="bg-emerald-50/50 dark:bg-emerald-950/20 border-b border-emerald-100 dark:border-emerald-900/40">
            <CardTitle className="text-emerald-700 dark:text-emerald-300 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              Matched Core Competencies ({data.skill_gap.matched.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4">
            <div className="flex flex-wrap gap-2">
              {data.skill_gap.matched.map((skill, idx) => (
                <Badge key={idx} variant="success" size="md">
                  ✓ {skill}
                </Badge>
              ))}
            </div>
            <p className="text-2xs text-slate-500 mt-4">
              These skills match top keywords from active job postings in the target role.
            </p>
          </CardContent>
        </Card>

        {/* Missing Skills with Live Market Demand % */}
        <Card variant="default">
          <CardHeader className="bg-rose-50/50 dark:bg-rose-950/20 border-b border-rose-100 dark:border-rose-900/40">
            <CardTitle className="text-rose-700 dark:text-rose-300 flex items-center gap-2">
              <XCircle className="w-4 h-4 text-rose-500" />
              Missing High-Demand Skills ({data.skill_gap.missing.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4 space-y-3">
            {data.skill_gap.missing.map((item, idx) => (
              <div key={idx} className="flex items-center justify-between p-2.5 rounded-lg bg-rose-50/40 dark:bg-rose-950/30 border border-rose-200/60 dark:border-rose-900/60">
                <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
                  {item.skill}
                </span>
                <div className="flex items-center gap-2">
                  <span className="text-2xs text-slate-500 font-medium">Market Demand:</span>
                  <Badge variant="danger" size="sm">
                    {item.demand_pct}%
                  </Badge>
                </div>
              </div>
            ))}
            <p className="text-2xs text-rose-600 dark:text-rose-400 font-medium">
              Priority gap: Adding MLOps will increase ATS pass rates by +28%.
            </p>
          </CardContent>
        </Card>

        {/* Weak or Unquantified Areas */}
        <Card variant="default">
          <CardHeader className="bg-amber-50/50 dark:bg-amber-950/20 border-b border-amber-100 dark:border-amber-900/40">
            <CardTitle className="text-amber-800 dark:text-amber-300 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-500" />
              Weak or Under-Quantified Evidence
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4 space-y-2">
            {data.skill_gap.weak.map((w, idx) => (
              <div key={idx} className="flex items-start gap-2 text-xs text-slate-700 dark:text-slate-300">
                <span className="text-amber-500 font-bold">•</span>
                <span>{w}</span>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Trending Market Signals */}
        <Card variant="default">
          <CardHeader className="bg-indigo-50/50 dark:bg-indigo-950/20 border-b border-indigo-100 dark:border-indigo-900/40">
            <CardTitle className="text-indigo-700 dark:text-indigo-300 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-indigo-500" />
              Trending 2026 Industry Signals
            </CardTitle>
          </CardHeader>
          <CardContent className="p-4">
            <div className="flex flex-wrap gap-2">
              {data.skill_gap.trending.map((trend, idx) => (
                <Badge key={idx} variant="primary" size="md">
                  🔥 {trend}
                </Badge>
              ))}
            </div>
            <p className="text-2xs text-slate-500 mt-4">
              Emerging demand signals detected via live job scrapers and LinkedIn market feeds.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
