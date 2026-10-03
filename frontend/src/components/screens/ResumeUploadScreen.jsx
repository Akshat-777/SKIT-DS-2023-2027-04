import React, { useState } from 'react';
import { UploadCloud, FileText, CheckCircle2, ShieldAlert, Cpu, Sparkles, ArrowRight } from 'lucide-react';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Card, { CardContent } from '../ui/Card';
import Badge from '../ui/Badge';
import ProgressBar from '../ui/ProgressBar';
import ErrorState from '../ui/ErrorState';
import EmptyState from '../ui/EmptyState';

export default function ResumeUploadScreen({
  state = 'success',
  onUploadComplete = () => {}
}) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState({
    name: 'Aarav_Sharma_Resume_2026.pdf',
    size: '1.4 MB',
    type: 'application/pdf',
  });
  const [targetRole, setTargetRole] = useState('Data Scientist / ML Engineer');
  const [ocrEnabled, setOcrEnabled] = useState(true);
  const [uploadProgress, setUploadProgress] = useState(100);
  const [isUploading, setIsUploading] = useState(false);

  if (state === 'empty') {
    return (
      <EmptyState
        icon={UploadCloud}
        title="No Resume Uploaded Yet"
        description="Upload your latest PDF or DOCX resume to trigger NLP parsing, ATS scoring, and live market intelligence."
        action={{
          label: "Upload Resume Now",
          onClick: () => {}
        }}
      />
    );
  }

  if (state === 'loading') {
    return (
      <div className="max-w-2xl mx-auto p-8 bg-white dark:bg-slate-850 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-brand-100 dark:bg-brand-950 text-brand-600 flex items-center justify-center animate-spin">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
              Uploading & Initializing OCR Pipeline...
            </h3>
            <p className="text-xs text-slate-500">Dispatching multi-part binary to FastAPI resume gateway...</p>
          </div>
        </div>
        <ProgressBar value={68} showValue label="Uploading binary stream" variant="primary" />
      </div>
    );
  }

  if (state === 'error') {
    return (
      <ErrorState
        error={{
          code: 'UNSUPPORTED_FILE_FORMAT',
          message: 'The uploaded file exceeds the 10MB limit or is not a valid PDF or DOCX file. Please verify file integrity and re-upload.'
        }}
        onRetry={() => {}}
        actionLabel="Choose Another File"
      />
    );
  }

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleSimulatedUpload = () => {
    setIsUploading(true);
    setUploadProgress(20);
    const interval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsUploading(false);
          onUploadComplete();
          return 100;
        }
        return prev + 30;
      });
    }, 300);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header Info */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight flex items-center gap-2">
            Resume Ingestion & Target Role
            <Badge variant="primary" size="sm">FR-001</Badge>
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            Accepts PDF/DOCX with integrated Tesseract/TrOCR engine for scanned resumes.
          </p>
        </div>
        <div className="flex items-center gap-2 text-2xs bg-slate-100 dark:bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700">
          <Cpu className="w-3.5 h-3.5 text-brand-500" />
          <span className="font-medium text-slate-700 dark:text-slate-300">Min 8GB RAM Cloud Server</span>
        </div>
      </div>

      {/* Target Role Selector */}
      <Card variant="default">
        <CardContent className="p-5 space-y-4">
          <Input
            label="Target Job Role for Benchmarking"
            value={targetRole}
            onChange={(e) => setTargetRole(e.target.value)}
            placeholder="e.g. Data Scientist / ML Engineer"
            helperText="CareerLens will fetch live market demand signals and ATS benchmarks for this exact job title."
            required
          />

          <div className="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-800 text-xs">
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="ocr-toggle"
                checked={ocrEnabled}
                onChange={(e) => setOcrEnabled(e.target.checked)}
                className="rounded border-slate-300 text-brand-600 focus:ring-brand-500"
              />
              <label htmlFor="ocr-toggle" className="text-slate-700 dark:text-slate-300 font-medium cursor-pointer">
                Enable OCR Fallback for scanned/image resumes (NLP Pipeline)
              </label>
            </div>
            <Badge variant="success" size="sm" dot>OCR Active</Badge>
          </div>
        </CardContent>
      </Card>

      {/* Drag & Drop Upload Zone */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={(e) => {
          e.preventDefault();
          setDragActive(false);
        }}
        className={`relative border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center transition-all duration-200 ${
          dragActive
            ? 'border-brand-500 bg-brand-50/50 dark:bg-brand-950/30 ring-4 ring-brand-500/20'
            : 'border-slate-300 dark:border-slate-700 hover:border-brand-400 bg-white dark:bg-slate-850'
        }`}
      >
        <div className="w-16 h-16 rounded-2xl bg-brand-50 dark:bg-brand-950/80 border border-brand-200 dark:border-brand-800 text-brand-600 dark:text-brand-400 mx-auto flex items-center justify-center mb-4 shadow-subtle">
          <UploadCloud className="w-8 h-8" />
        </div>

        <h3 className="text-base sm:text-lg font-bold text-slate-900 dark:text-slate-100 mb-1">
          Drag & Drop your resume here, or <span className="text-brand-600 cursor-pointer hover:underline">browse files</span>
        </h3>
        <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mx-auto mb-4">
          Supported file formats: PDF, DOCX (Max size: 10MB). Text-extractable or scanned documents.
        </p>

        {selectedFile && (
          <div className="max-w-md mx-auto p-3.5 bg-slate-50 dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 flex items-center justify-between gap-3 text-left mb-5">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-rose-100 text-rose-600 dark:bg-rose-950/80 dark:text-rose-400 flex items-center justify-center">
                <FileText className="w-5 h-5" />
              </div>
              <div>
                <p className="text-xs font-bold text-slate-900 dark:text-slate-100 truncate max-w-[200px]">
                  {selectedFile.name}
                </p>
                <p className="text-2xs text-slate-500">{selectedFile.size} • Ready for analysis</p>
              </div>
            </div>
            <CheckCircle2 className="w-5 h-5 text-emerald-500 flex-shrink-0" />
          </div>
        )}

        {isUploading && (
          <div className="max-w-md mx-auto mb-4">
            <ProgressBar value={uploadProgress} label="Uploading file to parsing gateway..." showValue variant="primary" />
          </div>
        )}

        <Button
          variant="primary"
          size="lg"
          isLoading={isUploading}
          onClick={handleSimulatedUpload}
          icon={<ArrowRight className="w-4 h-4" />}
          iconPosition="right"
        >
          Begin ATS Parsing & Analysis
        </Button>
      </div>
    </div>
  );
}
