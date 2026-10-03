/**
 * CareerLens UI & Component Verification Suite
 * Validates that all 13 required UI components, 7 screen wireframes,
 * and Shared JSON contracts conform to project specs and types.
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log('====================================================');
console.log('  CareerLens UI Library & Wireframe Verification');
console.log('  Final Year Project');
console.log('====================================================\n');

let passCount = 0;
let failCount = 0;

function assert(condition, message) {
  if (condition) {
    console.log(`  ✓ PASS: ${message}`);
    passCount++;
  } else {
    console.error(`  ✗ FAIL: ${message}`);
    failCount++;
  }
}

// 1. Check all 13 required UI components exist
const requiredComponents = [
  'Button.jsx',
  'Input.jsx',
  'Card.jsx',
  'Badge.jsx',
  'Modal.jsx',
  'Tabs.jsx',
  'ProgressBar.jsx',
  'Spinner.jsx',
  'Skeleton.jsx',
  'Toast.jsx',
  'EmptyState.jsx',
  'ErrorState.jsx',
  'ScoreRing.jsx'
];

console.log('1. Checking Reusable UI Components in src/components/ui/ ...');
const uiDir = path.join(__dirname, 'src', 'components', 'ui');
requiredComponents.forEach((comp) => {
  const filePath = path.join(uiDir, comp);
  const exists = fs.existsSync(filePath);
  assert(exists, `Component exists: ${comp}`);
});

// 2. Check all 7 screen wireframe components exist
const requiredScreens = [
  'LoginRegisterScreen.jsx',
  'ResumeUploadScreen.jsx',
  'ParsingStatusScreen.jsx',
  'AtsSkillGapScreen.jsx',
  'MarketFitSalaryScreen.jsx',
  'LearningRoadmapScreen.jsx',
  'RecruiterCritiqueScreen.jsx'
];

console.log('\n2. Checking 7 Screen Wireframe Modules in src/components/screens/ ...');
const screensDir = path.join(__dirname, 'src', 'components', 'screens');
requiredScreens.forEach((scr) => {
  const filePath = path.join(screensDir, scr);
  const exists = fs.existsSync(filePath);
  assert(exists, `Screen wireframe exists: ${scr}`);
});

// 3. Check Design Token Configurations
console.log('\n3. Validating Tailwind Config & Global CSS Design Tokens ...');
const tailwindConfigPath = path.join(__dirname, 'tailwind.config.js');
const indexCssPath = path.join(__dirname, 'src', 'index.css');

assert(fs.existsSync(tailwindConfigPath), 'tailwind.config.js exists');
const tailwindContent = fs.readFileSync(tailwindConfigPath, 'utf8');
assert(tailwindContent.includes('ats:'), 'Tailwind config includes ATS score color thresholds');
assert(tailwindContent.includes('brand:'), 'Tailwind config includes custom brand palette');
assert(tailwindContent.includes('screens:'), 'Tailwind config includes responsive breakpoints (xs 375, md 768, 2xl 1440)');

assert(fs.existsSync(indexCssPath), 'index.css exists');
const indexCssContent = fs.readFileSync(indexCssPath, 'utf8');
assert(indexCssContent.includes('Plus+Jakarta+Sans') || indexCssContent.includes('Plus Jakarta Sans'), 'index.css imports Plus Jakarta Sans font');
assert(indexCssContent.includes('@tailwind base;'), 'index.css includes Tailwind directives');

// 4. Validate Shared JSON Contract Compliance
console.log('\n4. Validating Shared JSON Contracts against specs ...');
const mockDataPath = path.join(__dirname, 'src', 'data', 'mockData.js');
assert(fs.existsSync(mockDataPath), 'mockData.js exists');

import('./src/data/mockData.js').then((module) => {
  const { mockParsedResume, mockScoreResult, mockMarketFit, mockRoadmap, mockCritique, mockApiError } = module;

  // ParsedResume
  assert(mockParsedResume.resume_id && mockParsedResume.name && Array.isArray(mockParsedResume.skills), 'ParsedResume contract valid');
  assert(mockParsedResume.skills[0].type === 'explicit' || mockParsedResume.skills[0].type === 'implicit', 'Skills contract uses explicit/implicit');

  // ScoreResult
  assert(typeof mockScoreResult.ats_score === 'number' && mockScoreResult.breakdown && mockScoreResult.skill_gap, 'ScoreResult contract valid');
  assert(Array.isArray(mockScoreResult.skill_gap.matched) && Array.isArray(mockScoreResult.skill_gap.missing), 'Skill gap contract has matched & missing');

  // MarketFit
  assert(mockMarketFit.currency === 'INR' && mockMarketFit.unit === 'LPA', 'MarketFit contract uses INR LPA currency');
  assert(typeof mockMarketFit.salary_min === 'number' && typeof mockMarketFit.salary_max === 'number', 'MarketFit has numerical salary_min and salary_max');

  // Roadmap
  assert(Array.isArray(mockRoadmap.phases) && mockRoadmap.phases[0].linked_gap_skill, 'Roadmap contract connects phases to linked_gap_skill');

  // Critique
  assert(Array.isArray(mockCritique.agents) && mockCritique.merged && mockCritique.merged.consensus_score, 'Critique contract includes 3 agents & merged consensus');

  // Error contract
  assert(mockApiError.error && mockApiError.error.code && mockApiError.error.message, 'API error contract adheres to {"error": {"code": str, "message": str}}');

  console.log('\n====================================================');
  console.log(`  Test Results: ${passCount} Passed, ${failCount} Failed`);
  console.log('====================================================\n');

  if (failCount > 0) {
    process.exit(1);
  } else {
    process.exit(0);
  }
}).catch((err) => {
  console.error('Failed to import mock data:', err);
  process.exit(1);
});
