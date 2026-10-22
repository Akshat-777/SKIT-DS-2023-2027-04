import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { getAtsScoreTier, SCORE_TIERS } from '../utils/scoreThresholds';
import ScoreRing from '../components/ui/ScoreRing';
import BreakdownCard from '../components/score/BreakdownCard';
import BreakdownGrid from '../components/score/BreakdownGrid';
import AtsSkillGapScreen from '../components/screens/AtsSkillGapScreen';
import AtsStorybookDemo from '../components/demo/AtsStorybookDemo';
import {
  mockScoreGood,
  mockScorePoor,
  mockScoreFair,
  mockScoreExcellent,
  mockScoreNoGaps,
} from '../data/mockScoreFixtures';

describe('ATS Score Thresholds & Classification', () => {
  it('correctly classifies score < 50 as Poor', () => {
    const tier = getAtsScoreTier(42);
    expect(tier.tier).toBe(SCORE_TIERS.POOR);
    expect(tier.label).toBe('Poor');
    expect(tier.color).toBe('#EF4444');
    expect(tier.badgeVariant).toBe('danger');
  });

  it('correctly classifies score between 50 and 69 as Fair', () => {
    const tier = getAtsScoreTier(64);
    expect(tier.tier).toBe(SCORE_TIERS.FAIR);
    expect(tier.label).toBe('Fair');
    expect(tier.color).toBe('#F59E0B');
    expect(tier.badgeVariant).toBe('warning');
  });

  it('correctly classifies score between 70 and 84 as Good', () => {
    const tier = getAtsScoreTier(82);
    expect(tier.tier).toBe(SCORE_TIERS.GOOD);
    expect(tier.label).toBe('Good');
    expect(tier.color).toBe('#3B82F6');
    expect(tier.badgeVariant).toBe('primary');
  });

  it('correctly classifies score >= 85 as Excellent', () => {
    const tier = getAtsScoreTier(94);
    expect(tier.tier).toBe(SCORE_TIERS.EXCELLENT);
    expect(tier.label).toBe('Excellent');
    expect(tier.color).toBe('#10B981');
    expect(tier.badgeVariant).toBe('success');
  });

  it('handles boundary conditions: 0, 49, 50, 69, 70, 84, 85, 100', () => {
    expect(getAtsScoreTier(0).tier).toBe(SCORE_TIERS.POOR);
    expect(getAtsScoreTier(49).tier).toBe(SCORE_TIERS.POOR);
    expect(getAtsScoreTier(50).tier).toBe(SCORE_TIERS.FAIR);
    expect(getAtsScoreTier(69).tier).toBe(SCORE_TIERS.FAIR);
    expect(getAtsScoreTier(70).tier).toBe(SCORE_TIERS.GOOD);
    expect(getAtsScoreTier(84).tier).toBe(SCORE_TIERS.GOOD);
    expect(getAtsScoreTier(85).tier).toBe(SCORE_TIERS.EXCELLENT);
    expect(getAtsScoreTier(100).tier).toBe(SCORE_TIERS.EXCELLENT);
  });
});

describe('ScoreRing Component', () => {
  it('renders circular score ring with accessible role="meter" and aria values', () => {
    render(<ScoreRing score={82} label="Overall ATS Fit Score" showTierLegend={true} />);

    const meter = screen.getByRole('meter', { name: 'Overall ATS Fit Score' });
    expect(meter).toBeInTheDocument();
    expect(meter).toHaveAttribute('aria-valuenow', '82');
    expect(meter).toHaveAttribute('aria-valuemin', '0');
    expect(meter).toHaveAttribute('aria-valuemax', '100');
    expect(meter.getAttribute('aria-valuetext')).toContain('Good');

    // Color is not the only signal: text tier badge is rendered
    expect(screen.getByTestId('score-tier-badge')).toHaveTextContent('Good');
    expect(screen.getByTestId('score-value')).toHaveTextContent('82');
  });

  it('renders Poor tier threshold badge for score 42', () => {
    render(<ScoreRing score={42} />);
    expect(screen.getByTestId('score-tier-badge')).toHaveTextContent('Poor');
  });

  it('renders Excellent tier threshold badge for score 95', () => {
    render(<ScoreRing score={95} />);
    expect(screen.getByTestId('score-tier-badge')).toHaveTextContent('Excellent');
  });
});

describe('BreakdownCard & BreakdownGrid', () => {
  it('renders a breakdown metric card with title, score, mini progress bar, tooltip, and improve hint', () => {
    render(<BreakdownCard metricKey="keyword_match" score={88} />);

    expect(screen.getByText('Keyword Match')).toBeInTheDocument();
    expect(screen.getByTestId('score-value-keyword_match')).toHaveTextContent('88%');
    expect(screen.getByTestId('tier-badge-keyword_match')).toHaveTextContent('Excellent');

    // Mini progress bar with ARIA attributes
    const progressBar = screen.getByRole('progressbar', { name: 'Keyword Match progress' });
    expect(progressBar).toBeInTheDocument();
    expect(progressBar).toHaveAttribute('aria-valuenow', '88');

    // Tooltip trigger
    const tooltipTrigger = screen.getByRole('button', {
      name: 'Plain-English explanation for Keyword Match',
    });
    expect(tooltipTrigger).toBeInTheDocument();
    fireEvent.click(tooltipTrigger);
    expect(screen.getByRole('tooltip')).toBeInTheDocument();
    expect(screen.getByText(/Measures exact and synonymous matches/i)).toBeInTheDocument();

    // "How to improve this" expandable hint
    const improveBtn = screen.getByRole('button', { name: /How to improve this/i });
    expect(improveBtn).toBeInTheDocument();
    fireEvent.click(improveBtn);
    expect(screen.getByTestId('improve-hint-keyword_match')).toBeInTheDocument();
    expect(screen.getByText(/Add missing target technologies/i)).toBeInTheDocument();
  });

  it('renders all 6 breakdown metric cards in BreakdownGrid', () => {
    render(<BreakdownGrid breakdown={mockScoreGood.breakdown} />);

    expect(screen.getByTestId('breakdown-card-keyword_match')).toBeInTheDocument();
    expect(screen.getByTestId('breakdown-card-semantic_similarity')).toBeInTheDocument();
    expect(screen.getByTestId('breakdown-card-section_completeness')).toBeInTheDocument();
    expect(screen.getByTestId('breakdown-card-formatting')).toBeInTheDocument();
    expect(screen.getByTestId('breakdown-card-experience_relevance')).toBeInTheDocument();
    expect(screen.getByTestId('breakdown-card-quantified_impact')).toBeInTheDocument();
  });
});

describe('AtsSkillGapScreen Component Flow & Interactions', () => {
  it('renders correctly from mockScoreGood fixture', () => {
    render(<AtsSkillGapScreen state="success" data={mockScoreGood} />);

    // Screen container
    expect(screen.getByTestId('ats-skill-gap-screen')).toBeInTheDocument();

    // Check heading
    expect(screen.getByText(/ATS Score Cards & Skill-Gap Analysis/i)).toBeInTheDocument();

    // Check missing skills rendered
    expect(screen.getByText(/MLOps \(MLflow \/ Kubeflow\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Kubernetes Orchestration/i)).toBeInTheDocument();

    // Check trending skills rendered
    expect(screen.getByText(/RAG Architecture & Embeddings/i)).toBeInTheDocument();
    expect(screen.getByText(/LangChain \/ LlamaIndex/i)).toBeInTheDocument();
  });

  it('opens side panel drawer when clicking a skill with demand and why it matters', () => {
    render(<AtsSkillGapScreen state="success" data={mockScoreGood} />);

    // Click on missing skill row
    const skillButton = screen.getByRole('button', {
      name: new RegExp('MLOps \\(MLflow / Kubeflow\\)', 'i'),
    });
    fireEvent.click(skillButton);

    // Verify side panel drawer is opened
    const dialog = screen.getByRole('dialog');
    expect(dialog).toBeInTheDocument();
    expect(within(dialog).getByText(/Why This Matters for ATS & Recruiters/i)).toBeInTheDocument();
    expect(within(dialog).getByText(/Google XYZ Resume Bullet Template/i)).toBeInTheDocument();
    expect(within(dialog).getByText(/Live Market Job Postings Demand/i)).toBeInTheDocument();

    // Close panel
    const closeBtn = within(dialog).getByRole('button', { name: /Close skill details/i });
    fireEvent.click(closeBtn);
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('allows switching between filter tabs (Missing, Weak, Trending, Matched)', () => {
    render(<AtsSkillGapScreen state="success" data={mockScoreGood} />);

    // Click "Missing Gaps" filter
    const missingTab = screen.getByRole('tab', { name: /Missing Gaps/i });
    fireEvent.click(missingTab);
    expect(missingTab).toHaveAttribute('aria-selected', 'true');

    // Click "Trending Signals" filter
    const trendingTab = screen.getByRole('tab', { name: /Trending Signals/i });
    fireEvent.click(trendingTab);
    expect(trendingTab).toHaveAttribute('aria-selected', 'true');
  });

  it('allows switching target roles via the role switcher', () => {
    render(<AtsSkillGapScreen state="success" data={mockScoreGood} />);

    const roleSelect = screen.getByLabelText(/Target Role:/i);
    expect(roleSelect).toBeInTheDocument();

    fireEvent.change(roleSelect, { target: { value: 'Full Stack AI Engineer' } });
    expect(roleSelect.value).toBe('Full Stack AI Engineer');
  });

  it('renders accessible data table when switching view mode', () => {
    render(<AtsSkillGapScreen state="success" data={mockScoreGood} />);

    const tableModeBtn = screen.getByRole('button', { name: /Accessible Table/i });
    fireEvent.click(tableModeBtn);

    // Verify accessible semantic tables
    expect(screen.getByText(/Table 1: Missing Skills Ranked by Live Market Demand/i)).toBeInTheDocument();
    expect(screen.getByText(/Table 2: 6-Dimension Recruiter ATS Score Matrix/i)).toBeInTheDocument();
    expect(screen.getByText(/Table 3: Skill Portfolio Summary Distribution/i)).toBeInTheDocument();
  });

  it('renders skeleton loading state', () => {
    render(<AtsSkillGapScreen state="loading" data={mockScoreGood} />);
    expect(screen.getByTestId('ats-loading-skeleton')).toBeInTheDocument();
  });

  it('renders empty state when no gaps are found or state is empty', () => {
    render(<AtsSkillGapScreen state="empty" data={mockScoreNoGaps} />);
    expect(screen.getByTestId('ats-empty-state')).toBeInTheDocument();
    expect(screen.getByText(/No Skill Gaps Found — 100% Fit!/i)).toBeInTheDocument();
  });

  it('renders error state with actionable retry button', () => {
    const retrySpy = vi.fn();
    render(<AtsSkillGapScreen state="error" onRetry={retrySpy} />);

    expect(screen.getByTestId('ats-error-state')).toBeInTheDocument();
    const retryBtn = screen.getByRole('button', { name: /Retry ATS Analysis/i });
    expect(retryBtn).toBeInTheDocument();
  });
});

describe('Storybook-Like Demo Workbench', () => {
  it('renders the interactive studio with viewport buttons, fixture buttons, and raw JSON inspector', () => {
    render(<AtsStorybookDemo />);

    expect(screen.getByTestId('ats-storybook-demo')).toBeInTheDocument();
    expect(screen.getByText(/ATS Score & Skill-Gap Component Studio/i)).toBeInTheDocument();

    // Viewport selectors
    expect(screen.getByRole('button', { name: /375px/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /768px/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /1440px/i })).toBeInTheDocument();

    // Toggle JSON inspector
    const inspectBtn = screen.getByRole('button', { name: /Inspect JSON/i });
    fireEvent.click(inspectBtn);
    expect(screen.getByText(/ScoreResult JSON Contract Payload/i)).toBeInTheDocument();
  });
});
