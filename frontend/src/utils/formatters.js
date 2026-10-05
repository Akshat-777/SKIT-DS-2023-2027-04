/**
 * CareerLens Formatters & UI Helper Utilities
 */

/**
 * Format salary in Indian Rupees (INR) and Lakhs Per Annum (LPA)
 * @param {number} min - Minimum LPA
 * @param {number} max - Maximum LPA
 * @param {string} currency - e.g. "INR"
 * @param {string} unit - e.g. "LPA"
 * @returns {string} e.g. "₹14.5 - ₹22.0 LPA"
 */
export function formatSalary(min, max, currency = 'INR', unit = 'LPA') {
  const sym = currency === 'INR' ? '₹' : '$';
  if (min === undefined || min === null) return 'N/A';
  if (max === undefined || max === null || min === max) {
    return `${sym}${min} ${unit}`;
  }
  return `${sym}${min} - ${sym}${max} ${unit}`;
}

/**
 * Determine ATS score classification tier and Tailwind theme tokens
 * CareerLens ATS Score Threshold Ranges:
 * - Red (0 - 49): Critical gaps
 * - Amber (50 - 74): Moderate fit
 * - Green (75 - 100): Recruiter ready
 * @param {number} score
 * @returns {{ level: 'red'|'amber'|'green', label: string, color: string, badgeVariant: string }}
 */
export function getScoreThreshold(score) {
  const num = Number(score) || 0;
  if (num >= 75) {
    return {
      level: 'green',
      label: 'Recruiter Ready',
      color: '#10B981',
      badgeVariant: 'success',
      textClass: 'text-emerald-600 dark:text-emerald-400',
      bgClass: 'bg-emerald-50 dark:bg-emerald-950/60',
      borderClass: 'border-emerald-200 dark:border-emerald-800',
    };
  }
  if (num >= 50) {
    return {
      level: 'amber',
      label: 'Moderate Fit',
      color: '#F59E0B',
      badgeVariant: 'warning',
      textClass: 'text-amber-600 dark:text-amber-400',
      bgClass: 'bg-amber-50 dark:bg-amber-950/60',
      borderClass: 'border-amber-200 dark:border-amber-800',
    };
  }
  return {
    level: 'red',
    label: 'Critical Gaps',
    color: '#EF4444',
    badgeVariant: 'danger',
    textClass: 'text-rose-600 dark:text-rose-400',
    bgClass: 'bg-rose-50 dark:bg-rose-950/60',
    borderClass: 'border-rose-200 dark:border-rose-800',
  };
}

/**
 * Format ISO dates for user display
 * @param {string} dateStr
 * @returns {string} e.g. "Oct 5, 2026"
 */
export function formatDate(dateStr) {
  if (!dateStr) return '';
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch (_e) {
    return dateStr;
  }
}
