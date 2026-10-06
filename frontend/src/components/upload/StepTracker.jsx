import React, { useState, useEffect } from 'react';
import {
  CheckCircle2,
  FileCheck2,
  FileSearch,
  Users2,
  Cpu,
  BarChart3,
  AlertTriangle,
  Clock,
  Sparkles,
} from 'lucide-react';
import ProgressBar from '../ui/ProgressBar';
import Badge from '../ui/Badge';
import Spinner from '../ui/Spinner';

export const PARSING_STEPS = [
  {
    id: 'uploaded',
    label: 'Uploaded',
    description: 'Document received and validated by FastAPI gateway',
    percentage: 20,
    icon: FileCheck2,
  },
  {
    id: 'text_extraction',
    label: 'Text extraction/OCR',
    description: 'PyMuPDF text streams & TrOCR optical recognition',
    percentage: 40,
    icon: FileSearch,
  },
  {
    id: 'entity_extraction',
    label: 'Entity extraction',
    description: 'Hugging Face Transformers NER (Education, Experience)',
    percentage: 60,
    icon: Users2,
  },
  {
    id: 'skill_extraction',
    label: 'Skill extraction',
    description: 'Explicit & implicit skills taxonomy classification',
    percentage: 80,
    icon: Cpu,
  },
  {
    id: 'scoring',
    label: 'Scoring',
    description: 'LightGBM ATS score & live job-market demand match',
    percentage: 100,
    icon: BarChart3,
  },
];

/**
 * CareerLens StepTracker Component
 * 
 * Displays live parsing progress across 5 microservice stages:
 * Uploaded -> Text extraction/OCR -> Entity extraction -> Skill extraction -> Scoring
 * 
 * Features:
 * - Real-time progress bar (0-100%)
 * - Step icons with Completed, In-Progress, Pending, and Failed states
 * - Current-step dynamic message from backend NLP workers
 * - "OCR in use for scanned document" notice with visual highlight
 * - Elapsed timer & cloud specification indicator (Min 8GB RAM Cloud Server)
 */
export default function StepTracker({
  currentStepId = 'uploaded',
  progressPct = 20,
  currentMessage = 'Parsing document in Hugging Face Transformers & LightGBM pipeline...',
  ocrInUse = false,
  isFailed = false,
  failedStepId = null,
  onCancel,
  className = '',
}) {
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  // Timer tracking elapsed parsing duration
  useEffect(() => {
    const timer = setInterval(() => {
      setElapsedSeconds((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Determine current active step index
  const activeStepIndex = PARSING_STEPS.findIndex(
    (s) => s.id === currentStepId
  );
  const normalizedIndex = activeStepIndex >= 0 ? activeStepIndex : 0;

  return (
    <div
      data-testid="step-tracker-container"
      className={`w-full bg-white dark:bg-slate-850 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 sm:p-8 shadow-card space-y-6 ${className}`}
    >
      {/* Header & Meta */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="primary" size="sm">
              Live NLP Pipeline
            </Badge>
            <span className="text-2xs font-mono text-slate-500">FR-001 • FR-002 • FR-003</span>
          </div>
          <h3 className="text-lg sm:text-xl font-bold text-slate-900 dark:text-slate-100">
            Analyzing Resume & Market Fit
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Polling FastAPI status every 2 seconds. Live Hugging Face NER and LightGBM model execution.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 text-2xs font-mono text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
            <Clock className="w-3.5 h-3.5 text-brand-500" />
            <span>Elapsed: {elapsedSeconds}s</span>
          </div>

          {onCancel && (
            <button
              type="button"
              data-testid="cancel-parsing-button"
              onClick={onCancel}
              className="text-2xs font-medium text-slate-500 hover:text-rose-600 dark:hover:text-rose-400 transition-colors"
            >
              Cancel
            </button>
          )}
        </div>
      </div>

      {/* OCR Notice: Scanned document detection */}
      {ocrInUse && (
        <div
          data-testid="ocr-notice-banner"
          className="flex items-start sm:items-center gap-3 p-3.5 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/80 text-amber-900 dark:text-amber-200 text-xs animate-fade-in"
        >
          <div className="w-7 h-7 rounded-lg bg-amber-200 dark:bg-amber-900 text-amber-800 dark:text-amber-200 flex items-center justify-center flex-shrink-0">
            <Sparkles className="w-4 h-4" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-bold">OCR in use for scanned document</span>
              <span className="px-1.5 py-0.5 rounded bg-amber-200 dark:bg-amber-900 text-3xs font-mono font-bold uppercase tracking-wider">
                TrOCR Active
              </span>
            </div>
            <p className="text-2xs text-amber-800 dark:text-amber-300 mt-0.5">
              PyMuPDF detected non-text bitmap streams. Optical character recognition pipeline is active for deep text recovery.
            </p>
          </div>
        </div>
      )}

      {/* Progress Bar with Percentage */}
      <div className="space-y-1.5">
        <div className="flex justify-between items-center text-xs font-semibold">
          <span className="text-slate-700 dark:text-slate-300">
            Current Stage: <span className="text-brand-600 dark:text-brand-400 font-bold">{PARSING_STEPS[normalizedIndex]?.label}</span>
          </span>
          <span className="font-mono font-bold text-brand-600 dark:text-brand-400 text-sm">
            {progressPct}%
          </span>
        </div>
        <ProgressBar
          value={progressPct}
          max={100}
          variant="gradient"
          size="md"
          animated={!isFailed && progressPct < 100}
        />
        <p className="text-2xs text-slate-500 dark:text-slate-400 italic">
          {currentMessage}
        </p>
      </div>

      {/* 5-Step Visual Tracker Flow */}
      <div className="pt-4 border-t border-slate-100 dark:border-slate-800">
        <ol className="grid grid-cols-1 sm:grid-cols-5 gap-3 sm:gap-2">
          {PARSING_STEPS.map((step, idx) => {
            const Icon = step.icon;
            const isCompleted = idx < normalizedIndex || progressPct >= 100;
            const isCurrent = idx === normalizedIndex && progressPct < 100 && !isFailed;
            const isStepFailed = isFailed && (failedStepId === step.id || idx === normalizedIndex);
            const isPending = idx > normalizedIndex && !isFailed;

            return (
              <li
                key={step.id}
                data-testid={`step-item-${step.id}`}
                className={`relative flex sm:flex-col items-center sm:items-start p-3 sm:p-3 rounded-xl border transition-all ${
                  isCompleted
                    ? 'bg-emerald-50/50 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-800/60'
                    : isCurrent
                    ? 'bg-brand-50/60 dark:bg-brand-950/30 border-brand-300 dark:border-brand-700 shadow-sm ring-2 ring-brand-500/20'
                    : isStepFailed
                    ? 'bg-rose-50 dark:bg-rose-950/30 border-rose-300 dark:border-rose-800'
                    : 'bg-slate-50/60 dark:bg-slate-900/40 border-slate-200 dark:border-slate-800 opacity-60'
                }`}
              >
                <div className="flex items-center sm:justify-between w-full mb-0 sm:mb-2">
                  {/* Step Icon */}
                  <div
                    className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                      isCompleted
                        ? 'bg-emerald-600 text-white'
                        : isCurrent
                        ? 'bg-brand-600 text-white shadow-glow-brand'
                        : isStepFailed
                        ? 'bg-rose-600 text-white'
                        : 'bg-slate-200 dark:bg-slate-800 text-slate-500'
                    }`}
                  >
                    {isCompleted ? (
                      <CheckCircle2 className="w-4 h-4" />
                    ) : isCurrent ? (
                      <Spinner size="xs" color="white" />
                    ) : isStepFailed ? (
                      <AlertTriangle className="w-4 h-4" />
                    ) : (
                      <Icon className="w-4 h-4" />
                    )}
                  </div>

                  {/* Step Number Tag */}
                  <span className="hidden sm:inline-block text-3xs font-mono font-semibold text-slate-400">
                    0{idx + 1}
                  </span>
                </div>

                {/* Step Details */}
                <div className="ml-3 sm:ml-0 min-w-0 flex-1">
                  <div className="flex items-center gap-1.5">
                    <span
                      className={`text-xs font-bold truncate ${
                        isCompleted
                          ? 'text-emerald-700 dark:text-emerald-300'
                          : isCurrent
                          ? 'text-brand-700 dark:text-brand-300'
                          : isStepFailed
                          ? 'text-rose-700 dark:text-rose-300'
                          : 'text-slate-600 dark:text-slate-400'
                      }`}
                    >
                      {step.label}
                    </span>
                  </div>

                  <p className="hidden sm:block text-3xs text-slate-500 dark:text-slate-400 line-clamp-2 mt-0.5 leading-tight">
                    {step.description}
                  </p>
                </div>
              </li>
            );
          })}
        </ol>
      </div>
    </div>
  );
}
