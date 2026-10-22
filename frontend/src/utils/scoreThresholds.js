/**
 * CareerLens ATS Score Threshold & Breakdown Specification
 * 
 * Score Tiers:
 * - Poor (< 50): Critical gaps, immediate intervention required
 * - Fair (50 - 69): Moderate fit, passes basic screening but lacks competitive edge
 * - Good (70 - 84): Strong match, highly competitive for interview shortlisting
 * - Excellent (85 - 100): Top-tier candidate, exceeding ATS qualification benchmark
 */

export const SCORE_TIERS = {
  POOR: 'Poor',
  FAIR: 'Fair',
  GOOD: 'Good',
  EXCELLENT: 'Excellent',
};

/**
 * Classifies an ATS score into Poor, Fair, Good, or Excellent with associated theme tokens.
 * @param {number|string} score - ATS score (0 - 100)
 * @returns {object} Tier metadata including label, colors, classes, and plain-English summary.
 */
export function getAtsScoreTier(score) {
  const num = Math.min(100, Math.max(0, Math.round(Number(score) || 0)));

  if (num >= 85) {
    return {
      tier: SCORE_TIERS.EXCELLENT,
      label: 'Excellent',
      color: '#10B981', // Emerald 500
      badgeVariant: 'success',
      textClass: 'text-emerald-700 dark:text-emerald-300',
      bgClass: 'bg-emerald-50 dark:bg-emerald-950/60',
      borderClass: 'border-emerald-200 dark:border-emerald-800',
      ringColor: '#10B981',
      glow: 'rgba(16, 185, 129, 0.25)',
      description: 'Exceptional recruiter match. Exceeds standard automated screening thresholds.',
      shortDesc: 'Recruiter-Ready',
      iconName: 'CheckCircle2',
    };
  }

  if (num >= 70) {
    return {
      tier: SCORE_TIERS.GOOD,
      label: 'Good',
      color: '#3B82F6', // Blue 500
      badgeVariant: 'primary',
      textClass: 'text-blue-700 dark:text-blue-300',
      bgClass: 'bg-blue-50 dark:bg-blue-950/60',
      borderClass: 'border-blue-200 dark:border-blue-800',
      ringColor: '#3B82F6',
      glow: 'rgba(59, 130, 246, 0.25)',
      description: 'Competitive candidate profile. High probability of clearing automated ATS filters.',
      shortDesc: 'Competitive Fit',
      iconName: 'Sparkles',
    };
  }

  if (num >= 50) {
    return {
      tier: SCORE_TIERS.FAIR,
      label: 'Fair',
      color: '#F59E0B', // Amber 500
      badgeVariant: 'warning',
      textClass: 'text-amber-700 dark:text-amber-300',
      bgClass: 'bg-amber-50 dark:bg-amber-950/60',
      borderClass: 'border-amber-200 dark:border-amber-800',
      ringColor: '#F59E0B',
      glow: 'rgba(245, 158, 11, 0.25)',
      description: 'Moderate fit with noticeable gaps in keywords or quantified impact.',
      shortDesc: 'Moderate Fit',
      iconName: 'AlertTriangle',
    };
  }

  return {
    tier: SCORE_TIERS.POOR,
    label: 'Poor',
    color: '#EF4444', // Red 500
    badgeVariant: 'danger',
    textClass: 'text-rose-700 dark:text-rose-300',
    bgClass: 'bg-rose-50 dark:bg-rose-950/60',
    borderClass: 'border-rose-200 dark:border-rose-800',
    ringColor: '#EF4444',
    glow: 'rgba(239, 68, 68, 0.25)',
    description: 'Critical gaps detected. Unlikely to pass ATS filters without targeted optimization.',
    shortDesc: 'Needs Immediate Polish',
    iconName: 'AlertCircle',
  };
}

/**
 * 6-Factor ATS Breakdown Metadata Specifications
 */
export const BREAKDOWN_METRIC_CONFIG = {
  keyword_match: {
    key: 'keyword_match',
    label: 'Keyword Match',
    weight: '20%',
    weightNum: 0.2,
    tooltip: 'Measures exact and synonymous matches between your resume and high-frequency terms from target job descriptions.',
    improveHint: 'Add missing target technologies and industry terms directly into your skills list and project descriptions.',
    benchmarkGood: 75,
  },
  semantic_similarity: {
    key: 'semantic_similarity',
    label: 'Semantic Similarity',
    weight: '25%',
    weightNum: 0.25,
    tooltip: 'Uses ChromaDB vector embeddings to evaluate how closely your resume’s conceptual context matches job postings, beyond keyword stuffing.',
    improveHint: 'Describe technical problem-solving, project context, and architectural decisions using industry-standard engineering phrasing.',
    benchmarkGood: 70,
  },
  section_completeness: {
    key: 'section_completeness',
    label: 'Section Completeness',
    weight: '15%',
    weightNum: 0.15,
    tooltip: 'Checks for standard ATS-expected resume sections: Contact Info, Summary, Experience, Education, Skills, and Projects.',
    improveHint: 'Use standard header names (Experience, Education, Skills, Projects) so parsers do not drop entire sections.',
    benchmarkGood: 85,
  },
  formatting: {
    key: 'formatting',
    label: 'ATS Formatting & Cleanliness',
    weight: '10%',
    weightNum: 0.1,
    tooltip: 'Scans for parsing obstacles such as multi-column layouts, graphics, tables, unusual fonts, or header/footer traps.',
    improveHint: 'Adopt a single-column layout, standard bullet points, and clean typography to guarantee 100% parser readability.',
    benchmarkGood: 80,
  },
  experience_relevance: {
    key: 'experience_relevance',
    label: 'Experience Relevance',
    weight: '15%',
    weightNum: 0.15,
    tooltip: 'Evaluates the recency, job titles, and scope of your past work against the seniority and responsibilities of the target role.',
    improveHint: 'Reframe prior project roles to emphasize responsibilities and tech stack aligned with your target job description.',
    benchmarkGood: 75,
  },
  quantified_impact: {
    key: 'quantified_impact',
    label: 'Quantified Impact',
    weight: '15%',
    weightNum: 0.15,
    tooltip: 'Detects numerical metrics (%, $, latency, scale) demonstrating concrete outcomes rather than passive job duties.',
    improveHint: 'Apply the Google XYZ formula: "Accomplished [X] as measured by [Y] by doing [Z]" to every single bullet point.',
    benchmarkGood: 70,
  },
};
