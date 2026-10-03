import React, { useState } from 'react';
import {
  Sparkles,
  Layers,
  Layout,
  Sun,
  Moon,
  Monitor,
  Tablet,
  Smartphone,
  CheckCircle2,
  AlertTriangle,
  Upload,
  UserCheck,
  Award,
  Code2,
  FileText,
  Info,
  ExternalLink,
  RefreshCw,
  Bell,
  HelpCircle,
  TrendingUp,
  Cpu
} from 'lucide-react';

// UI Library Components
import Button from './ui/Button';
import Input from './ui/Input';
import Card, { CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from './ui/Card';
import Badge from './ui/Badge';
import Modal from './ui/Modal';
import Tabs from './ui/Tabs';
import ProgressBar from './ui/ProgressBar';
import Spinner from './ui/Spinner';
import Skeleton from './ui/Skeleton';
import { useToast } from './ui/Toast';
import EmptyState from './ui/EmptyState';
import ErrorState from './ui/ErrorState';
import ScoreRing from './ui/ScoreRing';

// Screens
import LoginRegisterScreen from './screens/LoginRegisterScreen';
import ResumeUploadScreen from './screens/ResumeUploadScreen';
import ParsingStatusScreen from './screens/ParsingStatusScreen';
import AtsSkillGapScreen from './screens/AtsSkillGapScreen';
import MarketFitSalaryScreen from './screens/MarketFitSalaryScreen';
import LearningRoadmapScreen from './screens/LearningRoadmapScreen';
import RecruiterCritiqueScreen from './screens/RecruiterCritiqueScreen';

// Mock Data
import {
  mockParsedResume,
  mockScoreResult,
  mockMarketFit,
  mockRoadmap,
  mockCritique,
  mockApiError
} from '../data/mockData';

export default function DemoPage() {
  const toast = useToast();

  // App Navigation & Controls
  const [activeMainTab, setActiveMainTab] = useState('components'); // 'components' | 'screens' | 'specs'
  const [selectedScreen, setSelectedScreen] = useState('ats'); // 7 screens
  const [screenState, setScreenState] = useState('success'); // 'success' | 'loading' | 'empty' | 'error'
  const [deviceViewport, setDeviceViewport] = useState('fluid'); // 'fluid' | 'desktop' (1440) | 'tablet' (768) | 'mobile' (375)
  const [isDarkMode, setIsDarkMode] = useState(false);

  // Component Demo States
  const [demoModalOpen, setDemoModalOpen] = useState(false);
  const [demoInputVal, setDemoInputVal] = useState('Aarav Sharma');
  const [demoInputError, setDemoInputError] = useState('');
  const [demoActiveTab, setDemoActiveTab] = useState('overview');
  const [buttonLoading, setButtonLoading] = useState(false);
  const [progressVal, setProgressVal] = useState(82);
  const [chromaError, setChromaError] = useState(false);
  const [isReconnecting, setIsReconnecting] = useState(false);

  const handleRetryChroma = () => {
    setIsReconnecting(true);
    setTimeout(() => {
      setIsReconnecting(false);
      setChromaError(false);
      toast.success('ChromaDB Reconnected', 'Vector embedding microservice on port 8000 is healthy and operational.');
    }, 600);
  };

  const toggleDarkMode = () => {
    setIsDarkMode((prev) => {
      const next = !prev;
      if (next) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
      return next;
    });
  };

  const handleSimulateToast = (type) => {
    if (type === 'success') {
      toast.success('Resume Parsed Successfully', 'Extracted 6 skills and 3 experience nodes in 1.4s.');
    } else if (type === 'error') {
      toast.error('API Limit Reached', 'LinkedIn live data rate limit exceeded. Switched to fallback index.');
    } else if (type === 'warning') {
      toast.warning('Skill Gap Alert', 'MLOps & Kubernetes are missing for Data Scientist role.');
    } else {
      toast.info('SDG 4 Project Active', 'CareerLens is running on SKIT Jaipur cloud cluster.');
    }
  };

  const mainNavigationTabs = [
    { id: 'components', label: 'Reusable UI Library', icon: <Layers className="w-4 h-4" />, badge: '13 Components' },
    { id: 'screens', label: 'Screen Wireframes & Live Flow', icon: <Layout className="w-4 h-4" />, badge: '7 Screens' },
    { id: 'specs', label: 'Figma Design Tokens & Specs', icon: <Code2 className="w-4 h-4" /> },
  ];

  const screenNavigation = [
    { id: 'login', label: '1. Login / Register' },
    { id: 'upload', label: '2. Resume Upload' },
    { id: 'parsing', label: '3. Parsing Status' },
    { id: 'ats', label: '4. ATS Score & Skill Gap' },
    { id: 'market', label: '5. Market-Fit & Salary' },
    { id: 'roadmap', label: '6. Learning Roadmap' },
    { id: 'critique', label: '7. Recruiter Critique' },
  ];

  const getViewportContainerClass = () => {
    if (deviceViewport === 'mobile') return 'max-w-[375px] mx-auto border-x-4 border-slate-400 dark:border-slate-700 shadow-2xl rounded-3xl p-3 bg-slate-50 dark:bg-slate-900 my-4 transition-all duration-300';
    if (deviceViewport === 'tablet') return 'max-w-[768px] mx-auto border-x-4 border-slate-400 dark:border-slate-700 shadow-2xl rounded-2xl p-4 bg-slate-50 dark:bg-slate-900 my-4 transition-all duration-300';
    if (deviceViewport === 'desktop') return 'max-w-[1440px] mx-auto border border-slate-300 dark:border-slate-700 shadow-xl rounded-xl p-6 bg-slate-50 dark:bg-slate-900 my-4 transition-all duration-300';
    return 'w-full';
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col font-sans transition-colors duration-200">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-40 bg-white/85 dark:bg-slate-900/85 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 px-4 sm:px-8 py-3.5">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
          {/* Brand Identity */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-500 text-white flex items-center justify-center font-extrabold text-lg shadow-brand-500/25 shadow-lg">
              CL
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-extrabold tracking-tight text-slate-900 dark:text-white">
                  CareerLens
                </h1>
                <Badge variant="primary" size="sm" className="hidden sm:inline-flex">
                  SKIT Jaipur
                </Badge>
                <Badge variant="success" size="sm" dot className="hidden sm:inline-flex">
                  SDG 4
                </Badge>
              </div>
              <p className="text-2xs text-slate-500 dark:text-slate-400">
                Final Year Project
              </p>
            </div>
          </div>

          {/* Navigation & Controls */}
          <div className="flex flex-wrap items-center gap-3">
            <Tabs
              tabs={mainNavigationTabs}
              activeTab={activeMainTab}
              onChange={setActiveMainTab}
              variant="pills"
            />

            <div className="h-6 w-px bg-slate-200 dark:bg-slate-800 hidden lg:block" />

            {/* Dark Mode Toggle */}
            <button
              type="button"
              onClick={toggleDarkMode}
              aria-label="Toggle dark mode"
              className="p-2 rounded-lg border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            >
              {isDarkMode ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-indigo-600" />}
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-8 py-6">
        {/* ========================================================================= */}
        {/* TAB 1: REUSABLE UI LIBRARY SHOWCASE */}
        {/* ========================================================================= */}
        {activeMainTab === 'components' && (
          <div className="space-y-10 animate-in fade-in duration-200">
            {/* Header intro */}
            <div>
              <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2">
                Reusable UI Library Showcase
                <Badge variant="role" size="sm">React + Tailwind CSS</Badge>
              </h2>
              <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
                Fully accessible components with ARIA roles, keyboard navigation, focus rings, dark mode tokens, and all states.
              </p>
            </div>

            {/* 1. Buttons */}
            <section className="space-y-4">
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2 pb-2 border-b border-slate-200 dark:border-slate-800">
                1. Button Component
                <span className="text-xs font-normal text-slate-400">(Variants, Sizes, Icons, Loading, Disabled)</span>
              </h3>
              <div className="flex flex-wrap items-center gap-3">
                <Button variant="primary" size="md">Primary Button</Button>
                <Button variant="secondary" size="md">Secondary</Button>
                <Button variant="outline" size="md">Outline</Button>
                <Button variant="ghost" size="md">Ghost</Button>
                <Button variant="danger" size="md">Danger Action</Button>
                <Button
                  variant="primary"
                  isLoading={buttonLoading}
                  onClick={() => {
                    setButtonLoading(true);
                    setTimeout(() => setButtonLoading(false), 2000);
                  }}
                  icon={<Sparkles className="w-4 h-4" />}
                >
                  Click For Loading
                </Button>
                <Button variant="outline" disabled>Disabled State</Button>
                <Button variant="primary" size="sm">Small (sm)</Button>
                <Button variant="primary" size="lg">Large (lg)</Button>
              </div>
            </section>

            {/* 2. Form Inputs */}
            <section className="space-y-4">
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2 pb-2 border-b border-slate-200 dark:border-slate-800">
                2. Input Component
                <span className="text-xs font-normal text-slate-400">(Labels, Helper Text, Error Validation, Icons, Focus Rings)</span>
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                <Input
                  label="Candidate Name"
                  value={demoInputVal}
                  onChange={(e) => setDemoInputVal(e.target.value)}
                  placeholder="e.g. Aarav Sharma"
                  helperText="Official university enrolled name"
                  leadingIcon={<UserCheck className="w-4 h-4" />}
                  required
                />
                <Input
                  label="Target Role (Validated)"
                  value="Data Scientist / ML"
                  error={demoInputError || 'Minimum 3 years experience required for Senior role'}
                  onChange={() => {}}
                  placeholder="e.g. Data Scientist"
                />
                <Input
                  label="Disabled API Key"
                  value="sk_live_skit_2026_ds_04"
                  disabled
                  helperText="Provisioned via Node.js auth-service"
                />
              </div>
            </section>

            {/* 3. Cards */}
            <section className="space-y-4">
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2 pb-2 border-b border-slate-200 dark:border-slate-800">
                3. Card System
                <span className="text-xs font-normal text-slate-400">(Default, Elevated, Outline, Interactive with Keyboard Enter/Space)</span>
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card variant="default">
                  <CardHeader>
                    <CardTitle>Default Surface Card</CardTitle>
                    <CardDescription>Clean boundary with subtle border & background</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-xs text-slate-600 dark:text-slate-400">
                      Ideal for structured listings, candidate profiles, and passive analytics.
                    </p>
                  </CardContent>
                  <CardFooter>
                    <span>Status: Active</span>
                    <Badge variant="success" size="sm">Verified</Badge>
                  </CardFooter>
                </Card>

                <Card variant="elevated">
                  <CardHeader>
                    <CardTitle>Elevated Shadow Card</CardTitle>
                    <CardDescription>Soft diffused shadow elevation</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-xs text-slate-600 dark:text-slate-400">
                      Used for primary KPI metrics, ATS score rings, and high-impact summaries.
                    </p>
                  </CardContent>
                  <CardFooter>
                    <span>Elevation: 4px</span>
                    <Badge variant="primary" size="sm">KPI</Badge>
                  </CardFooter>
                </Card>

                <Card
                  variant="interactive"
                  onClick={() => toast.info('Card Clicked', 'Keyboard Enter/Space or mouse click detected!')}
                >
                  <CardHeader>
                    <CardTitle className="text-brand-600 dark:text-brand-400">
                      Interactive Card
                    </CardTitle>
                    <CardDescription>Hover lift, cursor pointer & focus ring</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-xs text-slate-600 dark:text-slate-400">
                      Click or press Enter/Space on this card to trigger action feedback.
                    </p>
                  </CardContent>
                  <CardFooter>
                    <span className="text-brand-600 font-semibold text-2xs">Press Enter to select</span>
                    <ExternalLink className="w-3.5 h-3.5 text-brand-600" />
                  </CardFooter>
                </Card>
              </div>
            </section>

            {/* 4. Badges & ATS Score Color Thresholds */}
            <section className="space-y-4">
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2 pb-2 border-b border-slate-200 dark:border-slate-800">
                4. Badge & ATS Score Color Thresholds
                <span className="text-xs font-normal text-slate-400">(Red: 0-49, Amber: 50-74, Green: 75-100)</span>
              </h3>
              <div className="flex flex-wrap items-center gap-3">
                <Badge variant="default">Default</Badge>
                <Badge variant="primary">Primary Brand</Badge>
                <Badge variant="success" dot>Success (dot)</Badge>
                <Badge variant="warning">Warning / Alert</Badge>
                <Badge variant="danger">Danger / Critical</Badge>
                <Badge variant="info">Info Notice</Badge>
                <Badge variant="role">Role / SDG 4</Badge>
                <div className="h-5 w-px bg-slate-300 dark:bg-slate-700 mx-2" />
                <Badge score={42}>Score 42 (Auto Red)</Badge>
                <Badge score={68}>Score 68 (Auto Amber)</Badge>
                <Badge score={92}>Score 92 (Auto Green)</Badge>
              </div>
            </section>

            {/* 5. ScoreRing & ProgressBars */}
            <section className="space-y-4">
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2 pb-2 border-b border-slate-200 dark:border-slate-800">
                5. ScoreRing & ProgressBar System
                <span className="text-xs font-normal text-slate-400">(Radial SVG meter + dynamic linear progress)</span>
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
                <Card variant="default" className="p-6 flex flex-col items-center text-center">
                  <ScoreRing score={45} size={120} label="Critical Score" sublabel="Red Zone (<50)" />
                </Card>
                <Card variant="default" className="p-6 flex flex-col items-center text-center">
                  <ScoreRing score={67} size={120} label="Moderate Score" sublabel="Amber Zone (50-74)" />
                </Card>
                <Card variant="default" className="p-6 flex flex-col items-center text-center">
                  <ScoreRing score={88} size={120} label="Recruiter Ready" sublabel="Green Zone (75-100)" />
                </Card>
              </div>

              <div className="p-6 rounded-xl bg-white dark:bg-slate-850 border border-slate-200 dark:border-slate-800 space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-700 dark:text-slate-300">
                    Live Progress Control:
                  </span>
                  <div className="flex items-center gap-2">
                    <Button size="sm" variant="outline" onClick={() => setProgressVal(38)}>Red (38%)</Button>
                    <Button size="sm" variant="outline" onClick={() => setProgressVal(64)}>Amber (64%)</Button>
                    <Button size="sm" variant="outline" onClick={() => setProgressVal(88)}>Green (88%)</Button>
                  </div>
                </div>
                <ProgressBar value={progressVal} label="ATS Composite Index (Dynamic Threshold)" showValue variant="ats" size="md" />
                <ProgressBar value={75} label="Gradient Variant (Market Analytics)" showValue variant="gradient" size="sm" />
                <ProgressBar value={90} label="Striped Animated Processing Bar" showValue variant="primary" striped animated size="sm" />
              </div>
            </section>

            {/* 6. Tabs, Modals, Spinners, Skeletons, Toasts */}
            <section className="space-y-4">
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2 pb-2 border-b border-slate-200 dark:border-slate-800">
                6. Interactive Widgets: Modal, Tabs, Spinner, Skeleton, Toast
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Modal & Toast triggers */}
                <Card variant="default" className="p-5 space-y-4">
                  <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                    Accessible Modal & Toast Triggers
                  </h4>
                  <div className="flex flex-wrap gap-2.5">
                    <Button variant="primary" onClick={() => setDemoModalOpen(true)}>
                      Open Accessible Modal
                    </Button>
                    <Button variant="outline" onClick={() => handleSimulateToast('success')}>
                      Success Toast
                    </Button>
                    <Button variant="outline" onClick={() => handleSimulateToast('warning')}>
                      Warning Toast
                    </Button>
                    <Button variant="danger" onClick={() => handleSimulateToast('error')}>
                      Error Toast
                    </Button>
                  </div>
                </Card>

                {/* Spinners & Skeleton loading */}
                <Card variant="default" className="p-5 space-y-4">
                  <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                    Spinners & Skeleton Loaders
                  </h4>
                  <div className="flex items-center gap-4">
                    <Spinner size="xs" color="brand" />
                    <Spinner size="sm" color="ats-green" />
                    <Spinner size="md" color="ats-amber" />
                    <Spinner size="lg" color="ats-red" />
                  </div>
                  <div className="pt-2">
                    <Skeleton variant="text" width="60%" />
                    <Skeleton variant="text" width="85%" />
                  </div>
                </Card>
              </div>
            </section>

            {/* 7. EmptyState & ErrorState */}
            <section className="space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-slate-200 dark:border-slate-800">
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                  7. EmptyState & ErrorState (Contract Aligned)
                </h3>
                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant={chromaError ? 'primary' : 'outline'}
                    onClick={() => {
                      if (chromaError) {
                        handleRetryChroma();
                      } else {
                        setChromaError(true);
                        toast.warning('Simulated Error', 'Triggered CHROMA_VECTOR_DISCONNECTED demo state.');
                      }
                    }}
                  >
                    {chromaError ? 'Resolve Error State' : 'Test Error State Simulation'}
                  </Button>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <EmptyState
                  icon={FileText}
                  title="No Resumes Uploaded Yet"
                  description="Upload your PDF/DOCX to begin the multi-agent ATS evaluation."
                  action={{ label: "Upload Now", onClick: () => {} }}
                />

                {chromaError ? (
                  <ErrorState
                    error={{
                      code: 'CHROMA_VECTOR_DISCONNECTED',
                      message: 'ChromaDB vector embedding microservice timed out on port 8000. Check Docker container health.'
                    }}
                    onRetry={handleRetryChroma}
                    actionLabel={isReconnecting ? 'Reconnecting...' : 'Retry Connection'}
                  />
                ) : (
                  <div className="flex flex-col items-center justify-center text-center p-8 sm:p-10 rounded-2xl border border-emerald-200 dark:border-emerald-900/60 bg-emerald-50/40 dark:bg-emerald-950/20">
                    <div className="w-12 h-12 rounded-2xl bg-emerald-100 dark:bg-emerald-900/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mb-3.5 shadow-subtle">
                      <CheckCircle2 className="w-6 h-6" />
                    </div>

                    <span className="font-mono text-2xs uppercase tracking-wider px-2 py-0.5 rounded bg-emerald-200/60 dark:bg-emerald-900/80 text-emerald-800 dark:text-emerald-300 font-bold mb-2">
                      STATUS: 200_OK (PORT 8000)
                    </span>

                    <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 mb-1.5">
                      ChromaDB Vector Service Healthy
                    </h3>

                    <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 max-w-md mb-5 leading-relaxed">
                      Vector embedding microservice is active and responding. 384-dimensional cosine similarity index operational.
                    </p>

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setChromaError(true);
                        toast.warning('Simulated Error', 'Triggered CHROMA_VECTOR_DISCONNECTED test state.');
                      }}
                    >
                      Simulate Service Disconnect
                    </Button>
                  </div>
                )}
              </div>
            </section>
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 2: SCREEN WIREFRAMES & LIVE FLOW */}
        {/* ========================================================================= */}
        {activeMainTab === 'screens' && (
          <div className="space-y-6 animate-in fade-in duration-200">
            {/* Control Bar: Screen Picker + State Switcher + Viewport Switcher */}
            <div className="p-4 bg-white dark:bg-slate-850 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-subtle flex flex-col lg:flex-row lg:items-center justify-between gap-4">
              {/* Screen Picker */}
              <div className="flex-1">
                <label className="block text-2xs font-bold uppercase tracking-wider text-slate-400 mb-1.5">
                  Select Screen Wireframe
                </label>
                <div className="flex flex-wrap gap-1.5">
                  {screenNavigation.map((scr) => (
                    <button
                      key={scr.id}
                      type="button"
                      onClick={() => setSelectedScreen(scr.id)}
                      className={`text-xs px-2.5 py-1.5 rounded-lg font-medium transition-all ${
                        selectedScreen === scr.id
                          ? 'bg-brand-600 text-white font-bold shadow-xs'
                          : 'bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300'
                      }`}
                    >
                      {scr.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* State Handler Switcher */}
              <div>
                <label className="block text-2xs font-bold uppercase tracking-wider text-slate-400 mb-1.5">
                  Screen State
                </label>
                <div className="flex rounded-lg bg-slate-100 dark:bg-slate-800 p-1">
                  {['success', 'loading', 'empty', 'error'].map((st) => (
                    <button
                      key={st}
                      type="button"
                      onClick={() => setScreenState(st)}
                      className={`text-2xs px-2.5 py-1 rounded-md font-semibold capitalize transition-all ${
                        screenState === st
                          ? 'bg-white dark:bg-slate-900 text-brand-600 dark:text-brand-400 shadow-xs'
                          : 'text-slate-600 dark:text-slate-400'
                      }`}
                    >
                      {st}
                    </button>
                  ))}
                </div>
              </div>

              {/* Viewport Width Switcher */}
              <div>
                <label className="block text-2xs font-bold uppercase tracking-wider text-slate-400 mb-1.5">
                  Viewport Frame
                </label>
                <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 p-1 rounded-lg">
                  <button
                    type="button"
                    onClick={() => setDeviceViewport('fluid')}
                    title="Fluid 100% Responsive"
                    className={`p-1.5 rounded text-xs flex items-center gap-1 font-semibold ${
                      deviceViewport === 'fluid' ? 'bg-white dark:bg-slate-900 text-brand-600 shadow-xs' : 'text-slate-500'
                    }`}
                  >
                    Fluid
                  </button>
                  <button
                    type="button"
                    onClick={() => setDeviceViewport('desktop')}
                    title="Desktop 1440px"
                    className={`p-1.5 rounded text-xs flex items-center gap-1 font-semibold ${
                      deviceViewport === 'desktop' ? 'bg-white dark:bg-slate-900 text-brand-600 shadow-xs' : 'text-slate-500'
                    }`}
                  >
                    <Monitor className="w-3.5 h-3.5" /> 1440
                  </button>
                  <button
                    type="button"
                    onClick={() => setDeviceViewport('tablet')}
                    title="Tablet 768px"
                    className={`p-1.5 rounded text-xs flex items-center gap-1 font-semibold ${
                      deviceViewport === 'tablet' ? 'bg-white dark:bg-slate-900 text-brand-600 shadow-xs' : 'text-slate-500'
                    }`}
                  >
                    <Tablet className="w-3.5 h-3.5" /> 768
                  </button>
                  <button
                    type="button"
                    onClick={() => setDeviceViewport('mobile')}
                    title="Mobile 375px"
                    className={`p-1.5 rounded text-xs flex items-center gap-1 font-semibold ${
                      deviceViewport === 'mobile' ? 'bg-white dark:bg-slate-900 text-brand-600 shadow-xs' : 'text-slate-500'
                    }`}
                  >
                    <Smartphone className="w-3.5 h-3.5" /> 375
                  </button>
                </div>
              </div>
            </div>

            {/* Viewport Frame Container */}
            <div className={getViewportContainerClass()}>
              {selectedScreen === 'login' && (
                <LoginRegisterScreen
                  state={screenState}
                  onLoginSuccess={() => {
                    toast.success('Signed in', 'JWT token stored in secure cookie');
                    setSelectedScreen('upload');
                  }}
                />
              )}

              {selectedScreen === 'upload' && (
                <ResumeUploadScreen
                  state={screenState}
                  onUploadComplete={() => {
                    toast.success('Upload Finished', 'Initiating Hugging Face NER pipeline');
                    setSelectedScreen('parsing');
                  }}
                />
              )}

              {selectedScreen === 'parsing' && (
                <ParsingStatusScreen state={screenState} data={mockParsedResume} />
              )}

              {selectedScreen === 'ats' && (
                <AtsSkillGapScreen state={screenState} data={mockScoreResult} />
              )}

              {selectedScreen === 'market' && (
                <MarketFitSalaryScreen state={screenState} data={mockMarketFit} />
              )}

              {selectedScreen === 'roadmap' && (
                <LearningRoadmapScreen state={screenState} data={mockRoadmap} />
              )}

              {selectedScreen === 'critique' && (
                <RecruiterCritiqueScreen state={screenState} data={mockCritique} />
              )}
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 3: FIGMA DESIGN TOKENS & SPECS */}
        {/* ========================================================================= */}
        {activeMainTab === 'specs' && (
          <div className="space-y-8 animate-in fade-in duration-200">
            <div>
              <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2">
                Figma Setup Guide & Design Token Matrix
                <Badge variant="role" size="sm">Design System v2.4</Badge>
              </h2>
              <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
                Precise layout grids, typography scales, color hex values, and component variant maps to recreate seamlessly in Figma.
              </p>
            </div>

            {/* 1. Layout Grids */}
            <Card variant="default">
              <CardHeader>
                <CardTitle>1. Responsive Figma Layout Grid Specifications</CardTitle>
                <CardDescription>Exact frame sizes, column counts, margins, and gutters for Figma auto-layout</CardDescription>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                <table className="w-full text-xs text-left border-collapse">
                  <thead>
                    <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-400 font-mono">
                      <th className="py-2.5 pr-4">Breakpoint</th>
                      <th className="py-2.5 px-4">Frame Width</th>
                      <th className="py-2.5 px-4">Columns</th>
                      <th className="py-2.5 px-4">Margin (Left/Right)</th>
                      <th className="py-2.5 px-4">Gutter</th>
                      <th className="py-2.5 pl-4">Target Device Use</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300">
                    <tr>
                      <td className="py-2.5 pr-4 font-bold text-brand-600 dark:text-brand-400">Desktop</td>
                      <td className="py-2.5 px-4 font-mono font-semibold">1440px (H: 1024px)</td>
                      <td className="py-2.5 px-4">12 Columns</td>
                      <td className="py-2.5 px-4 font-mono">72px</td>
                      <td className="py-2.5 px-4 font-mono">24px</td>
                      <td className="py-2.5 pl-4">Standard 1080p/MacBook display dashboard</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 pr-4 font-bold text-brand-600 dark:text-brand-400">Tablet</td>
                      <td className="py-2.5 px-4 font-mono font-semibold">768px (H: 1024px)</td>
                      <td className="py-2.5 px-4">8 Columns</td>
                      <td className="py-2.5 px-4 font-mono">32px</td>
                      <td className="py-2.5 px-4 font-mono">16px</td>
                      <td className="py-2.5 pl-4">iPad portrait / medium tablets</td>
                    </tr>
                    <tr>
                      <td className="py-2.5 pr-4 font-bold text-brand-600 dark:text-brand-400">Mobile</td>
                      <td className="py-2.5 px-4 font-mono font-semibold">375px (H: 812px)</td>
                      <td className="py-2.5 px-4">4 Columns</td>
                      <td className="py-2.5 px-4 font-mono">16px</td>
                      <td className="py-2.5 px-4 font-mono">12px</td>
                      <td className="py-2.5 pl-4">iPhone 13 / 14 / modern Android viewports</td>
                    </tr>
                  </tbody>
                </table>
              </CardContent>
            </Card>

            {/* 2. Color Tokens */}
            <Card variant="default">
              <CardHeader>
                <CardTitle>2. Complete Color Palette (Hex & Semantic Application)</CardTitle>
                <CardDescription>Tailwind extended tokens, ATS threshold colors, and light/dark mode pairs</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3 text-center">
                  <div className="p-3 rounded-lg bg-indigo-600 text-white space-y-1">
                    <span className="text-2xs font-mono">#4F46E5</span>
                    <p className="text-xs font-bold">Brand Primary</p>
                  </div>
                  <div className="p-3 rounded-lg bg-emerald-500 text-white space-y-1">
                    <span className="text-2xs font-mono">#10B981</span>
                    <p className="text-xs font-bold">ATS Green (75-100)</p>
                  </div>
                  <div className="p-3 rounded-lg bg-amber-500 text-white space-y-1">
                    <span className="text-2xs font-mono">#F59E0B</span>
                    <p className="text-xs font-bold">ATS Amber (50-74)</p>
                  </div>
                  <div className="p-3 rounded-lg bg-rose-500 text-white space-y-1">
                    <span className="text-2xs font-mono">#EF4444</span>
                    <p className="text-xs font-bold">ATS Red (0-49)</p>
                  </div>
                  <div className="p-3 rounded-lg bg-teal-600 text-white space-y-1">
                    <span className="text-2xs font-mono">#0D9488</span>
                    <p className="text-xs font-bold">Market LPA Teal</p>
                  </div>
                  <div className="p-3 rounded-lg bg-purple-600 text-white space-y-1">
                    <span className="text-2xs font-mono">#8B5CF6</span>
                    <p className="text-xs font-bold">Recruiter Agent</p>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-2 text-xs">
                  <p className="font-bold text-slate-900 dark:text-slate-100">Surface Neutrals:</p>
                  <p className="text-slate-600 dark:text-slate-400">
                    • Light Mode Canvas: <span className="font-mono text-brand-600 font-semibold">#F8FAFC (slate-50)</span> | Surface: <span className="font-mono text-brand-600 font-semibold">#FFFFFF</span> | Border: <span className="font-mono text-brand-600 font-semibold">#E2E8F0 (slate-200)</span>
                  </p>
                  <p className="text-slate-600 dark:text-slate-400">
                    • Dark Mode Canvas: <span className="font-mono text-brand-600 font-semibold">#0B1120 (slate-925)</span> | Surface: <span className="font-mono text-brand-600 font-semibold">#151F32 (slate-850)</span> | Border: <span className="font-mono text-brand-600 font-semibold">#1E293B (slate-800)</span>
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* 3. Figma Page Structure & Naming Conventions */}
            <Card variant="default">
              <CardHeader>
                <CardTitle>3. Recommended Figma File & Page Organization</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-xs text-slate-700 dark:text-slate-300">
                <div className="p-3 rounded-lg bg-slate-100 dark:bg-slate-800/60 font-mono space-y-1">
                  <p className="text-brand-600 font-bold">📁 Page 1: 📌 Cover & Project Info (Final Year Project, SDG 4)</p>
                  <p className="text-indigo-600 font-bold">📁 Page 2: 🎨 Styles & Design Tokens (Colors, Typography, Shadows, Grids)</p>
                  <p className="text-emerald-600 font-bold">📁 Page 3: 🧩 Components Library (Buttons, Inputs, Cards, Rings, Modals)</p>
                  <p className="text-purple-600 font-bold">📁 Page 4: 📱 Wireframes (Desktop 1440, Tablet 768, Mobile 375)</p>
                  <p className="text-amber-600 font-bold">📁 Page 5: ✨ Final Hi-Fi Screens (All 7 screens in Light & Dark modes)</p>
                  <p className="text-rose-600 font-bold">📁 Page 6: 🔄 Prototype Flows (Upload -&gt; Parse -&gt; ATS -&gt; Critique)</p>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </main>

      {/* Accessible Demo Modal */}
      <Modal
        isOpen={demoModalOpen}
        onClose={() => setDemoModalOpen(false)}
        title="Candidate Skill Verification Modal"
        description="Verify implicit skill detection before pushing embeddings to ChromaDB."
        size="md"
        footer={
          <>
            <Button variant="ghost" onClick={() => setDemoModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={() => {
                setDemoModalOpen(false);
                toast.success('Skill Verified', 'Added Docker to verified implicit taxonomy.');
              }}
            >
              Confirm Verification
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div className="p-3 rounded-lg bg-brand-50 dark:bg-brand-950/60 border border-brand-200 dark:border-brand-800 text-xs text-brand-900 dark:text-brand-200">
            <strong>Implicit Skill:</strong> Docker (Confidence: 86%)
            <p className="mt-1 opacity-80">Evidence: "Containerized multi-service architectures with min 8GB RAM specs"</p>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-400">
            Closing this modal with the Escape key or clicking outside the backdrop works smoothly and locks background scrolling.
          </p>
        </div>
      </Modal>

      {/* Global Footer */}
      <footer className="mt-auto border-t border-slate-200 dark:border-slate-800 py-6 px-4 sm:px-8 text-center text-xs text-slate-500 dark:text-slate-400">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
          <p>
            CareerLens: Smart Resume & Market Analysis System • Final Year Project
          </p>
          <div className="flex items-center gap-2 text-2xs text-slate-400">
            <span>SDG 4: Quality Education</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
