import React, { useState, useRef, useCallback } from 'react';
import { UploadCloud, FileText, X, CheckCircle2, AlertCircle } from 'lucide-react';
import Button from '../ui/Button';
import Badge from '../ui/Badge';

const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024; // 5 MB limit per specification

const ACCEPTED_MIME_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/msword',
];

const ACCEPTED_EXTENSIONS = ['.pdf', '.docx'];

/**
 * Format bytes into human-readable string (KB / MB)
 * @param {number} bytes
 * @returns {string}
 */
export function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

/**
 * CareerLens FileDropzone Component
 * 
 * Supports:
 * - Drag-and-drop with highlight styling
 * - Accepts only PDF / DOCX, strictly enforced <= 5 MB
 * - File preview card with name, formatted size, type badge, and remove action
 * - Keyboard accessible (Enter & Space trigger, tab focus ring, ARIA)
 * - "Choose file" fallback button
 * - Validation error emission
 */
export default function FileDropzone({
  file = null,
  onFileSelect,
  onFileRemove,
  onError,
  disabled = false,
  className = '',
}) {
  const [isDragActive, setIsDragActive] = useState(false);
  const dragCounterRef = useRef(0);
  const fileInputRef = useRef(null);

  /**
   * Validate uploaded file format and size
   * @param {File} candidateFile
   * @returns {boolean}
   */
  const validateFile = useCallback(
    (candidateFile) => {
      if (!candidateFile) return false;

      // 1. Check for empty or 0-byte file
      if (candidateFile.size === 0) {
        if (onError) {
          onError({
            code: 'EMPTY_OR_UNREADABLE',
            message: 'Selected file is empty (0 bytes) or corrupted. Please provide a valid resume.',
          });
        }
        return false;
      }

      // 2. Check file size (max 5 MB)
      if (candidateFile.size > MAX_FILE_SIZE_BYTES) {
        if (onError) {
          onError({
            code: 'FILE_TOO_LARGE',
            message: `File size (${formatBytes(candidateFile.size)}) exceeds the 5MB limit. Please upload a smaller resume.`,
          });
        }
        return false;
      }

      // 3. Check MIME type and extension
      const fileName = candidateFile.name.toLowerCase();
      const hasValidExt = ACCEPTED_EXTENSIONS.some((ext) => fileName.endsWith(ext));
      const hasValidMime = ACCEPTED_MIME_TYPES.includes(candidateFile.type);

      if (!hasValidExt && !hasValidMime) {
        if (onError) {
          onError({
            code: 'UNSUPPORTED_TYPE',
            message: 'Unsupported file type. CareerLens accepts only PDF or DOCX documents.',
          });
        }
        return false;
      }

      return true;
    },
    [onError]
  );

  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (disabled) return;
    dragCounterRef.current += 1;
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDragActive(true);
    }
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (disabled) return;
    dragCounterRef.current -= 1;
    if (dragCounterRef.current === 0) {
      setIsDragActive(false);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (disabled) return;
    e.dataTransfer.dropEffect = 'copy';
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (disabled) return;
    setIsDragActive(false);
    dragCounterRef.current = 0;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      if (validateFile(droppedFile)) {
        onFileSelect(droppedFile);
      }
      e.dataTransfer.clearData();
    }
  };

  const handleInputChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      const selected = e.target.files[0];
      if (validateFile(selected)) {
        onFileSelect(selected);
      }
      // Reset input value so re-uploading the same file triggers change
      e.target.value = '';
    }
  };

  const openFilePicker = () => {
    if (!disabled && fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleKeyDown = (e) => {
    if (disabled) return;
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      openFilePicker();
    }
  };

  // Resolve file extension type for badge
  const isDocx = file?.name?.toLowerCase().endsWith('.docx');

  return (
    <div className={`w-full ${className}`}>
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        id="resume-file-input"
        data-testid="resume-file-input"
        accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        onChange={handleInputChange}
        disabled={disabled}
        className="hidden"
      />

      {!file ? (
        /* Drag-and-Drop Active Zone */
        <div
          role="button"
          tabIndex={disabled ? -1 : 0}
          aria-label="Upload resume file dropzone. Drag and drop PDF or DOCX file here or press Enter to browse."
          aria-disabled={disabled}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onKeyDown={handleKeyDown}
          onClick={openFilePicker}
          className={`relative border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center transition-all duration-200 cursor-pointer select-none outline-none focus-visible:ring-4 focus-visible:ring-brand-500/30 ${
            disabled
              ? 'opacity-50 cursor-not-allowed bg-slate-50 dark:bg-slate-900 border-slate-200 dark:border-slate-800'
              : isDragActive
              ? 'border-brand-500 bg-brand-50/70 dark:bg-brand-950/40 ring-4 ring-brand-500/20 scale-[1.01]'
              : 'border-slate-300 dark:border-slate-700 hover:border-brand-400 bg-white dark:bg-slate-850 shadow-subtle hover:shadow-card'
          }`}
        >
          {/* Pulsing Cloud Icon */}
          <div
            className={`w-16 h-16 rounded-2xl mx-auto flex items-center justify-center mb-4 transition-transform duration-200 ${
              isDragActive
                ? 'bg-brand-500 text-white scale-110 shadow-glow-brand'
                : 'bg-brand-50 dark:bg-brand-950/80 border border-brand-200 dark:border-brand-800 text-brand-600 dark:text-brand-400'
            }`}
          >
            <UploadCloud className="w-8 h-8" />
          </div>

          <h3 className="text-base sm:text-lg font-bold text-slate-900 dark:text-slate-100 mb-1">
            Drag & drop your resume here, or{' '}
            <span className="text-brand-600 dark:text-brand-400 underline underline-offset-2">
              choose file
            </span>
          </h3>

          <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mx-auto mb-4">
            Supports <strong className="text-slate-700 dark:text-slate-300">PDF</strong> and{' '}
            <strong className="text-slate-700 dark:text-slate-300">DOCX</strong> formats (Max{' '}
            <span className="font-semibold text-slate-700 dark:text-slate-300">5 MB</span>).
            Scanned documents are handled with TrOCR optical recognition.
          </p>

          {/* Explicit "Choose file" fallback button */}
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={disabled}
            onClick={(e) => {
              e.stopPropagation();
              openFilePicker();
            }}
            className="pointer-events-auto"
          >
            Choose File from Device
          </Button>

          {/* Format Badges */}
          <div className="flex items-center justify-center gap-2 mt-5 pt-4 border-t border-slate-100 dark:border-slate-800 text-2xs text-slate-500">
            <span className="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 font-mono font-medium">
              .PDF
            </span>
            <span className="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 font-mono font-medium">
              .DOCX
            </span>
            <span>•</span>
            <span>Max 5 MB</span>
            <span>•</span>
            <span className="text-emerald-600 dark:text-emerald-400 font-medium">
              OCR Compatible
            </span>
          </div>
        </div>
      ) : (
        /* File Preview Card */
        <div
          data-testid="file-preview-card"
          className="relative p-5 bg-white dark:bg-slate-850 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-card transition-all"
        >
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-center gap-3.5 min-w-0">
              {/* Type Badge Icon */}
              <div
                className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 font-bold text-xs uppercase shadow-subtle ${
                  isDocx
                    ? 'bg-blue-100 text-blue-700 dark:bg-blue-950/80 dark:text-blue-300 border border-blue-200 dark:border-blue-800'
                    : 'bg-rose-100 text-rose-700 dark:bg-rose-950/80 dark:text-rose-300 border border-rose-200 dark:border-rose-800'
                }`}
              >
                <div className="flex flex-col items-center">
                  <FileText className="w-5 h-5 mb-0.5" />
                  <span className="text-3xs font-mono font-black">{isDocx ? 'DOCX' : 'PDF'}</span>
                </div>
              </div>

              {/* File Info */}
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <h4
                    className="text-sm font-bold text-slate-900 dark:text-slate-100 truncate max-w-[240px] sm:max-w-md"
                    title={file.name}
                  >
                    {file.name}
                  </h4>
                  <Badge variant="success" size="sm" dot>
                    Valid
                  </Badge>
                </div>
                <div className="flex items-center gap-2 mt-1 text-2xs text-slate-500 dark:text-slate-400">
                  <span>{formatBytes(file.size)}</span>
                  <span>•</span>
                  <span>{isDocx ? 'Microsoft Word Document' : 'Portable Document Format'}</span>
                </div>
              </div>
            </div>

            {/* Remove / Clear Action */}
            <button
              type="button"
              data-testid="remove-file-button"
              aria-label="Remove selected resume"
              disabled={disabled}
              onClick={(e) => {
                e.stopPropagation();
                onFileRemove();
              }}
              className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors focus:outline-none focus:ring-2 focus:ring-rose-500 disabled:opacity-50"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="flex items-center justify-between mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 text-2xs">
            <span className="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Document ready for multi-agent ATS evaluation & NER extraction
            </span>
            <button
              type="button"
              disabled={disabled}
              onClick={openFilePicker}
              className="text-brand-600 dark:text-brand-400 hover:underline font-medium"
            >
              Change document
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
