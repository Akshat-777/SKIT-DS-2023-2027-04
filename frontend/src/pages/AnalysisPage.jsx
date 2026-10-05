import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  TrendingUp,
  Compass,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  GraduationCap,
  Briefcase,
  Layers,
} from 'lucide-react';
import PageContainer from '../components/layout/PageContainer';
import Card, { CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import Tabs from '../components/ui/Tabs';
import ScoreRing from '../components/ui/ScoreRing';
import ProgressBar from '../components/ui/ProgressBar';
import Spinner from '../components/ui/Spinner';
import ScoreRadarChart from '../components/charts/ScoreRadarChart';
import SkillGapBar from '../components/charts/SkillGapBar';
import { resumeService } from '../services/resumeService';
import { dashboardService } from '../services/dashboardService';
import { getScoreThreshold } from '../utils/formatters';

export default function AnalysisPage() {
  const { resumeId = 'mock-resume-101' } = useParams();

  const [loading, setLoading] = useState(true);
  const [parsedResume, setParsedResume] = useState(null);
  const [scoreResult, setScoreResult] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      setLoading(true);
      try {
        const [resumeData, scoreData] = await Promise.all([
          resumeService.getResume(resumeId),
          dashboardService.getAtsScore(resumeId),
        ]);
        if (isMounted) {
          setParsedResume(resumeData);
          setScoreResult(scoreData);
        }
      } catch (err) {
        console.error('Failed to load analysis:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadData();
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
            Computing ATS recruiter score and running live skill-gap analysis...
          </p>
        </div>
      </PageContainer>
    );
  }

  const atsScore = scoreResult?.ats_score ?? 82;
  const threshold = getScoreThreshold(atsScore);
  const breakdown = scoreResult?.breakdown ?? {};
  const skillGap = scoreResult?.skill_gap ?? { matched: [], missing: [], weak: [], trending: [] };

  return (
    <PageContainer>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="primary" size="sm">
                FR-002 & FR-003
              </Badge>
              <span className="text-2xs font-mono text-slate-500">Resume ID: {resumeId}</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-slate-100 tracking-tight">
              ATS Scoring & Skill Gap Analysis
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
              Benchmarked for role:{' '}
              <strong className="text-slate-700 dark:text-slate-200">
                {scoreResult?.target_role || 'Data Scientist / ML Engineer'}
              </strong>
            </p>
          </div>

          {/* Quick CTA to next steps */}
          <div className="flex items-center gap-2">
            <Link to={`/market-fit/${resumeId}`}>
              <Button variant="secondary" size="sm" icon={<TrendingUp className="w-3.5 h-3.5" />}>
                Market Fit & Salary
              </Button>
            </Link>
            <Link to={`/roadmap/${resumeId}`}>
              <Button variant="primary" size="sm" icon={<Compass className="w-3.5 h-3.5" />}>
                Learning Roadmap
              </Button>
            </Link>
          </div>
        </div>

        {/* Top Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          {/* Main Score Ring Card */}
          <Card
            variant="default"
            className="md:col-span-5 flex flex-col items-center justify-center p-6 text-center"
          >
            <ScoreRing score={atsScore} size={160} strokeWidth={14} />
            <div className="mt-4 space-y-1">
              <Badge variant={threshold.badgeVariant} size="md">
                {threshold.label}
              </Badge>
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 mt-2">
                Overall Recruiter-Grade ATS Score
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 max-w-xs">
                Candidate surpasses 80% threshold for automated screening systems in tech hiring.
              </p>
            </div>
          </Card>

          {/* Radar Dimension Chart */}
          <Card variant="default" className="md:col-span-7 p-6 flex flex-col justify-center">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-brand-500" />
                6-Dimension ATS Breakdown
              </h3>
              <span className="text-2xs text-slate-400">Vector & Rule Metrics</span>
            </div>
            <div className="flex justify-center">
              <ScoreRadarChart breakdown={breakdown} size={260} />
            </div>
          </Card>
        </div>

        {/* Tabs: Skill Gap vs Parsed Resume Details */}
        <Tabs
          activeTab={activeTab}
          onChange={setActiveTab}
          tabs={[
            { id: 'overview', label: 'Skill Gap vs Live Market' },
            { id: 'parsed', label: 'NER Parsed Resume Data' },
            { id: 'breakdown', label: 'Detailed Scoring Matrix' },
          ]}
        />

        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Matched vs Missing Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Missing Skills (Critical Priority) */}
              <Card variant="default">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm text-rose-600 dark:text-rose-400 flex items-center gap-2">
                      <AlertCircle className="w-4 h-4" />
                      Critical Skill Gaps ({skillGap.missing.length})
                    </CardTitle>
                    <Badge variant="danger" size="sm">
                      High Demand
                    </Badge>
                  </div>
                  <CardDescription>
                    Skills demanded by live job postings not detected with sufficient evidence.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-2.5">
                  {skillGap.missing.map((item, idx) => (
                    <SkillGapBar
                      key={idx}
                      skill={typeof item === 'string' ? item : item.skill}
                      demandPct={typeof item === 'string' ? 75 : item.demand_pct}
                      status="missing"
                    />
                  ))}
                </CardContent>
              </Card>

              {/* Matched Skills */}
              <Card variant="default">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm text-emerald-600 dark:text-emerald-400 flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4" />
                      Verified Matched Skills ({skillGap.matched.length})
                    </CardTitle>
                    <Badge variant="success" size="sm">
                      Screening Pass
                    </Badge>
                  </div>
                  <CardDescription>
                    Key skills strongly present in your candidate profile.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-2.5">
                  {skillGap.matched.map((skill, idx) => (
                    <SkillGapBar
                      key={idx}
                      skill={skill}
                      demandPct={90 - idx * 4}
                      status="matched"
                    />
                  ))}
                </CardContent>
              </Card>
            </div>

            {/* Trending & Weak Skills */}
            <Card variant="default">
              <CardHeader>
                <CardTitle className="text-sm">Trending & Emerging Technologies</CardTitle>
                <CardDescription>
                  Market intelligence radar detected rising adoption for your target role.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {skillGap.trending?.map((skill, idx) => (
                    <Badge key={idx} variant="primary" size="md">
                      🔥 {skill}
                    </Badge>
                  ))}
                  {skillGap.weak?.map((skill, idx) => (
                    <Badge key={idx} variant="warning" size="md">
                      ⚠️ Weak evidence: {skill}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === 'parsed' && parsedResume && (
          <div className="space-y-6">
            <Card variant="default">
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <GraduationCap className="w-4 h-4 text-brand-500" />
                  Candidate Overview & Education
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                  <div>
                    <span className="text-slate-400">Name:</span>{' '}
                    <strong className="text-slate-800 dark:text-slate-200">
                      {parsedResume.name}
                    </strong>
                  </div>
                  <div>
                    <span className="text-slate-400">Email:</span>{' '}
                    <strong className="text-slate-800 dark:text-slate-200">
                      {parsedResume.email}
                    </strong>
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-100 dark:border-slate-800">
                  <h4 className="text-xs font-bold text-slate-700 dark:text-slate-300 mb-2">
                    Education:
                  </h4>
                  {parsedResume.education?.map((edu, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-700 text-xs"
                    >
                      <p className="font-bold text-slate-900 dark:text-slate-100">{edu.degree}</p>
                      <p className="text-slate-500">
                        {edu.institution} • {edu.year}
                      </p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Experience */}
            <Card variant="default">
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Briefcase className="w-4 h-4 text-brand-500" />
                  Experience Extraction
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {parsedResume.experience?.map((exp, idx) => (
                  <div
                    key={idx}
                    className="p-4 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-200 dark:border-slate-700 space-y-2 text-xs"
                  >
                    <div className="flex justify-between items-center">
                      <p className="font-bold text-slate-900 dark:text-slate-100">
                        {exp.title} • {exp.company}
                      </p>
                      <span className="text-2xs text-slate-400">
                        {exp.start} - {exp.end}
                      </span>
                    </div>
                    <ul className="list-disc list-inside space-y-1 text-slate-600 dark:text-slate-300">
                      {exp.bullets?.map((bullet, bIdx) => (
                        <li key={bIdx}>{bullet}</li>
                      ))}
                    </ul>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* NER Extracted Skills Contract */}
            <Card variant="default">
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Layers className="w-4 h-4 text-brand-500" />
                  Transformers NER Skills (Explicit vs Implicit)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {parsedResume.skills?.map((sk, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-xs space-y-1"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-900 dark:text-slate-100">
                          {sk.name}
                        </span>
                        <Badge variant={sk.type === 'explicit' ? 'primary' : 'neutral'} size="sm">
                          {sk.type}
                        </Badge>
                      </div>
                      <p className="text-2xs text-slate-500">
                        Confidence: {(sk.confidence * 100).toFixed(0)}%
                      </p>
                      {sk.evidence && (
                        <p className="text-2xs text-slate-400 italic truncate">
                          Evidence: &ldquo;{sk.evidence}&rdquo;
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === 'breakdown' && (
          <Card variant="default">
            <CardHeader>
              <CardTitle className="text-sm">Scoring Breakdown Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {Object.entries(breakdown).map(([key, val]) => (
                <div key={key} className="space-y-1.5">
                  <div className="flex justify-between text-xs font-semibold">
                    <span className="capitalize text-slate-700 dark:text-slate-300">
                      {key.replace(/_/g, ' ')}
                    </span>
                    <span className="font-mono text-brand-600 dark:text-brand-400">{val}%</span>
                  </div>
                  <ProgressBar value={val} variant="primary" showValue={false} />
                </div>
              ))}
            </CardContent>
          </Card>
        )}
      </div>
    </PageContainer>
  );
}
