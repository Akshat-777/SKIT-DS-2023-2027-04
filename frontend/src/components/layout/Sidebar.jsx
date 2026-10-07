import React from 'react';
import { NavLink, useParams } from 'react-router-dom';
import {
  UploadCloud,
  FileCheck2,
  TrendingUp,
  Compass,
  Users2,
  History,
  X,
  Sparkles,
  BookOpen,
  Award,
} from 'lucide-react';
import Badge from '../ui/Badge';

export default function Sidebar({ isOpen, onClose }) {
  // If user is currently on a specific resume route, preserve that ID in links
  const params = useParams();
  const currentResumeId = params.resumeId || 'mock-resume-101';

  const navItems = [
    {
      to: '/upload',
      icon: UploadCloud,
      label: 'Resume Ingestion',
      badge: 'FR-001',
      description: 'OCR & PDF/DOCX Parsing',
    },
    {
      to: `/analysis/${currentResumeId}`,
      icon: FileCheck2,
      label: 'ATS & Skill Gap',
      badge: 'FR-003',
      description: 'Live Market Benchmark',
    },
    {
      to: `/market-fit/${currentResumeId}`,
      icon: TrendingUp,
      label: 'Market Fit & Salary',
      badge: 'FR-004',
      description: 'LightGBM Regression',
    },
    {
      to: `/roadmap/${currentResumeId}`,
      icon: Compass,
      label: 'Learning Roadmap',
      badge: 'FR-005',
      description: 'RAG Grounded Phases',
    },
    {
      to: `/critique/${currentResumeId}`,
      icon: Users2,
      label: 'Recruiter Critique',
      badge: 'Multi-Agent',
      description: 'Recruiter, HR, Manager',
    },
    {
      to: '/history',
      icon: History,
      label: 'Upload History',
      description: 'Saved analyses & tokens',
    },
  ];

  const content = (
    <div className="flex flex-col h-full bg-white dark:bg-slate-900 border-r border-slate-200/80 dark:border-slate-800">
      {/* Mobile Header */}
      <div className="lg:hidden flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-brand-600 text-white flex items-center justify-center">
            <Sparkles className="w-4 h-4" />
          </div>
          <span className="font-extrabold text-slate-900 dark:text-white">CareerLens</span>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="p-1.5 rounded-lg text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Main Navigation Links */}
      <div className="flex-1 py-4 px-3 space-y-1.5 overflow-y-auto">
        <div className="px-3 mb-2 text-2xs font-bold uppercase tracking-wider text-slate-400">
          Core Modules
        </div>

        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onClose}
              className={({ isActive }) =>
                `group flex items-start gap-3 px-3 py-2.5 rounded-xl transition-all duration-150 ${
                  isActive
                    ? 'bg-brand-500/10 dark:bg-brand-500/15 text-brand-600 dark:text-brand-400 font-semibold shadow-xs border border-brand-500/20'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100/70 dark:hover:bg-slate-800/60'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <div
                    className={`mt-0.5 p-1.5 rounded-lg transition-colors ${
                      isActive
                        ? 'bg-brand-500 text-white shadow-glow-brand'
                        : 'bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 group-hover:bg-white dark:group-hover:bg-slate-700'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-1">
                      <span className="text-xs truncate">{item.label}</span>
                      {item.badge && (
                        <Badge
                          variant={isActive ? 'primary' : 'neutral'}
                          size="sm"
                          className="scale-90"
                        >
                          {item.badge}
                        </Badge>
                      )}
                    </div>
                    {item.description && (
                      <p className="text-[10px] text-slate-400 dark:text-slate-500 truncate mt-0.5">
                        {item.description}
                      </p>
                    )}
                  </div>
                </>
              )}
            </NavLink>
          );
        })}
      </div>

      {/* Team & Institutional Metadata */}
      <div className="p-3.5 m-3 rounded-2xl bg-slate-50 dark:bg-slate-850 border border-slate-200/80 dark:border-slate-800 space-y-2">
        <div className="flex items-center gap-1.5 text-2xs font-bold text-slate-700 dark:text-slate-300">
          <Award className="w-3.5 h-3.5 text-brand-500" />
          <span>SKIT Jaipur (2023 - 2027)</span>
        </div>
        <p className="text-2xs text-slate-500 dark:text-slate-400 leading-relaxed">
          B.Tech CSE (Data Science) Project
          <br />
          SDG 4: Quality Education
        </p>
        <div className="pt-2 border-t border-slate-200/60 dark:border-slate-800 text-[10px] text-slate-400">
          <p className="font-semibold text-slate-600 dark:text-slate-300">Core Team:</p>
          <p className="truncate">Akshat A., Akshat G., Aishani B., Aryan R.</p>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Permanent Sidebar */}
      <aside className="hidden lg:block w-64 flex-shrink-0 h-[calc(100vh-4rem)] sticky top-16 z-30">
        {content}
      </aside>

      {/* Mobile Drawer (with backdrop) */}
      {isOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          <div
            className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs transition-opacity"
            onClick={onClose}
          />
          <div className="relative w-72 max-w-[80vw] h-full shadow-modal animate-in slide-in-from-left duration-200 z-10">
            {content}
          </div>
        </div>
      )}
    </>
  );
}
