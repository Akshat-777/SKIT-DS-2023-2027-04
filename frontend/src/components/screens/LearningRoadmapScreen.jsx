import React from 'react';
import { Compass, BookOpen, ExternalLink, Code2, Link2, Calendar, CheckSquare, Sparkles } from 'lucide-react';
import Card, { CardHeader, CardTitle, CardContent } from '../ui/Card';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import Skeleton from '../ui/Skeleton';
import ErrorState from '../ui/ErrorState';
import EmptyState from '../ui/EmptyState';
import { mockRoadmap } from '../../data/mockData';

export default function LearningRoadmapScreen({ state = 'success', data = mockRoadmap }) {
  if (state === 'empty') {
    return (
      <EmptyState
        icon={Compass}
        title="No Learning Roadmap Generated"
        description="Run the skill gap evaluation to synthesize an AI-grounded, RAG-personalized curriculum."
        action={{ label: "Generate Roadmap", onClick: () => {} }}
      />
    );
  }

  if (state === 'loading') {
    return (
      <div className="space-y-6">
        <div className="p-6 bg-white dark:bg-slate-850 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-4">
          <Skeleton variant="text" width="280px" height="24px" />
          <Skeleton variant="text" width="400px" height="14px" />
        </div>
        <div className="space-y-4">
          <Skeleton variant="card" count={3} />
        </div>
      </div>
    );
  }

  if (state === 'error') {
    return (
      <ErrorState
        error={{
          code: 'RAG_GENERATION_FAILED',
          message: 'The RAG curriculum generator timed out while querying ChromaDB verified course vectors. Re-dispatching prompt.'
        }}
        onRetry={() => {}}
        actionLabel="Regenerate Roadmap"
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight flex items-center gap-2">
            Personalized Learning Roadmap
            <Badge variant="primary" size="sm">FR-005</Badge>
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            RAG-grounded curriculum dynamically tailored to close verified skill gaps for <span className="font-semibold text-brand-600 dark:text-brand-400">{data.target_role}</span>.
          </p>
        </div>
        <Badge variant="role" size="md">
          <Sparkles className="w-3.5 h-3.5 mr-1 inline" /> SDG 4: Quality Education
        </Badge>
      </div>

      {/* Phases Timeline */}
      <div className="space-y-6">
        {data.phases.map((phase, idx) => (
          <Card key={idx} variant="elevated" className="overflow-hidden border-l-4 border-l-brand-600">
            <CardHeader className="bg-slate-50/70 dark:bg-slate-900/40 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <span className="text-2xs font-mono font-bold text-brand-600 dark:text-brand-400 flex items-center gap-1.5 uppercase">
                  <Calendar className="w-3.5 h-3.5" />
                  {phase.weeks}
                </span>
                <CardTitle className="text-base sm:text-lg mt-1">{phase.phase}</CardTitle>
              </div>

              {/* Linked Gap Skill Badge */}
              <div className="flex items-center gap-1.5 self-start sm:self-auto">
                <span className="text-2xs text-slate-400">Target Gap:</span>
                <Badge variant="danger" size="sm" className="font-medium">
                  <Link2 className="w-3 h-3 mr-1" />
                  {phase.linked_gap_skill}
                </Badge>
              </div>
            </CardHeader>

            <CardContent className="p-6 space-y-5">
              {/* Skills targeted */}
              <div>
                <span className="text-2xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                  Skills To Master
                </span>
                <div className="flex flex-wrap gap-2">
                  {phase.skills.map((skill, sIdx) => (
                    <Badge key={sIdx} variant="primary" size="md">
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Vetted Learning Resources */}
              <div>
                <span className="text-2xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                  Curated Open-Access Resources (RAG Retrieved)
                </span>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {phase.resources.map((res, rIdx) => (
                    <a
                      key={rIdx}
                      href={res.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-850 hover:border-brand-500 dark:hover:border-brand-500 hover:shadow-xs transition-all flex items-center justify-between gap-3 group"
                    >
                      <div className="flex items-center gap-2.5 min-w-0">
                        <div className="w-7 h-7 rounded-md bg-brand-50 dark:bg-brand-950 text-brand-600 dark:text-brand-400 flex items-center justify-center flex-shrink-0">
                          <BookOpen className="w-4 h-4" />
                        </div>
                        <div className="truncate">
                          <p className="text-xs font-semibold text-slate-900 dark:text-slate-100 group-hover:text-brand-600 truncate">
                            {res.title}
                          </p>
                          <p className="text-2xs text-slate-400">{res.type}</p>
                        </div>
                      </div>
                      <ExternalLink className="w-3.5 h-3.5 text-slate-400 group-hover:text-brand-600 flex-shrink-0" />
                    </a>
                  ))}
                </div>
              </div>

              {/* Capstone Project to Build */}
              <div className="p-4 rounded-xl bg-brand-50/50 dark:bg-brand-950/20 border border-brand-200/70 dark:border-brand-900/50">
                <span className="text-2xs font-bold uppercase tracking-wider text-brand-700 dark:text-brand-300 flex items-center gap-1.5 mb-1">
                  <Code2 className="w-4 h-4" /> Recommended Proof-of-Work Project
                </span>
                <p className="text-xs sm:text-sm font-semibold text-slate-900 dark:text-slate-100">
                  {phase.project}
                </p>
                <p className="text-2xs text-slate-500 dark:text-slate-400 mt-1">
                  Adding this verified repository project directly addresses the recruiter's experience evidence concern.
                </p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
