import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Users2, CheckCircle2, AlertTriangle, Sparkles } from 'lucide-react';
import PageContainer from '../components/layout/PageContainer';
import Card, { CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import Tabs from '../components/ui/Tabs';
import Spinner from '../components/ui/Spinner';
import ScoreRing from '../components/ui/ScoreRing';
import { dashboardService } from '../services/dashboardService';

export default function CritiquePage() {
  const { resumeId = 'mock-resume-101' } = useParams();
  const [loading, setLoading] = useState(true);
  const [critique, setCritique] = useState(null);
  const [activePersona, setActivePersona] = useState('merged');

  useEffect(() => {
    let isMounted = true;
    async function load() {
      setLoading(true);
      try {
        const data = await dashboardService.getCritique(resumeId);
        if (isMounted) setCritique(data);
      } catch (e) {
        console.error('Failed to load critique:', e);
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
            Convening multi-agent recruiter panel (Recruiter, HR, Hiring Manager)...
          </p>
        </div>
      </PageContainer>
    );
  }

  const agents = critique?.agents ?? [];
  const merged = critique?.merged ?? {
    consensus_score: 84,
    verdict: 'Proceed to Technical Screen',
    agreements: [],
    disagreements: [],
  };

  const currentAgent = agents.find((a) => a.persona.toLowerCase().includes(activePersona));

  return (
    <PageContainer>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="primary" size="sm">
                FR-005 Multi-Agent
              </Badge>
              <span className="text-2xs font-mono text-slate-500">LLM Recruiter Personas</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-slate-100 tracking-tight">
              Multi-Agent Recruiter Persona Critique
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
              Independent critiques from 3 hiring stakeholders: Tech Recruiter, HR Director, and
              Hiring Manager.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Link to="/upload">
              <Button variant="secondary" size="sm">
                Upload Another Resume
              </Button>
            </Link>
          </div>
        </div>

        {/* Merged Consensus Banner */}
        <Card
          variant="default"
          className="border-l-4 border-l-brand-600 bg-gradient-to-r from-brand-50/50 via-transparent to-transparent dark:from-brand-950/20"
        >
          <CardContent className="p-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-1">
                <span className="text-xs font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5" />
                  Tri-Agent Consensus Verdict
                </span>
                <h3 className="text-xl font-black text-slate-900 dark:text-white">
                  {merged.verdict}
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Consensus computed from weighted aggregation across all 3 agent evaluations.
                </p>
              </div>
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <span className="text-2xs text-slate-400 block font-semibold uppercase">
                    Consensus Score
                  </span>
                  <span className="text-3xl font-black text-slate-900 dark:text-white">
                    {merged.consensus_score}
                    <span className="text-xs font-normal text-slate-400">/100</span>
                  </span>
                </div>
                <ScoreRing score={merged.consensus_score} size={64} strokeWidth={6} />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Persona Switcher Tabs */}
        <Tabs
          activeTab={activePersona}
          onChange={setActivePersona}
          tabs={[
            { id: 'merged', label: 'Consensus & Agreements' },
            { id: 'recruiter', label: 'Tech Recruiter' },
            { id: 'hr', label: 'HR Director' },
            { id: 'manager', label: 'Hiring Manager' },
          ]}
        />

        {/* View 1: Merged Consensus */}
        {activePersona === 'merged' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Agreements */}
            <Card variant="default">
              <CardHeader>
                <CardTitle className="text-sm text-emerald-600 dark:text-emerald-400 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4" />
                  Agent Points of Agreement ({merged.agreements.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {merged.agreements.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-3 bg-emerald-50/50 dark:bg-emerald-950/20 rounded-xl border border-emerald-100 dark:border-emerald-900/40 text-xs text-slate-700 dark:text-slate-300"
                  >
                    {item}
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Disagreements */}
            <Card variant="default">
              <CardHeader>
                <CardTitle className="text-sm text-amber-600 dark:text-amber-400 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" />
                  Points of Debate & Divergence ({merged.disagreements.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {merged.disagreements.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-3 bg-amber-50/50 dark:bg-amber-950/20 rounded-xl border border-amber-100 dark:border-amber-900/40 text-xs text-slate-700 dark:text-slate-300"
                  >
                    {item}
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        )}

        {/* View 2: Specific Persona Critique */}
        {activePersona !== 'merged' && currentAgent && (
          <div className="space-y-6">
            <Card variant="default">
              <CardHeader>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <CardTitle className="text-base flex items-center gap-2">
                      <Users2 className="w-5 h-5 text-brand-500" />
                      {currentAgent.persona} Evaluation
                    </CardTitle>
                    <CardDescription>
                      Verdict:{' '}
                      <strong className="text-slate-800 dark:text-slate-200">
                        {currentAgent.verdict}
                      </strong>
                    </CardDescription>
                  </div>
                  <Badge variant="primary" size="md">
                    Persona Score: {currentAgent.score}/100
                  </Badge>
                </div>
              </CardHeader>

              <CardContent className="space-y-6">
                {/* Strengths & Concerns */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4" /> Observed Strengths
                    </h4>
                    <ul className="space-y-1.5 text-xs text-slate-700 dark:text-slate-300 list-disc list-inside">
                      {currentAgent.strengths.map((str, sIdx) => (
                        <li key={sIdx}>{str}</li>
                      ))}
                    </ul>
                  </div>

                  <div className="space-y-2">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-rose-600 dark:text-rose-400 flex items-center gap-1.5">
                      <AlertTriangle className="w-4 h-4" /> Recruiter Concerns
                    </h4>
                    <ul className="space-y-1.5 text-xs text-slate-700 dark:text-slate-300 list-disc list-inside">
                      {currentAgent.concerns.map((con, cIdx) => (
                        <li key={cIdx}>{con}</li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* Rewrites (Before vs After) */}
                {currentAgent.rewrites && currentAgent.rewrites.length > 0 && (
                  <div className="pt-4 border-t border-slate-100 dark:border-slate-800 space-y-3">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                      Recommended Bullet Rewrites for Recruiter Impact:
                    </h4>
                    {currentAgent.rewrites.map((rw, rIdx) => (
                      <div
                        key={rIdx}
                        className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 space-y-2 text-xs"
                      >
                        <div className="space-y-1">
                          <span className="text-2xs font-bold uppercase text-rose-600 dark:text-rose-400">
                            Before (Generic):
                          </span>
                          <p className="text-slate-600 dark:text-slate-400 line-through italic pl-2 border-l-2 border-rose-300">
                            &ldquo;{rw.before}&rdquo;
                          </p>
                        </div>
                        <div className="space-y-1">
                          <span className="text-2xs font-bold uppercase text-emerald-600 dark:text-emerald-400">
                            After (Recruiter-Grade Impact):
                          </span>
                          <p className="text-slate-900 dark:text-slate-100 font-medium pl-2 border-l-2 border-emerald-500">
                            &ldquo;{rw.after}&rdquo;
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </PageContainer>
  );
}
