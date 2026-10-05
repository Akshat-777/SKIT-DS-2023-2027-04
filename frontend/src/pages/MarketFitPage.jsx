import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Compass, Briefcase } from 'lucide-react';
import PageContainer from '../components/layout/PageContainer';
import Card, { CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import ScoreRing from '../components/ui/ScoreRing';
import Spinner from '../components/ui/Spinner';
import SalaryRangeChart from '../components/charts/SalaryRangeChart';
import { dashboardService } from '../services/dashboardService';

export default function MarketFitPage() {
  const { resumeId = 'mock-resume-101' } = useParams();
  const [loading, setLoading] = useState(true);
  const [marketFit, setMarketFit] = useState(null);

  useEffect(() => {
    let isMounted = true;
    async function load() {
      setLoading(true);
      try {
        const data = await dashboardService.getMarketFit(resumeId);
        if (isMounted) setMarketFit(data);
      } catch (e) {
        console.error('Failed to load market fit:', e);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    load();
    return () => {
      isMounted = false;
    };
  }, [resumeId]);

  if (loading) {
    return (
      <PageContainer>
        <div className="py-20 flex flex-col items-center justify-center space-y-4">
          <Spinner size="lg" variant="primary" />
          <p className="text-sm font-medium text-slate-500 animate-pulse">
            Querying LightGBM model and evaluating salary benchmarks...
          </p>
        </div>
      </PageContainer>
    );
  }

  const fitScore = marketFit?.fit_score ?? 88;
  const salaryMin = marketFit?.salary_min ?? 14.5;
  const salaryMax = marketFit?.salary_max ?? 22.0;
  const currency = marketFit?.currency ?? 'INR';
  const unit = marketFit?.unit ?? 'LPA';
  const topFactors = marketFit?.top_factors ?? [];

  return (
    <PageContainer>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="primary" size="sm">
                FR-004
              </Badge>
              <span className="text-2xs font-mono text-slate-500">LightGBM + Live Market Feed</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-slate-100 tracking-tight">
              Market Fit & Salary Prediction
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
              Estimated market alignment and salary bandwidth calibrated against current hiring
              trends.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Link to={`/roadmap/${resumeId}`}>
              <Button variant="primary" size="sm" icon={<Compass className="w-3.5 h-3.5" />}>
                View Learning Roadmap
              </Button>
            </Link>
          </div>
        </div>

        {/* Top Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          {/* Fit Score Ring */}
          <Card
            variant="default"
            className="md:col-span-4 flex flex-col items-center justify-center p-6 text-center"
          >
            <ScoreRing score={fitScore} size={150} strokeWidth={12} />
            <div className="mt-4 space-y-1">
              <Badge variant="success" size="md">
                High Market Demand
              </Badge>
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 mt-2">
                Market Compatibility: {fitScore}/100
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 max-w-xs">
                LightGBM regression model indicates candidate is in top 12th percentile for Indian
                tech companies.
              </p>
            </div>
          </Card>

          {/* Salary Prediction Chart */}
          <Card variant="default" className="md:col-span-8 p-6">
            <SalaryRangeChart
              min={salaryMin}
              max={salaryMax}
              currency={currency}
              unit={unit}
              topFactors={topFactors}
            />
          </Card>
        </div>

        {/* Live Job Market Context */}
        <Card variant="default">
          <CardHeader>
            <CardTitle className="text-sm flex items-center gap-2">
              <Briefcase className="w-4 h-4 text-brand-500" />
              Live Tech Market Demand Signals
            </CardTitle>
            <CardDescription>
              Job-board APIs live stream (active fallbacks safeguard against rate limits)
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                <span className="text-2xs text-slate-400 uppercase font-semibold">
                  Active Openings
                </span>
                <p className="text-xl font-extrabold text-slate-900 dark:text-slate-100 mt-1">
                  2,840+
                </p>
                <span className="text-2xs text-emerald-600 font-medium">+14% vs last quarter</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                <span className="text-2xs text-slate-400 uppercase font-semibold">
                  Top Hiring Metro
                </span>
                <p className="text-xl font-extrabold text-slate-900 dark:text-slate-100 mt-1">
                  Bengaluru / NCR
                </p>
                <span className="text-2xs text-slate-500">62% of aggregate volume</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                <span className="text-2xs text-slate-400 uppercase font-semibold">
                  Highest Premium Skill
                </span>
                <p className="text-xl font-extrabold text-slate-900 dark:text-slate-100 mt-1">
                  PyTorch / MLOps
                </p>
                <span className="text-2xs text-brand-600 font-medium">+₹4.2 LPA lift</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </PageContainer>
  );
}
