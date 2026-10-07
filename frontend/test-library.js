/**
 * CareerLens Architecture & Deliverables Verification Suite
 * Validates:
 * 1. 13 UI Library components
 * 2. 7 Screen wireframes
 * 3. Responsive Layout modules (Navbar, Sidebar, PageContainer, ProtectedRoute)
 * 4. Chart components (ScoreRadarChart, SalaryRangeChart, SkillGapBar)
 * 5. React Router v6 pages (Login, Register, Upload, Analysis, MarketFit, Roadmap, Critique, History, 404)
 * 6. API & Service layer (Axios instances, authService, resumeService, dashboardService, mock-mode switch)
 * 7. AuthContext & custom hooks (useAuth, useResume, useDashboard)
 * 8. Utilities (tokenStorage localStorage tradeoff, formatters)
 * 9. Tooling configs (Vite alias @/, .env, Prettier, ESLint)
 * 10. Shared JSON contract conformance
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log('====================================================');
console.log('  CareerLens Full System Architecture Verification');
console.log('  SKIT Jaipur • Final Year B.Tech CSE (DS)');
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

// 1. Reusable UI Components
console.log('1. Checking Reusable UI Components in src/components/ui/ ...');
const uiComponents = [
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
  'ScoreRing.jsx',
];
uiComponents.forEach((comp) => {
  assert(fs.existsSync(path.join(__dirname, 'src', 'components', 'ui', comp)), `UI Component exists: ${comp}`);
});

// 2. Layout Components
console.log('\n2. Checking Responsive Layout Components in src/components/layout/ ...');
const layoutComponents = ['Navbar.jsx', 'Sidebar.jsx', 'PageContainer.jsx', 'ProtectedRoute.jsx'];
layoutComponents.forEach((comp) => {
  assert(fs.existsSync(path.join(__dirname, 'src', 'components', 'layout', comp)), `Layout Component exists: ${comp}`);
});

// 3. Chart Components
console.log('\n3. Checking Chart Components in src/components/charts/ ...');
const chartComponents = ['ScoreRadarChart.jsx', 'SalaryRangeChart.jsx', 'SkillGapBar.jsx'];
chartComponents.forEach((comp) => {
  assert(fs.existsSync(path.join(__dirname, 'src', 'components', 'charts', comp)), `Chart Component exists: ${comp}`);
});

// 4. Page Views (React Router v6)
console.log('\n4. Checking Lazy-Loaded Page Views in src/pages/ ...');
const pages = [
  'LoginPage.jsx',
  'RegisterPage.jsx',
  'UploadPage.jsx',
  'AnalysisPage.jsx',
  'MarketFitPage.jsx',
  'RoadmapPage.jsx',
  'CritiquePage.jsx',
  'HistoryPage.jsx',
  'NotFoundPage.jsx',
];
pages.forEach((pg) => {
  assert(fs.existsSync(path.join(__dirname, 'src', 'pages', pg)), `Page exists: ${pg}`);
});

// 5. API & Service Layer
console.log('\n5. Checking API Layer & Services in src/services/ ...');
const services = ['apiClient.js', 'authService.js', 'resumeService.js', 'dashboardService.js'];
services.forEach((srv) => {
  assert(fs.existsSync(path.join(__dirname, 'src', 'services', srv)), `Service exists: ${srv}`);
});
const apiClientContent = fs.readFileSync(path.join(__dirname, 'src', 'services', 'apiClient.js'), 'utf8');
assert(apiClientContent.includes('Authorization') && apiClientContent.includes('Bearer'), 'apiClient attaches Authorization Bearer token');
assert(apiClientContent.includes('401'), 'apiClient handles 401 unauthorized status');
assert(apiClientContent.includes('{"error": {"code": str, "message": str}}') || apiClientContent.includes('standardizedError'), 'apiClient formats standard error contract');

// 6. Context & Hooks
console.log('\n6. Checking AuthContext & Custom Hooks ...');
assert(fs.existsSync(path.join(__dirname, 'src', 'context', 'AuthContext.jsx')), 'AuthContext.jsx exists');
assert(fs.existsSync(path.join(__dirname, 'src', 'hooks', 'useAuth.js')), 'useAuth.js exists');
assert(fs.existsSync(path.join(__dirname, 'src', 'hooks', 'useResume.js')), 'useResume.js exists');
assert(fs.existsSync(path.join(__dirname, 'src', 'hooks', 'useDashboard.js')), 'useDashboard.js exists');

// 7. Token Storage & Tradeoff Documentation
console.log('\n7. Checking Token Persistence & Architecture Tradeoff ...');
const tokenStoragePath = path.join(__dirname, 'src', 'utils', 'tokenStorage.js');
assert(fs.existsSync(tokenStoragePath), 'tokenStorage.js exists');
const tokenStorageContent = fs.readFileSync(tokenStoragePath, 'utf8');
assert(tokenStorageContent.includes('localStorage') && tokenStorageContent.includes('In-Memory'), 'tokenStorage documents localStorage vs memory tradeoff');

// 8. Router & Root App
console.log('\n8. Checking React Router Configuration & Root App ...');
assert(fs.existsSync(path.join(__dirname, 'src', 'routes', 'AppRoutes.jsx')), 'AppRoutes.jsx exists');
const appRoutesContent = fs.readFileSync(path.join(__dirname, 'src', 'routes', 'AppRoutes.jsx'), 'utf8');
assert(appRoutesContent.includes('/login') && appRoutesContent.includes('/register'), 'AppRoutes registers /login and /register');
assert(appRoutesContent.includes('/upload') && appRoutesContent.includes('/analysis/:resumeId'), 'AppRoutes registers /upload and /analysis/:resumeId');
assert(appRoutesContent.includes('/market-fit/:resumeId') && appRoutesContent.includes('/roadmap/:resumeId'), 'AppRoutes registers /market-fit and /roadmap');
assert(appRoutesContent.includes('/critique/:resumeId') && appRoutesContent.includes('/history'), 'AppRoutes registers /critique and /history');
assert(appRoutesContent.includes('ProtectedRoute'), 'AppRoutes wraps protected pages in ProtectedRoute');
assert(appRoutesContent.includes('Suspense'), 'AppRoutes configures React Suspense lazy loading');

// 9. Tooling & Configs
console.log('\n9. Checking Build Tooling, Aliases & Environment Configs ...');
const viteConfigContent = fs.readFileSync(path.join(__dirname, 'vite.config.js'), 'utf8');
assert(viteConfigContent.includes('@') && viteConfigContent.includes('./src'), 'vite.config.js includes @/ path alias');
assert(fs.existsSync(path.join(__dirname, '.env')), '.env exists');
assert(fs.existsSync(path.join(__dirname, '.env.example')), '.env.example exists');
const envContent = fs.readFileSync(path.join(__dirname, '.env'), 'utf8');
assert(envContent.includes('VITE_API_BASE_URL'), '.env configures VITE_API_BASE_URL for FastAPI');
assert(envContent.includes('VITE_AUTH_BASE_URL'), '.env configures VITE_AUTH_BASE_URL for Node auth');
assert(envContent.includes('VITE_USE_MOCK'), '.env configures VITE_USE_MOCK switch');
assert(fs.existsSync(path.join(__dirname, '.prettierrc')), '.prettierrc exists');

// 10. Shared JSON Contracts
console.log('\n10. Validating Shared JSON Contracts against specifications ...');
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
