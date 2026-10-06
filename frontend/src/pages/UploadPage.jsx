import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Sparkles,
  ArrowRight,
  Cpu,
  Layers,
  CheckCircle2,
  XCircle,
  HelpCircle,
  FlaskConical,
  RotateCcw,
} from 'lucide-react';
import PageContainer from '../components/layout/PageContainer';
import Button from '../components/ui/Button';
import Card, { CardContent } from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import ProgressBar from '../components/ui/ProgressBar';
import { useToast } from '../components/ui/Toast';
import FileDropzone from '../components/upload/FileDropzone';
import TargetRoleSelector from '../components/upload/TargetRoleSelector';
import StepTracker from '../components/upload/StepTracker';
import UploadErrorCard from '../components/upload/UploadErrorCard';
import { usePolling } from '../hooks/usePolling';
import { resumeService } from '../services/resumeService';
import { setMockScenario, getMockScenario } from '../mocks/handlers';

export default function UploadPage({ pollInterval = 2000 }) {
  const navigate = useNavigate();
  const toast = useToast();

  // 1. File & Configuration State
  const [selectedFile, setSelectedFile] = useState(null);
  const [targetRole, setTargetRole] = useState('Data Scientist / ML Engineer');
  const [ocrEnabled, setOcrEnabled] = useState(true);

  // 2. Lifecycle & Progress State: 'idle' | 'uploading' | 'parsing' | 'error' | 'success'
  const [pageState, setPageState] = useState('idle');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadedResumeId, setUploadedResumeId] = useState(null);
  const [errorState, setErrorState] = useState(null);
  const [failedStep, setFailedStep] = useState(null);

  // 3. Scenario Lab for MSW demonstration
  const [activeScenario, setActiveScenario] = useState('happy_path');
  const [showScenarioLab, setShowScenarioLab] = useState(false);

  // AbortController reference to cancel in-flight uploads
  const uploadAbortRef = useRef(null);

  // Keep MSW handler scenario in sync with UI selector
  const handleScenarioChange = (scenarioKey) => {
    setActiveScenario(scenarioKey);
    setMockScenario(scenarioKey);
    if (typeof window !== 'undefined' && window.localStorage) {
      window.localStorage.setItem('careerlens_msw_scenario', scenarioKey);
    }
    toast.info('MSW Scenario Updated', `Simulation switched to: "${scenarioKey}"`);
  };

  useEffect(() => {
    const current = getMockScenario();
    if (current) setActiveScenario(current);
  }, []);

  /**
   * 4. Live Polling Hook for Status Tracker
   * Driven by polling GET /resumes/{id}/status every 2 seconds
   */
  const {
    data: parsingData,
    error: pollingError,
    stop: stopPolling,
    restart: restartPolling,
  } = usePolling({
    queryFn: async (signal) => {
      if (!uploadedResumeId) return null;
      return await resumeService.getResumeStatus(uploadedResumeId, { signal });
    },
    interval: pollInterval,
    enabled: pageState === 'parsing' && !!uploadedResumeId,
    useBackoff: false,
    maxAttempts: 30, // 30 attempts * 2s = 60s timeout
    isTerminal: (res) => res?.status === 'completed' || res?.status === 'failed',
    onSuccess: (res) => {
      setPageState('success');
      toast.success(
        'Parsing Complete!',
        'NER extracted skills and LightGBM model computed ATS market-fit.'
      );
      const targetId = res?.resume_id || uploadedResumeId || 'res_default';
      navigate(`/analysis/${targetId}`);
    },
    onError: (err) => {
      setPageState('error');
      setErrorState(err);
      setFailedStep(parsingData?.current_step || 'NLP Parsing Pipeline');
    },
  });

  // Watch for polling error updates
  useEffect(() => {
    if (pollingError && pageState === 'parsing') {
      setPageState('error');
      setErrorState(pollingError);
      setFailedStep(parsingData?.current_step || 'NLP Parsing Pipeline');
    }
  }, [pollingError, parsingData, pageState]);

  /**
   * Handle File Selection and Validation
   */
  const handleFileSelect = (file) => {
    setSelectedFile(file);
    setErrorState(null);
    setFailedStep(null);
    toast.info('Document Loaded', `${file.name} ready for market benchmarking.`);
  };

  const handleFileRemove = () => {
    setSelectedFile(null);
    setErrorState(null);
    setFailedStep(null);
    setUploadProgress(0);
    setPageState('idle');
  };

  const handleValidationError = (validationErr) => {
    setErrorState(validationErr);
    setPageState('error');
    toast.error('File Rejected', validationErr.message);
  };

  /**
   * Cancel In-Flight Upload via AbortController
   */
  const handleCancelUpload = () => {
    if (uploadAbortRef.current) {
      uploadAbortRef.current.abort();
      uploadAbortRef.current = null;
    }
    setPageState('idle');
    setUploadProgress(0);
    toast.info('Upload Canceled', 'File transmission was aborted by user.');
  };

  /**
   * Cancel In-Flight Polling & Analysis
   */
  const handleCancelParsing = () => {
    stopPolling();
    setPageState('idle');
    setUploadedResumeId(null);
    toast.info('Analysis Stopped', 'Resume evaluation was canceled.');
  };

  /**
   * Execute Resume Upload & Trigger Parsing Pipeline
   */
  const handleStartAnalysis = async () => {
    if (!selectedFile) {
      setErrorState({
        code: 'MISSING_FILE',
        message: 'Please choose or drag a PDF/DOCX resume file before starting.',
      });
      setPageState('error');
      return;
    }

    if (!targetRole.trim()) {
      setErrorState({
        code: 'MISSING_TARGET_ROLE',
        message: 'Please specify a target job role for ATS benchmarking.',
      });
      setPageState('error');
      return;
    }

    // Set up AbortController for cancelable Axios upload
    uploadAbortRef.current = new AbortController();
    setPageState('uploading');
    setUploadProgress(0);
    setErrorState(null);
    setFailedStep(null);

    // If simulated scenario is "corrupt_file" and active in MSW
    if (activeScenario === 'corrupt_file' && typeof window !== 'undefined') {
      window.localStorage.setItem('careerlens_msw_scenario', 'corrupt_file');
    }

    try {
      const response = await resumeService.uploadResume(selectedFile, {
        targetRole,
        ocrEnabled,
        abortSignal: uploadAbortRef.current.signal,
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            setUploadProgress(percentCompleted);
          }
        },
      });

      const newResumeId = response.resume_id || `res_${Date.now().toString(36)}`;
      setUploadedResumeId(newResumeId);
      setUploadProgress(100);

      // Transition smoothly into live parsing step tracker
      setPageState('parsing');
    } catch (err) {
      if (err.name === 'CanceledError' || err.name === 'AbortError') {
        return; // Handled by handleCancelUpload
      }

      setPageState('error');
      setErrorState({
        code: err.code || 'UPLOAD_FAILED',
        message: err.message || 'Failed to transmit resume to FastAPI ingestion gateway.',
      });
      setFailedStep('Upload Gateway');
    } finally {
      uploadAbortRef.current = null;
    }
  };

  /**
   * Retry failed operation
   */
  const handleRetry = () => {
    if (pageState === 'error' && uploadedResumeId) {
      // Retry polling
      setErrorState(null);
      setPageState('parsing');
      restartPolling();
    } else {
      // Retry upload
      handleStartAnalysis();
    }
  };

  /**
   * Re-upload / Choose new document
   */
  const handleReupload = () => {
    stopPolling();
    setPageState('idle');
    setSelectedFile(null);
    setErrorState(null);
    setFailedStep(null);
    setUploadProgress(0);
    setUploadedResumeId(null);
  };

  return (
    <PageContainer>
      <div className="space-y-6 max-w-4xl mx-auto">
        {/* Header Section */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="primary" size="sm">
                FR-001 Ingestion
              </Badge>
              <span className="text-2xs font-mono text-slate-500">
                FastAPI • PyMuPDF • TrOCR • Hugging Face
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-slate-100 tracking-tight">
              Resume Ingestion & Market Benchmarking
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
              Evaluates resumes against live job-market demand, scores ATS fit, and identifies skill gaps.
            </p>
          </div>

          {/* Cloud Server Spec & MSW Lab Toggle */}
          <div className="flex items-center gap-2 flex-wrap">
            <div className="flex items-center gap-1.5 text-2xs bg-slate-100 dark:bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700">
              <Cpu className="w-3.5 h-3.5 text-brand-500" />
              <span className="font-semibold text-slate-700 dark:text-slate-300">
                Min 8GB RAM Cloud
              </span>
            </div>

            <button
              type="button"
              data-testid="toggle-msw-lab"
              onClick={() => setShowScenarioLab(!showScenarioLab)}
              className="flex items-center gap-1.5 text-2xs px-3 py-1.5 rounded-lg bg-brand-50 dark:bg-brand-950/70 text-brand-700 dark:text-brand-300 border border-brand-200 dark:border-brand-800 hover:bg-brand-100 transition-colors font-medium"
            >
              <FlaskConical className="w-3.5 h-3.5" />
              <span>MSW Scenario Lab</span>
            </button>
          </div>
        </div>

        {/* MSW Scenario Lab Drawer (For instant demo & verification of all paths) */}
        {showScenarioLab && (
          <div
            data-testid="msw-scenario-lab-panel"
            className="p-4 bg-slate-900 text-slate-100 rounded-2xl border border-slate-700 shadow-xl space-y-3 animate-fade-in text-xs"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FlaskConical className="w-4 h-4 text-brand-400" />
                <span className="font-bold">Mock Service Worker (MSW) Demo Scenarios</span>
                <span className="text-3xs px-2 py-0.5 rounded bg-brand-500/30 text-brand-300 font-mono">
                  Simulate Any Path
                </span>
              </div>
              <button
                type="button"
                onClick={() => setShowScenarioLab(false)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <p className="text-2xs text-slate-400">
              Select a scenario below to test the full happy path or any error condition without a running backend:
            </p>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
              {[
                { id: 'happy_path', label: '1. Happy Path (Standard)' },
                { id: 'scanned_ocr', label: '2. Scanned Doc (TrOCR Notice)' },
                { id: 'upload_error', label: '3. Upload Failure (500)' },
                { id: 'corrupt_file', label: '4. Corrupt File (422)' },
                { id: 'step_ocr_error', label: '5. OCR Step Failure (502)' },
                { id: 'step_ner_error', label: '6. NER Step Failure (500)' },
                { id: 'step_scoring_error', label: '7. Scoring Timeout (504)' },
                { id: 'timeout', label: '8. Polling Timeout (>60s)' },
              ].map((s) => (
                <button
                  key={s.id}
                  type="button"
                  data-testid={`scenario-btn-${s.id}`}
                  onClick={() => handleScenarioChange(s.id)}
                  className={`px-2.5 py-1.5 rounded-lg text-left text-2xs font-medium transition-all ${
                    activeScenario === s.id
                      ? 'bg-brand-600 text-white shadow-glow-brand font-bold'
                      : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Global Error Banner if state is error */}
        {pageState === 'error' && errorState && (
          <UploadErrorCard
            error={errorState}
            failedStep={failedStep}
            onRetry={handleRetry}
            onReupload={handleReupload}
          />
        )}

        {/* LIVE PARSING STATE: Step Tracker (5 Steps: Uploaded, OCR, NER, Skills, Scoring) */}
        {(pageState === 'parsing' || pageState === 'success') && (
          <StepTracker
            currentStepId={parsingData?.status || (pageState === 'success' ? 'scoring' : 'uploaded')}
            progressPct={pageState === 'success' ? 100 : (parsingData?.progress_pct || 20)}
            currentMessage={
              parsingData?.message ||
              'Parsing resume text and extracting entities with Hugging Face...'
            }
            ocrInUse={parsingData?.ocr_in_use || activeScenario === 'scanned_ocr'}
            isFailed={false}
            onCancel={handleCancelParsing}
          />
        )}

        {/* UPLOADING STATE: Axios Progress Bar with AbortController Cancel */}
        {pageState === 'uploading' && (
          <Card variant="default">
            <CardContent className="p-6 sm:p-8 space-y-4 text-center">
              <div className="w-12 h-12 rounded-2xl bg-brand-50 dark:bg-brand-950 text-brand-600 dark:text-brand-400 mx-auto flex items-center justify-center animate-pulse">
                <Layers className="w-6 h-6" />
              </div>

              <div>
                <h3 className="text-base sm:text-lg font-bold text-slate-900 dark:text-slate-100">
                  Uploading Resume to FastAPI Gateway
                </h3>
                <p className="text-xs text-slate-500 mt-1">
                  Transmitting {selectedFile?.name} with multi-part stream...
                </p>
              </div>

              <div className="max-w-md mx-auto pt-2">
                <ProgressBar
                  value={uploadProgress}
                  max={100}
                  variant="primary"
                  size="md"
                  showValue
                  striped
                />
              </div>

              {/* Cancel Upload Button */}
              <div className="pt-2">
                <Button
                  type="button"
                  data-testid="cancel-upload-button"
                  variant="outline"
                  size="sm"
                  onClick={handleCancelUpload}
                  className="text-rose-600 border-rose-200 hover:bg-rose-50 dark:border-rose-800"
                >
                  Cancel Upload
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* IDLE / FORM CONFIGURATION STATE */}
        {(pageState === 'idle' || (pageState === 'error' && !uploadedResumeId)) && (
          <div className="space-y-6">
            {/* Step 1: Target Role & OCR Configuration Card */}
            <Card variant="default">
              <CardContent className="p-6 space-y-4">
                <TargetRoleSelector
                  value={targetRole}
                  onChange={setTargetRole}
                  disabled={pageState === 'uploading' || pageState === 'parsing'}
                />

                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t border-slate-100 dark:border-slate-800 text-xs">
                  <div className="flex items-center gap-2.5">
                    <input
                      type="checkbox"
                      id="ocr-toggle"
                      data-testid="ocr-checkbox"
                      checked={ocrEnabled}
                      onChange={(e) => setOcrEnabled(e.target.checked)}
                      className="w-4 h-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500 cursor-pointer"
                    />
                    <label
                      htmlFor="ocr-toggle"
                      className="text-slate-700 dark:text-slate-300 font-medium cursor-pointer select-none"
                    >
                      Enable TrOCR optical recognition for scanned / image resumes (Aishani Billore's OCR module)
                    </label>
                  </div>
                  <Badge variant="success" size="sm" dot>
                    TrOCR Ready
                  </Badge>
                </div>
              </CardContent>
            </Card>

            {/* Step 2: Drag & Drop Upload Zone */}
            <FileDropzone
              file={selectedFile}
              onFileSelect={handleFileSelect}
              onFileRemove={handleFileRemove}
              onError={handleValidationError}
              disabled={pageState === 'uploading' || pageState === 'parsing'}
            />

            {/* Action Bar */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 bg-slate-50 dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800">
              <div className="flex items-center gap-2 text-2xs text-slate-500">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                <span>
                  All uploads are processed securely under university data-privacy norms.
                </span>
              </div>

              <Button
                type="button"
                data-testid="begin-analysis-button"
                variant="primary"
                size="lg"
                disabled={!selectedFile || !targetRole.trim()}
                onClick={handleStartAnalysis}
                icon={<ArrowRight className="w-4 h-4" />}
                iconPosition="right"
                className="w-full sm:w-auto font-bold shadow-md shadow-brand-500/25"
              >
                Begin ATS Parsing & Analysis
              </Button>
            </div>
          </div>
        )}
      </div>
    </PageContainer>
  );
}
