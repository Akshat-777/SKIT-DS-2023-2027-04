import React, { useState } from 'react';
import {
  Smartphone,
  Tablet,
  Monitor,
  Maximize2,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Sparkles,
  RefreshCw,
  Code2,
  Copy,
  Check,
  Eye,
  Sliders,
  Award,
} from 'lucide-react';
import AtsSkillGapScreen from '../screens/AtsSkillGapScreen';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import {
  mockScoreGood,
  mockScorePoor,
  mockScoreFair,
  mockScoreExcellent,
  mockScoreNoGaps,
  mockRoleFixtures,
} from '../../data/mockScoreFixtures';

/**
 * AtsStorybookDemo Component
 * Storybook-like interactive workbench for testing:
 * - Viewport widths: 375px (Mobile), 768px (Tablet), 1440px (Desktop), and Fluid 100%
 * - Fixture states: Poor (42), Fair (64), Good (82), Excellent (94), No Gaps (100%)
 * - Operational states: Success, Loading (Skeleton), Empty ("no gaps found"), Error with retry
 * - Target role switcher
 * - Raw JSON contract inspector
 */
export default function AtsStorybookDemo() {
  // Workbench controls
  const [viewport, setViewport] = useState('fluid'); // '375', '768', '1440', 'fluid'
  const [activeFixtureKey, setActiveFixtureKey] = useState('good'); // 'poor', 'fair', 'good', 'excellent', 'nogaps'
  const [componentState, setComponentState] = useState('success'); // 'success', 'loading', 'empty', 'error'
  const [showJsonInspector, setShowJsonInspector] = useState(false);
  const [copiedJson, setCopiedJson] = useState(false);

  // Fixtures mapping
  const fixtureMap = {
    poor: { name: 'Poor Fit (42)', data: mockScorePoor, badge: 'danger' },
    fair: { name: 'Fair Fit (64)', data: mockScoreFair, badge: 'warning' },
    good: { name: 'Good Fit (82)', data: mockScoreGood, badge: 'primary' },
    excellent: { name: 'Excellent Fit (94)', data: mockScoreExcellent, badge: 'success' },
    nogaps: { name: 'No Gaps (100%)', data: mockScoreNoGaps, badge: 'success' },
  };

  const activeFixture = fixtureMap[activeFixtureKey] || fixtureMap.good;

  const handleCopyJson = () => {
    navigator.clipboard?.writeText(JSON.stringify(activeFixture.data, null, 2));
    setCopiedJson(true);
    setTimeout(() => setCopiedJson(false), 2000);
  };

  const getViewportWidthClass = () => {
    switch (viewport) {
      case '375':
        return 'w-[375px] max-w-[375px] mx-auto shadow-2xl rounded-2xl border-4 border-slate-700 dark:border-slate-600 bg-slate-50 dark:bg-slate-925 p-3 overflow-x-hidden';
      case '768':
        return 'w-[768px] max-w-[768px] mx-auto shadow-2xl rounded-2xl border-4 border-slate-700 dark:border-slate-600 bg-slate-50 dark:bg-slate-925 p-4 overflow-x-hidden';
      case '1440':
        return 'w-[1440px] max-w-full mx-auto shadow-2xl rounded-2xl border-2 border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-925 p-6 overflow-x-hidden';
      case 'fluid':
      default:
        return 'w-full max-w-7xl mx-auto p-2 sm:p-6';
    }
  };

  return (
    <div
      data-testid="ats-storybook-demo"
      className="space-y-6 w-full max-w-full overflow-x-hidden py-4"
    >
      {/* Storybook Top Control Bar */}
      <div className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-black uppercase tracking-wider text-brand-600 dark:text-brand-400 bg-brand-50 dark:bg-brand-950/60 px-2.5 py-0.5 rounded-full border border-brand-200 dark:border-brand-800">
                Storybook Component Playground
              </span>
              <span className="text-2xs font-mono text-slate-400">FR-003 Visual Testbench</span>
            </div>
            <h2 className="text-xl font-black text-slate-900 dark:text-slate-100 tracking-tight">
              ATS Score & Skill-Gap Component Studio
            </h2>
          </div>

          {/* Quick Actions: JSON & Reset */}
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              icon={<Code2 className="w-3.5 h-3.5" />}
              onClick={() => setShowJsonInspector(!showJsonInspector)}
            >
              {showJsonInspector ? 'Hide Contract JSON' : 'Inspect JSON'}
            </Button>
            <Button
              variant="secondary"
              size="sm"
              icon={<RefreshCw className="w-3.5 h-3.5" />}
              onClick={() => {
                setComponentState('success');
                setActiveFixtureKey('good');
                setViewport('fluid');
              }}
            >
              Reset Playground
            </Button>
          </div>
        </div>

        {/* Studio Controls Matrix */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-3 border-t border-slate-100 dark:border-slate-800">
          {/* 1. Viewport Resizer: 375px, 768px, 1440px, Fluid */}
          <div className="space-y-1.5">
            <span className="text-2xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1">
              <Sliders className="w-3 h-3" />
              Viewport Device Frame:
            </span>
            <div
              role="group"
              aria-label="Responsive Viewport Select"
              className="grid grid-cols-4 gap-1 p-1 bg-slate-100 dark:bg-slate-800 rounded-lg text-xs"
            >
              <button
                type="button"
                aria-pressed={viewport === '375'}
                onClick={() => setViewport('375')}
                className={`py-1 px-1.5 rounded flex items-center justify-center gap-1 font-semibold transition-colors ${
                  viewport === '375'
                    ? 'bg-white dark:bg-slate-700 text-brand-600 dark:text-brand-300 shadow-xs'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
                }`}
              >
                <Smartphone className="w-3.5 h-3.5" />
                <span>375px</span>
              </button>
              <button
                type="button"
                aria-pressed={viewport === '768'}
                onClick={() => setViewport('768')}
                className={`py-1 px-1.5 rounded flex items-center justify-center gap-1 font-semibold transition-colors ${
                  viewport === '768'
                    ? 'bg-white dark:bg-slate-700 text-brand-600 dark:text-brand-300 shadow-xs'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
                }`}
              >
                <Tablet className="w-3.5 h-3.5" />
                <span>768px</span>
              </button>
              <button
                type="button"
                aria-pressed={viewport === '1440'}
                onClick={() => setViewport('1440')}
                className={`py-1 px-1.5 rounded flex items-center justify-center gap-1 font-semibold transition-colors ${
                  viewport === '1440'
                    ? 'bg-white dark:bg-slate-700 text-brand-600 dark:text-brand-300 shadow-xs'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
                }`}
              >
                <Monitor className="w-3.5 h-3.5" />
                <span>1440px</span>
              </button>
              <button
                type="button"
                aria-pressed={viewport === 'fluid'}
                onClick={() => setViewport('fluid')}
                className={`py-1 px-1.5 rounded flex items-center justify-center gap-1 font-semibold transition-colors ${
                  viewport === 'fluid'
                    ? 'bg-white dark:bg-slate-700 text-brand-600 dark:text-brand-300 shadow-xs'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
                }`}
              >
                <Maximize2 className="w-3.5 h-3.5" />
                <span>Fluid</span>
              </button>
            </div>
          </div>

          {/* 2. Score Fixture Selector (Poor, Fair, Good, Excellent, No Gaps) */}
          <div className="space-y-1.5">
            <span className="text-2xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1">
              <Award className="w-3 h-3" />
              Score Tier Fixture:
            </span>
            <div
              role="group"
              aria-label="Score Fixture Select"
              className="grid grid-cols-5 gap-1 p-1 bg-slate-100 dark:bg-slate-800 rounded-lg text-2xs"
            >
              {Object.entries(fixtureMap).map(([key, item]) => (
                <button
                  key={key}
                  type="button"
                  aria-pressed={activeFixtureKey === key}
                  onClick={() => {
                    setActiveFixtureKey(key);
                    if (componentState !== 'success') setComponentState('success');
                  }}
                  className={`py-1 px-1 rounded text-center font-semibold capitalize truncate transition-colors ${
                    activeFixtureKey === key
                      ? 'bg-white dark:bg-slate-700 text-brand-600 dark:text-brand-300 shadow-xs'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
                  }`}
                >
                  {key}
                </button>
              ))}
            </div>
          </div>

          {/* 3. Component State Selector */}
          <div className="space-y-1.5">
            <span className="text-2xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1">
              <Eye className="w-3 h-3" />
              Operational State:
            </span>
            <div
              role="group"
              aria-label="State Select"
              className="grid grid-cols-4 gap-1 p-1 bg-slate-100 dark:bg-slate-800 rounded-lg text-xs"
            >
              {['success', 'loading', 'empty', 'error'].map((st) => (
                <button
                  key={st}
                  type="button"
                  aria-pressed={componentState === st}
                  onClick={() => setComponentState(st)}
                  className={`py-1 px-1.5 rounded capitalize text-center font-semibold transition-colors ${
                    componentState === st
                      ? 'bg-white dark:bg-slate-700 text-brand-600 dark:text-brand-300 shadow-xs'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
                  }`}
                >
                  {st}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Expandable JSON Inspector */}
        {showJsonInspector && (
          <div className="mt-3 p-4 rounded-xl bg-slate-950 text-slate-100 border border-slate-800 space-y-2 animate-fade-in">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono font-bold text-brand-400 flex items-center gap-1.5">
                <Code2 className="w-4 h-4" />
                ScoreResult JSON Contract Payload ({activeFixture.name}):
              </span>
              <button
                type="button"
                onClick={handleCopyJson}
                className="inline-flex items-center gap-1 text-2xs font-mono font-bold text-slate-300 hover:text-white px-2 py-1 rounded bg-slate-800 hover:bg-slate-700"
              >
                {copiedJson ? (
                  <>
                    <Check className="w-3 h-3 text-emerald-400" />
                    <span>Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3 h-3" />
                    <span>Copy Contract</span>
                  </>
                )}
              </button>
            </div>
            <pre className="text-2xs font-mono overflow-x-auto max-h-60 p-2 rounded bg-slate-900/80 border border-slate-800 text-emerald-400">
              {JSON.stringify(activeFixture.data, null, 2)}
            </pre>
          </div>
        )}
      </div>

      {/* Rendered Viewport Frame */}
      <div className="w-full flex justify-center overflow-x-auto pb-8">
        <div className={getViewportWidthClass()}>
          {viewport !== 'fluid' && (
            <div className="mb-3 pb-2 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between text-2xs text-slate-500 font-mono">
              <span>DEVICE VIEWPORT: {viewport}px</span>
              <Badge variant="neutral" size="sm">
                No Horizontal Scroll
              </Badge>
            </div>
          )}

          {/* Actual AtsSkillGapScreen Component */}
          <AtsSkillGapScreen
            state={componentState}
            data={activeFixture.data}
            onRetry={() => setComponentState('success')}
          />
        </div>
      </div>
    </div>
  );
}
