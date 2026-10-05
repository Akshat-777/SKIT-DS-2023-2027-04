import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, FileText, CheckCircle2, Cpu, ArrowRight } from 'lucide-react';
import PageContainer from '../components/layout/PageContainer';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Card, { CardContent } from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import ProgressBar from '../components/ui/ProgressBar';
import { useToast } from '../components/ui/Toast';
import { resumeService } from '../services/resumeService';

export default function UploadPage() {
  const navigate = useNavigate();
  const toast = useToast();

  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState({
    name: 'Aarav_Sharma_Resume_2026.pdf',
    size: '1.4 MB',
    type: 'application/pdf',
  });
  const [targetRole, setTargetRole] = useState('Data Scientist / ML Engineer');
  const [ocrEnabled, setOcrEnabled] = useState(true);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setSelectedFile({
        name: file.name,
        size: `${(file.size / (1024 * 1024)).toFixed(2)} MB`,
        type: file.type,
        raw: file,
      });
      toast.info('File Selected', `Loaded ${file.name} for ingestion.`);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile({
        name: file.name,
        size: `${(file.size / (1024 * 1024)).toFixed(2)} MB`,
        type: file.type,
        raw: file,
      });
      toast.info('File Selected', `Loaded ${file.name} for ingestion.`);
    }
  };

  const handleUploadAndAnalyze = async () => {
    setIsUploading(true);
    setUploadProgress(10);

    try {
      const result = await resumeService.uploadResume(selectedFile.raw || selectedFile, {
        targetRole,
        ocrEnabled,
        onUploadProgress: (evt) => {
          if (evt.total) {
            setUploadProgress(Math.round((evt.loaded * 100) / evt.total));
          }
        },
      });

      setUploadProgress(100);
      toast.success(
        'Ingestion Complete',
        'Transformers NER extracted skills and candidate credentials.'
      );

      // Navigate to ATS & Skill Gap analysis page
      const resumeId = result.resume_id || 'mock-resume-101';
      navigate(`/analysis/${resumeId}`);
    } catch (err) {
      toast.error('Upload Failed', err.message || 'Error communicating with FastAPI backend.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <PageContainer>
      <div className="space-y-6">
        {/* Header Section */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="primary" size="sm">
                FR-001
              </Badge>
              <span className="text-2xs font-mono text-slate-500">FastAPI Ingestion Gateway</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-slate-100 tracking-tight">
              Upload Resume Document
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
              Supports text-extractable and scanned PDF/DOCX resumes with OCR fallback pipeline.
            </p>
          </div>

          <div className="flex items-center gap-2 text-2xs bg-slate-100 dark:bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700">
            <Cpu className="w-3.5 h-3.5 text-brand-500" />
            <span className="font-medium text-slate-700 dark:text-slate-300">
              Min 8GB RAM Cloud Server
            </span>
          </div>
        </div>

        {/* Target Role & OCR Configuration */}
        <Card variant="default">
          <CardContent className="p-5 space-y-4">
            <Input
              label="Target Job Role for Market Benchmarking"
              value={targetRole}
              onChange={(e) => setTargetRole(e.target.value)}
              placeholder="e.g. Data Scientist / ML Engineer"
              helperText="CareerLens will fetch live market demand signals and ATS benchmarks for this exact job title."
              required
            />

            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pt-2 border-t border-slate-100 dark:border-slate-800 text-xs">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="ocr-toggle"
                  checked={ocrEnabled}
                  onChange={(e) => setOcrEnabled(e.target.checked)}
                  className="rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                />
                <label
                  htmlFor="ocr-toggle"
                  className="text-slate-700 dark:text-slate-300 font-medium cursor-pointer"
                >
                  Enable OCR Fallback for scanned/image resumes (NLP Pipeline)
                </label>
              </div>
              <Badge variant="success" size="sm" dot>
                TrOCR Ready
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Drag & Drop Upload Zone */}
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          className={`relative border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center transition-all duration-200 ${
            dragActive
              ? 'border-brand-500 bg-brand-50/50 dark:bg-brand-950/30 ring-4 ring-brand-500/20'
              : 'border-slate-300 dark:border-slate-700 hover:border-brand-400 bg-white dark:bg-slate-850'
          }`}
        >
          <input
            type="file"
            id="file-input"
            accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            onChange={handleFileChange}
            className="hidden"
          />

          <div className="w-16 h-16 rounded-2xl bg-brand-50 dark:bg-brand-950/80 border border-brand-200 dark:border-brand-800 text-brand-600 dark:text-brand-400 mx-auto flex items-center justify-center mb-4 shadow-subtle">
            <UploadCloud className="w-8 h-8" />
          </div>

          <h3 className="text-base sm:text-lg font-bold text-slate-900 dark:text-slate-100 mb-1">
            Drag & Drop your resume here, or{' '}
            <label
              htmlFor="file-input"
              className="text-brand-600 dark:text-brand-400 cursor-pointer hover:underline"
            >
              browse files
            </label>
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mx-auto mb-4">
            Supported formats: PDF, DOCX (Max size: 10MB). Text-extractable or scanned documents.
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
                  <p className="text-2xs text-slate-500">
                    {selectedFile.size} • Ready for analysis
                  </p>
                </div>
              </div>
              <CheckCircle2 className="w-5 h-5 text-emerald-500 flex-shrink-0" />
            </div>
          )}

          {isUploading && (
            <div className="max-w-md mx-auto mb-4">
              <ProgressBar
                value={uploadProgress}
                label="Uploading to FastAPI NER pipeline..."
                showValue
                variant="primary"
              />
            </div>
          )}

          <Button
            variant="primary"
            size="lg"
            isLoading={isUploading}
            onClick={handleUploadAndAnalyze}
            icon={<ArrowRight className="w-4 h-4" />}
            iconPosition="right"
          >
            Begin ATS Parsing & Analysis
          </Button>
        </div>
      </div>
    </PageContainer>
  );
}
