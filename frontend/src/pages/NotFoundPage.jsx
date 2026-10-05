import React from 'react';
import { Link } from 'react-router-dom';
import { HelpCircle, Home } from 'lucide-react';
import Button from '../components/ui/Button';

export default function NotFoundPage() {
  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-slate-50 dark:bg-slate-925 text-center">
      <div className="max-w-md w-full space-y-6">
        <div className="w-16 h-16 rounded-3xl bg-brand-50 dark:bg-brand-950/80 text-brand-600 dark:text-brand-400 mx-auto flex items-center justify-center shadow-subtle border border-brand-200 dark:border-brand-900">
          <HelpCircle className="w-8 h-8" />
        </div>

        <div className="space-y-2">
          <span className="text-xs font-mono font-bold text-brand-600 dark:text-brand-400 uppercase tracking-widest">
            HTTP 404 Error
          </span>
          <h1 className="text-3xl font-black text-slate-900 dark:text-white tracking-tight">
            Page Not Found
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">
            The career intelligence route you requested does not exist or may have been archived.
          </p>
        </div>

        <div className="flex items-center justify-center gap-3">
          <Link to="/">
            <Button variant="primary" size="md" icon={<Home className="w-4 h-4" />}>
              Return to Dashboard
            </Button>
          </Link>
          <Link to="/upload">
            <Button variant="secondary" size="md">
              Upload Resume
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
