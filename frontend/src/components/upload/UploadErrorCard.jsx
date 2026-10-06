import React from 'react';
import { AlertCircle, RefreshCw, Upload, WifiOff, FileWarning, Clock, ShieldAlert } from 'lucide-react';
import Button from '../ui/Button';

/**
 * CareerLens UploadErrorCard
 * 
 * Comprehensive error handling interface for all upload and parsing failure states:
 * - Unsupported file type
 * - File too large (> 5 MB)
 * - Empty or unreadable file
 * - Upload failure (HTTP 4xx/5xx)
 * - Parsing failure at specific step (OCR, NER, Scoring)
 * - Network offline
 * - Timeouts
 * 
 * Provides:
 * - Human-friendly explanation
 * - Contract error code {"error": {"code": str, "message": str}}
 * - Retry and Re-upload action buttons
 */
export default function UploadErrorCard({
  error,
  failedStep = null,
  onRetry,
  onReupload,
  className = '',
}) {
  if (!error) return null;

  const errorCode = error.code || 'UNKNOWN_ERROR';
  const errorMessage = error.message || 'An unexpected error occurred.';

  // Map error code to human-friendly title, icon, and contextual advice
  let title = 'Upload & Parsing Error';
  let Icon = AlertCircle;
  let advice = 'Please review your resume document or server connection and try again.';
  let isRetriable = true;

  switch (errorCode) {
    case 'UNSUPPORTED_TYPE':
      title = 'Unsupported File Format';
      Icon = FileWarning;
      advice = 'CareerLens requires PDF (.pdf) or Word (.docx) documents. Image files or archives are not accepted directly.';
      isRetriable = false;
      break;

    case 'FILE_TOO_LARGE':
      title = 'File Exceeds Size Limit';
      Icon = FileWarning;
      advice = 'The maximum document upload limit is 5 MB. Please compress your PDF or remove high-resolution raster images.';
      isRetriable = false;
      break;

    case 'EMPTY_OR_UNREADABLE':
    case 'CORRUPTED_FILE_STREAM':
      title = 'Empty or Corrupted Document';
      Icon = FileWarning;
      advice = 'The selected file contains 0 bytes or has corrupted binary headers. PyMuPDF could not read a valid document stream.';
      isRetriable = false;
      break;

    case 'NETWORK_OFFLINE':
      title = 'Network Connection Lost';
      Icon = WifiOff;
      advice = 'You appear to be offline. Reconnect to the internet and click Retry to resume your evaluation.';
      isRetriable = true;
      break;

    case 'POLLING_TIMEOUT':
    case 'SCORING_TIMEOUT':
    case 'TIMEOUT':
      title = 'ML Pipeline Latency Timeout';
      Icon = Clock;
      advice = 'The Hugging Face NER or LightGBM model queue timed out. The server may be under heavy campus demo load.';
      isRetriable = true;
      break;

    case 'OCR_EXTRACTION_FAILED':
      title = 'OCR Processing Failure';
      Icon = ShieldAlert;
      advice = `TrOCR failed during optical text extraction at step: ${failedStep || 'Text extraction/OCR'}. The scanned document may have insufficient DPI.`;
      isRetriable = true;
      break;

    case 'NER_EXTRACTION_FAILED':
      title = 'NER Parsing Failure';
      Icon = ShieldAlert;
      advice = `Entity extraction model encountered an issue at step: ${failedStep || 'Entity extraction'}.`;
      isRetriable = true;
      break;

    case 'UPLOAD_GATEWAY_ERROR':
    case 'UPLOAD_FAILED':
      title = 'Upload Failed to Gateway';
      Icon = AlertCircle;
      advice = 'The FastAPI backend could not receive the file stream. Check backend service health and min 8GB RAM specifications.';
      isRetriable = true;
      break;

    default:
      if (failedStep) {
        title = `Parsing Failed at Step: ${failedStep}`;
        Icon = AlertCircle;
        advice = `An error interrupted the evaluation pipeline during "${failedStep}".`;
      }
      break;
  }

  return (
    <div
      data-testid="upload-error-card"
      role="alert"
      aria-live="assertive"
      className={`w-full p-6 sm:p-7 bg-rose-50/90 dark:bg-rose-950/40 rounded-2xl border border-rose-200 dark:border-rose-900 shadow-sm animate-fade-in ${className}`}
    >
      <div className="flex items-start gap-4">
        {/* Error Category Icon */}
        <div className="w-11 h-11 rounded-xl bg-rose-100 text-rose-600 dark:bg-rose-900/80 dark:text-rose-300 flex items-center justify-center flex-shrink-0 shadow-xs">
          <Icon className="w-6 h-6" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <h3 className="text-base font-bold text-rose-900 dark:text-rose-100">
              {title}
            </h3>
            <span
              data-testid="error-code-badge"
              className="px-2 py-0.5 rounded-md bg-rose-200 dark:bg-rose-900 text-rose-800 dark:text-rose-200 font-mono text-3xs font-semibold uppercase tracking-wider"
            >
              {errorCode}
            </span>
          </div>

          <p className="text-xs text-rose-700 dark:text-rose-300 font-medium mb-1">
            {errorMessage}
          </p>

          <p className="text-2xs text-rose-600/90 dark:text-rose-400 leading-relaxed">
            {advice}
          </p>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center gap-3 mt-4 pt-3 border-t border-rose-200/80 dark:border-rose-900/80">
            {isRetriable && onRetry && (
              <Button
                type="button"
                data-testid="retry-error-button"
                variant="danger"
                size="sm"
                onClick={onRetry}
                icon={<RefreshCw className="w-3.5 h-3.5" />}
              >
                Retry
              </Button>
            )}

            {onReupload && (
              <Button
                type="button"
                data-testid="reupload-button"
                variant="outline"
                size="sm"
                onClick={onReupload}
                icon={<Upload className="w-3.5 h-3.5" />}
                className="bg-white dark:bg-slate-900 border-rose-300 dark:border-rose-800 text-rose-800 dark:text-rose-200 hover:bg-rose-100/50"
              >
                Re-upload Resume
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
