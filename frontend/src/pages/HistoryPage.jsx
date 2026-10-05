import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { History, FileText, ArrowRight, UploadCloud } from 'lucide-react';
import PageContainer from '../components/layout/PageContainer';
import Card, { CardContent } from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import Spinner from '../components/ui/Spinner';
import EmptyState from '../components/ui/EmptyState';
import { resumeService } from '../services/resumeService';
import { formatDate, getScoreThreshold } from '../utils/formatters';

export default function HistoryPage() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    async function load() {
      setLoading(true);
      try {
        const list = await resumeService.getResumeHistory();
        if (isMounted) setHistory(list);
      } catch (e) {
        console.error('Failed to load history:', e);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    load();
    return () => {
      isMounted = false;
    };
  }, []);

  if (loading) {
    return (
      <PageContainer>
        <div className="py-20 flex flex-col items-center justify-center space-y-4">
          <Spinner size="lg" variant="primary" />
          <p className="text-sm font-medium text-slate-500 animate-pulse">
            Loading resume parsing and analysis history...
          </p>
        </div>
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="primary" size="sm">
                History
              </Badge>
              <span className="text-2xs font-mono text-slate-500">FastAPI Parsed Resumes</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-slate-100 tracking-tight">
              Resume Analysis History
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
              Review prior resume submissions, benchmark comparisons, and recruiter feedback.
            </p>
          </div>

          <Link to="/upload">
            <Button variant="primary" size="sm" icon={<UploadCloud className="w-4 h-4" />}>
              Upload New Resume
            </Button>
          </Link>
        </div>

        {/* History List or Empty */}
        {history.length === 0 ? (
          <EmptyState
            icon={History}
            title="No Resumes Uploaded Yet"
            description="Upload your first resume to trigger the complete ATS analysis, LightGBM market prediction, and multi-agent critique."
            action={{
              label: 'Upload Resume',
              onClick: () => {
                window.location.href = '/upload';
              },
            }}
          />
        ) : (
          <div className="space-y-3">
            {history.map((item) => {
              const threshold = getScoreThreshold(item.ats_score || 80);
              return (
                <Card
                  key={item.resume_id}
                  variant="default"
                  className="hover:border-brand-300 dark:hover:border-slate-700 transition-all"
                >
                  <CardContent className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="flex items-start sm:items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-brand-50 dark:bg-brand-950/80 text-brand-600 dark:text-brand-400 flex items-center justify-center flex-shrink-0">
                        <FileText className="w-5 h-5" />
                      </div>
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-2">
                          <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                            {item.fileName || 'Resume.pdf'}
                          </h3>
                          <Badge variant={threshold.badgeVariant} size="sm">
                            ATS: {item.ats_score || 82}%
                          </Badge>
                        </div>
                        <p className="text-xs text-slate-500">
                          Role:{' '}
                          <span className="font-semibold text-slate-700 dark:text-slate-300">
                            {item.target_role}
                          </span>{' '}
                          • {formatDate(item.uploadedAt)}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 flex-wrap">
                      <Link to={`/analysis/${item.resume_id}`}>
                        <Button variant="secondary" size="sm">
                          ATS Score
                        </Button>
                      </Link>
                      <Link to={`/market-fit/${item.resume_id}`}>
                        <Button variant="secondary" size="sm">
                          Market Fit
                        </Button>
                      </Link>
                      <Link to={`/roadmap/${item.resume_id}`}>
                        <Button variant="secondary" size="sm">
                          Roadmap
                        </Button>
                      </Link>
                      <Link to={`/critique/${item.resume_id}`}>
                        <Button
                          variant="primary"
                          size="sm"
                          icon={<ArrowRight className="w-3.5 h-3.5" />}
                          iconPosition="right"
                        >
                          Critique
                        </Button>
                      </Link>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </PageContainer>
  );
}
