import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Users2, Calendar, ExternalLink, FolderGit2, BookOpen } from 'lucide-react';
import PageContainer from '../components/layout/PageContainer';
import Card, { CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import Spinner from '../components/ui/Spinner';
import { dashboardService } from '../services/dashboardService';

export default function RoadmapPage() {
  const { resumeId = 'mock-resume-101' } = useParams();
  const [loading, setLoading] = useState(true);
  const [roadmap, setRoadmap] = useState(null);

  useEffect(() => {
    let isMounted = true;
    async function load() {
      setLoading(true);
      try {
        const data = await dashboardService.getRoadmap(resumeId);
        if (isMounted) setRoadmap(data);
      } catch (e) {
        console.error('Failed to load roadmap:', e);
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
            Synthesizing RAG-grounded curriculum from ChromaDB vector knowledge base...
          </p>
        </div>
      </PageContainer>
    );
  }

  const phases = roadmap?.phases ?? [];

  return (
    <PageContainer>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="primary" size="sm">
                FR-005
              </Badge>
              <span className="text-2xs font-mono text-slate-500">RAG ChromaDB Knowledge Base</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-slate-100 tracking-tight">
              Personalized Learning Roadmap
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
              Engineered to close detected skill gaps for target role:{' '}
              <strong className="text-slate-700 dark:text-slate-200">
                {roadmap?.target_role || 'Data Scientist / ML Engineer'}
              </strong>
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Link to={`/critique/${resumeId}`}>
              <Button variant="primary" size="sm" icon={<Users2 className="w-3.5 h-3.5" />}>
                Multi-Agent Critique
              </Button>
            </Link>
          </div>
        </div>

        {/* Phase List */}
        <div className="space-y-6">
          {phases.map((phase, idx) => (
            <Card
              key={idx}
              variant="default"
              className="overflow-hidden border-l-4 border-l-brand-500"
            >
              <CardHeader className="bg-slate-50/50 dark:bg-slate-800/40">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-xl bg-brand-600 text-white font-black text-sm flex items-center justify-center shadow-xs">
                      {idx + 1}
                    </div>
                    <div>
                      <CardTitle className="text-base">{phase.phase}</CardTitle>
                      <div className="flex items-center gap-2 mt-0.5 text-xs text-slate-500">
                        <Calendar className="w-3.5 h-3.5" />
                        <span>Timeline: {phase.weeks}</span>
                        <span>•</span>
                        <span>
                          Linked Gap:{' '}
                          <strong className="text-rose-600 dark:text-rose-400">
                            {phase.linked_gap_skill}
                          </strong>
                        </span>
                      </div>
                    </div>
                  </div>
                  <Badge variant="neutral" size="sm">
                    Phase {idx + 1} of {phases.length}
                  </Badge>
                </div>
              </CardHeader>

              <CardContent className="p-6 space-y-4">
                {/* Target Skills */}
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                    Target Competencies:
                  </h4>
                  <div className="flex flex-wrap gap-1.5">
                    {phase.skills?.map((sk, sIdx) => (
                      <Badge key={sIdx} variant="primary" size="sm">
                        {sk}
                      </Badge>
                    ))}
                  </div>
                </div>

                {/* Hands-on Project */}
                {phase.project && (
                  <div className="p-3.5 rounded-xl bg-brand-50/60 dark:bg-brand-950/30 border border-brand-200/80 dark:border-brand-900/40 space-y-1">
                    <div className="flex items-center gap-2 text-xs font-bold text-brand-700 dark:text-brand-300">
                      <FolderGit2 className="w-4 h-4" />
                      <span>Portfolio Capstone Project:</span>
                    </div>
                    <p className="text-xs text-slate-700 dark:text-slate-300 pl-6">
                      {phase.project}
                    </p>
                  </div>
                )}

                {/* Curated Resources */}
                {phase.resources && phase.resources.length > 0 && (
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                      RAG-Grounded Learning Resources:
                    </h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {phase.resources.map((res, rIdx) => (
                        <a
                          key={rIdx}
                          href={res.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 transition-colors group text-xs"
                        >
                          <div className="flex items-center gap-2 truncate">
                            <BookOpen className="w-4 h-4 text-brand-500 flex-shrink-0" />
                            <span className="font-semibold text-slate-900 dark:text-slate-100 truncate">
                              {res.title}
                            </span>
                          </div>
                          <div className="flex items-center gap-1 text-slate-400 group-hover:text-brand-600">
                            <Badge variant="neutral" size="sm">
                              {res.type}
                            </Badge>
                            <ExternalLink className="w-3.5 h-3.5" />
                          </div>
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </PageContainer>
  );
}
