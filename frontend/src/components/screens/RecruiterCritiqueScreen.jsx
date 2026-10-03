import React, { useState } from 'react';
import { Users, UserCheck, CheckCircle2, AlertCircle, ArrowRight, Sparkles, Scale, Copy, Check } from 'lucide-react';
import Card, { CardHeader, CardTitle, CardContent } from '../ui/Card';
import Badge from '../ui/Badge';
import Tabs from '../ui/Tabs';
import Button from '../ui/Button';
import Skeleton from '../ui/Skeleton';
import ErrorState from '../ui/ErrorState';
import EmptyState from '../ui/EmptyState';
import { mockCritique } from '../../data/mockData';

export default function RecruiterCritiqueScreen({ state = 'success', data = mockCritique }) {
  const [activePersona, setActivePersona] = useState('Recruiter');
  const [copiedIdx, setCopiedIdx] = useState(null);

  if (state === 'empty') {
    return (
      <EmptyState
        icon={Users}
        title="No Recruiter Critique Generated"
        description="Trigger the multi-agent LLM critique to get unvarnished feedback from Recruiter, HR, and Hiring Manager personas."
        action={{ label: "Run Multi-Agent Critique", onClick: () => {} }}
      />
    );
  }

  if (state === 'loading') {
    return (
      <div className="space-y-6">
        <div className="p-6 bg-white dark:bg-slate-850 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-4">
          <Skeleton variant="text" width="260px" height="24px" />
          <Skeleton variant="text" width="450px" height="14px" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Skeleton variant="card" count={3} />
        </div>
      </div>
    );
  }

  if (state === 'error') {
    return (
      <ErrorState
        error={{
          code: 'LLM_AGENT_CONSENSUS_TIMEOUT',
          message: 'The multi-agent debate loop timed out while synthesizing Hiring Manager and Recruiter feedback. Re-dispatching agent consensus.'
        }}
        onRetry={() => {}}
        actionLabel="Retry Persona Synthesis"
      />
    );
  }

  const personaTabs = [
    { id: 'Recruiter', label: 'Senior Tech Recruiter', badge: `${data.agents.find(a => a.persona === 'Recruiter')?.score || 85}/100` },
    { id: 'HR', label: 'HR Director', badge: `${data.agents.find(a => a.persona === 'HR')?.score || 80}/100` },
    { id: 'Hiring Manager', label: 'Engineering Hiring Manager', badge: `${data.agents.find(a => a.persona === 'Hiring Manager')?.score || 81}/100` },
  ];

  const currentAgent = data.agents.find((a) => a.persona === activePersona) || data.agents[0];

  const handleCopyRewrite = (text, idx) => {
    navigator.clipboard?.writeText(text);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight flex items-center gap-2">
            Multi-Agent Recruiter Critique
            <Badge variant="primary" size="sm">FR-005</Badge>
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            Simulated evaluation from 3 distinct hiring viewpoints to eliminate subjective bias.
          </p>
        </div>
        <Badge variant="success" size="md" dot>
          Consensus Score: {data.merged.consensus_score}/100
        </Badge>
      </div>

      {/* Merged Consensus Banner */}
      <Card variant="elevated" className="border-brand-200 dark:border-brand-900/60 bg-gradient-to-r from-brand-50/50 via-white to-purple-50/30 dark:from-brand-950/20 dark:via-slate-850 dark:to-purple-950/20">
        <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-none pb-2">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-brand-600 text-white flex items-center justify-center">
              <Scale className="w-4 h-4" />
            </div>
            <div>
              <span className="text-2xs font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400">
                Multi-Agent Synthesis
              </span>
              <h3 className="text-sm sm:text-base font-bold text-slate-900 dark:text-slate-100">
                Tri-Persona Consensus Verdict
              </h3>
            </div>
          </div>
          <Badge variant="role" size="md">
            Verdict: {data.merged.verdict.split('.')[0]}
          </Badge>
        </CardHeader>
        <CardContent className="pt-0 space-y-4">
          <p className="text-xs sm:text-sm text-slate-700 dark:text-slate-300 font-medium leading-relaxed">
            "{data.merged.verdict}"
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-slate-200/60 dark:border-slate-800 text-xs">
            {/* Agreements */}
            <div className="space-y-1.5">
              <span className="text-2xs font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> Consensus Agreements
              </span>
              <ul className="space-y-1 text-slate-600 dark:text-slate-400">
                {data.merged.agreements.map((ag, i) => (
                  <li key={i} className="flex items-start gap-1.5">
                    <span className="text-emerald-500 font-bold">•</span>
                    <span>{ag}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Disagreements */}
            <div className="space-y-1.5">
              <span className="text-2xs font-bold uppercase tracking-wider text-amber-600 dark:text-amber-400 flex items-center gap-1">
                <AlertCircle className="w-3.5 h-3.5" /> Persona Deliberation
              </span>
              <ul className="space-y-1 text-slate-600 dark:text-slate-400">
                {data.merged.disagreements.map((dis, i) => (
                  <li key={i} className="flex items-start gap-1.5">
                    <span className="text-amber-500 font-bold">•</span>
                    <span>{dis}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Persona Tabs Switcher */}
      <Tabs
        tabs={personaTabs}
        activeTab={activePersona}
        onChange={setActivePersona}
        variant="pills"
      />

      {/* Selected Agent View */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Verdict, Strengths, Concerns */}
        <div className="space-y-6">
          <Card variant="default">
            <CardHeader className="flex items-center justify-between">
              <CardTitle>{currentAgent.persona}'s Assessment</CardTitle>
              <Badge score={currentAgent.score} size="md">
                {currentAgent.score}/100
              </Badge>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <span className="text-2xs font-semibold text-slate-400 uppercase tracking-wider">Verdict</span>
                <p className="text-xs sm:text-sm text-slate-800 dark:text-slate-200 mt-1 italic leading-relaxed">
                  "{currentAgent.verdict}"
                </p>
              </div>

              {/* Strengths */}
              <div>
                <span className="text-2xs font-semibold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider block mb-2">
                  Recognized Strengths
                </span>
                <ul className="space-y-2 text-xs text-slate-700 dark:text-slate-300">
                  {currentAgent.strengths.map((s, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-emerald-500 font-bold">✓</span>
                      <span>{s}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Concerns */}
              <div>
                <span className="text-2xs font-semibold text-rose-600 dark:text-rose-400 uppercase tracking-wider block mb-2">
                  Concerns & Friction Points
                </span>
                <ul className="space-y-2 text-xs text-slate-700 dark:text-slate-300">
                  {currentAgent.concerns.map((c, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-rose-500 font-bold">✕</span>
                      <span>{c}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Interactive Bullet Point Rewrites */}
        <div className="lg:col-span-2 space-y-4">
          <Card variant="default">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-brand-500" />
                Actionable Bullet Point Rewrites (Google XYZ Formula)
              </CardTitle>
              <p className="text-2xs text-slate-500">
                Transforms unquantified claims into recruiter-grade accomplishments
              </p>
            </CardHeader>
            <CardContent className="space-y-5">
              {currentAgent.rewrites.map((rewrite, rIdx) => (
                <div
                  key={rIdx}
                  className="rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-2xs"
                >
                  {/* Before */}
                  <div className="p-3.5 bg-rose-50/50 dark:bg-rose-950/20 border-b border-slate-200 dark:border-slate-800 flex items-start gap-3">
                    <span className="text-2xs font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-rose-200 text-rose-800 dark:bg-rose-900/60 dark:text-rose-300 flex-shrink-0 mt-0.5">
                      Before
                    </span>
                    <p className="text-xs text-rose-900 dark:text-rose-200 leading-relaxed line-through opacity-85">
                      {rewrite.before}
                    </p>
                  </div>

                  {/* After */}
                  <div className="p-3.5 bg-emerald-50/50 dark:bg-emerald-950/20 flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                    <div className="flex items-start gap-3">
                      <span className="text-2xs font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-emerald-200 text-emerald-800 dark:bg-emerald-900/60 dark:text-emerald-300 flex-shrink-0 mt-0.5">
                        Optimized
                      </span>
                      <p className="text-xs font-semibold text-emerald-950 dark:text-emerald-100 leading-relaxed">
                        {rewrite.after}
                      </p>
                    </div>

                    <button
                      type="button"
                      onClick={() => handleCopyRewrite(rewrite.after, rIdx)}
                      aria-label="Copy optimized bullet point"
                      className="self-end sm:self-start inline-flex items-center gap-1 text-2xs font-semibold px-2 py-1 rounded bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:border-brand-500 hover:text-brand-600 transition-colors"
                    >
                      {copiedIdx === rIdx ? (
                        <>
                          <Check className="w-3 h-3 text-emerald-500" />
                          <span className="text-emerald-600">Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3 h-3" />
                          <span>Copy</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
