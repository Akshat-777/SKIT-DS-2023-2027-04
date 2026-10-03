import React from 'react';
import { IndianRupee, TrendingUp, Award, CheckCircle2, ArrowUpRight, Brain, AlertCircle } from 'lucide-react';
import Card, { CardHeader, CardTitle, CardContent, CardFooter } from '../ui/Card';
import Badge from '../ui/Badge';
import ScoreRing from '../ui/ScoreRing';
import Skeleton from '../ui/Skeleton';
import ErrorState from '../ui/ErrorState';
import EmptyState from '../ui/EmptyState';
import { mockMarketFit } from '../../data/mockData';

export default function MarketFitSalaryScreen({ state = 'success', data = mockMarketFit }) {
  if (state === 'empty') {
    return (
      <EmptyState
        icon={IndianRupee}
        title="No Market Fit Prediction"
        description="Run the resume evaluation to generate LightGBM salary predictions and competitive market benchmarks."
        action={{ label: "Evaluate Market Fit", onClick: () => {} }}
      />
    );
  }

  if (state === 'loading') {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Skeleton variant="card" />
          <Skeleton variant="card" />
        </div>
        <Skeleton variant="card" />
      </div>
    );
  }

  if (state === 'error') {
    return (
      <ErrorState
        error={{
          code: 'MODEL_INFERENCE_ERROR',
          message: 'LightGBM model inference failed due to missing required feature vectors (experience_months, primary_tech_stack). Re-extracting features.'
        }}
        onRetry={() => {}}
        actionLabel="Retry Model Inference"
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight flex items-center gap-2">
            Market-Fit & Salary Prediction
            <Badge variant="primary" size="sm">FR-004</Badge>
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            Machine Learning predictions powered by LightGBM + scikit-learn regressor trained on 45,000+ Indian tech roles.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="role" size="md">
            <Brain className="w-3.5 h-3.5 mr-1 inline" /> LightGBM Regressor
          </Badge>
        </div>
      </div>

      {/* Main KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Market Fit Score */}
        <Card variant="elevated" className="flex flex-col items-center justify-center p-6 text-center">
          <ScoreRing
            score={data.fit_score}
            size={150}
            strokeWidth={11}
            label="Live Market Fit Index"
            sublabel="Percentile vs 2026 Batch Graduates"
          />
        </Card>

        {/* Predicted Salary Range Card */}
        <Card variant="elevated" className="lg:col-span-2 p-6 flex flex-col justify-between bg-gradient-to-br from-white via-teal-50/20 to-teal-100/30 dark:from-slate-850 dark:via-slate-850 dark:to-teal-950/20 border-teal-200/60 dark:border-teal-900/40">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-teal-700 dark:text-teal-400 flex items-center gap-1.5">
                <IndianRupee className="w-4 h-4" />
                Predicted CTC Band ({data.currency})
              </span>
              <Badge variant="success" size="sm" dot>Trained LightGBM</Badge>
            </div>

            <div className="flex items-baseline gap-2 mt-2">
              <span className="text-4xl sm:text-5xl font-extrabold font-mono text-slate-900 dark:text-slate-100 tracking-tight">
                {data.salary_min} – {data.salary_max}
              </span>
              <span className="text-xl sm:text-2xl font-bold text-teal-600 dark:text-teal-400">
                {data.unit}
              </span>
            </div>

            <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">
              Based on candidate education (SKIT Jaipur CSE DS), internship at Cognitive AI Labs, and verified skills.
            </p>
          </div>

          <div className="mt-6 pt-4 border-t border-teal-200/60 dark:border-teal-900/40 flex flex-wrap items-center justify-between gap-3 text-xs">
            <span className="text-slate-600 dark:text-slate-300 font-medium">
              Upper Bound Potential with MLOps Certification:
            </span>
            <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
              <ArrowUpRight className="w-4 h-4" />
              17.7 LPA (+25%)
            </span>
          </div>
        </Card>
      </div>

      {/* Top Value Drivers / ML Feature Importance */}
      <Card variant="default">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Award className="w-4 h-4 text-brand-500" />
            Top Contributing Factors (SHAP Feature Importance)
          </CardTitle>
          <p className="text-2xs text-slate-500">
            Explainable AI drivers identified by ML scoring service
          </p>
        </CardHeader>
        <CardContent className="space-y-3">
          {data.top_factors.map((factor, idx) => (
            <div
              key={idx}
              className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 flex items-start gap-3"
            >
              <div className="w-6 h-6 rounded-full bg-brand-100 text-brand-700 dark:bg-brand-950 dark:text-brand-300 flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">
                {idx + 1}
              </div>
              <p className="text-xs sm:text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-medium">
                {factor}
              </p>
            </div>
          ))}
        </CardContent>
        <CardFooter className="flex items-center justify-between">
          <span className="text-2xs text-slate-400">Model: LightGBM Regressor v1.2</span>
          <span className="text-2xs font-mono text-emerald-600 dark:text-emerald-400 font-semibold">
            R² Score: 0.892 | RMSE: 1.15 LPA
          </span>
        </CardFooter>
      </Card>
    </div>
  );
}
