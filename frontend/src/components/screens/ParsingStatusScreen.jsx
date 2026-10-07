import React, { useState } from 'react';
import { Cpu, CheckCircle2, AlertCircle, FileCheck, Layers, Sparkles, BookOpen, Briefcase, Zap } from 'lucide-react';
import Card, { CardHeader, CardTitle, CardContent } from '../ui/Card';
import Badge from '../ui/Badge';
import ProgressBar from '../ui/ProgressBar';
import Spinner from '../ui/Spinner';
import ErrorState from '../ui/ErrorState';
import EmptyState from '../ui/EmptyState';
import { mockParsedResume } from '../../data/mockData';

export default function ParsingStatusScreen({ state = 'success', data = mockParsedResume }) {
  const [activeStep, setActiveStep] = useState(4); // 1-4 pipeline steps

  const pipelineSteps = [
    { id: 1, title: 'Document OCR & Ingestion', desc: 'PyPDF / Tesseract text extraction', done: true },
    { id: 2, title: 'Hugging Face NER Model', desc: 'Entity extraction for Name, Education, Exp', done: true },
    { id: 3, title: 'Skill Taxonomy Classifier', desc: 'Classifying explicit vs implicit competencies', done: true },
    { id: 4, title: 'ChromaDB Vector Store', desc: 'Generating 384-d semantic embeddings', done: true },
  ];

  if (state === 'empty') {
    return (
      <EmptyState
        icon={Layers}
        title="No Resume Parsing In Progress"
        description="Please upload a resume file in the Upload tab to initiate the NER extraction pipeline."
        action={{ label: "Go to Resume Upload", onClick: () => {} }}
      />
    );
  }

  if (state === 'loading') {
    return (
      <div className="max-w-2xl mx-auto p-8 bg-white dark:bg-slate-850 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-6">
        <div className="flex items-center gap-3">
          <Spinner size="lg" color="brand" />
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
              Running Hugging Face Transformers NER...
            </h3>
            <p className="text-xs text-slate-500">Extracting named entities: EDUCATION, EXPERIENCE, SKILL taxonomy</p>
          </div>
        </div>
        <ProgressBar value={60} label="Step 2 of 4: Entity Recognition" showValue variant="primary" animated />
      </div>
    );
  }

  if (state === 'error') {
    return (
      <ErrorState
        error={{
          code: 'NER_EXTRACTION_FAILURE',
          message: 'The Hugging Face NER parser encountered malformed text encoding in the education section. Please verify the document encoding.'
        }}
        onRetry={() => {}}
        actionLabel="Retry Extraction Pipeline"
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight flex items-center gap-2">
            NER Parsing & Entity Extraction
            <Badge variant="primary" size="sm">FR-002</Badge>
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
            Structured candidate taxonomy extracted via Hugging Face Transformers + ChromaDB vector embeddings.
          </p>
        </div>
        <Badge variant="success" size="md" dot>
          Extraction Complete (1.8s)
        </Badge>
      </div>

      {/* 4-Step Pipeline Progression Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {pipelineSteps.map((step) => (
          <div
            key={step.id}
            className="p-4 rounded-xl border border-emerald-200 dark:border-emerald-800/60 bg-emerald-50/40 dark:bg-emerald-950/20 flex items-start gap-3 shadow-2xs"
          >
            <div className="w-7 h-7 rounded-full bg-emerald-500 text-white flex items-center justify-center flex-shrink-0 mt-0.5 text-xs font-bold">
              ✓
            </div>
            <div>
              <p className="text-xs font-bold text-slate-900 dark:text-slate-100 leading-tight">
                {step.title}
              </p>
              <p className="text-2xs text-slate-500 dark:text-slate-400 mt-1">
                {step.desc}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Parsed Output Grid (Shared ParsedResume Schema) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Candidate & Education */}
        <div className="space-y-6">
          {/* Identity Card */}
          <Card variant="default">
            <CardHeader className="flex items-center justify-between">
              <CardTitle>Candidate Overview</CardTitle>
              <Badge variant="outline" size="sm">ID: {data.resume_id}</Badge>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <span className="text-2xs font-semibold text-slate-400 uppercase tracking-wider">Candidate Name</span>
                <p className="text-base font-bold text-slate-900 dark:text-slate-100">{data.name}</p>
              </div>
              <div>
                <span className="text-2xs font-semibold text-slate-400 uppercase tracking-wider">Verified Email</span>
                <p className="text-xs font-mono text-brand-600 dark:text-brand-400">{data.email}</p>
              </div>
              <div className="pt-2 border-t border-slate-100 dark:border-slate-800">
                <span className="text-2xs font-semibold text-slate-400 uppercase tracking-wider">Detected Sections</span>
                <div className="flex flex-wrap gap-1.5 mt-1.5">
                  {Object.entries(data.sections).map(([section, present]) => (
                    <Badge key={section} variant={present ? 'success' : 'default'} size="sm">
                      {section}
                    </Badge>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Education Card */}
          <Card variant="default">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-brand-500" /> Education
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {data.education.map((edu, idx) => (
                <div key={idx} className="border-l-2 border-brand-500 pl-3 space-y-1">
                  <p className="text-xs font-bold text-slate-900 dark:text-slate-100">{edu.degree}</p>
                  <p className="text-xs text-slate-600 dark:text-slate-400">{edu.institution}</p>
                  <p className="text-2xs font-mono text-slate-400">{edu.year}</p>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Middle & Right Column: Experience & Classified Skills */}
        <div className="lg:col-span-2 space-y-6">
          {/* Work Experience */}
          <Card variant="default">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Briefcase className="w-4 h-4 text-brand-500" /> Extracted Work Experience
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {data.experience.map((exp, idx) => (
                <div key={idx} className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900/60 border border-slate-100 dark:border-slate-800 space-y-2">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                    <p className="text-sm font-bold text-slate-900 dark:text-slate-100">{exp.title}</p>
                    <Badge variant="outline" size="sm">{exp.start} — {exp.end}</Badge>
                  </div>
                  <p className="text-xs font-semibold text-brand-600 dark:text-brand-400">{exp.company}</p>
                  <ul className="list-disc list-inside space-y-1.5 text-xs text-slate-600 dark:text-slate-300 pt-2">
                    {exp.bullets.map((b, bIdx) => (
                      <li key={bIdx} className="leading-relaxed">{b}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Classified Skills Taxonomy */}
          <Card variant="default">
            <CardHeader className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="w-4 h-4 text-amber-500" /> Extracted Skills & Confidence
                </CardTitle>
                <p className="text-2xs text-slate-500 mt-0.5">Explicit (mentioned directly) vs Implicit (inferred from bullet accomplishments)</p>
              </div>
              <Badge variant="role" size="sm">{data.skills.length} Skills</Badge>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {data.skills.map((skill, sIdx) => (
                  <div
                    key={sIdx}
                    className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-850 hover:border-brand-300 dark:hover:border-brand-700 transition-colors space-y-1.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-900 dark:text-slate-100">{skill.name}</span>
                      <div className="flex items-center gap-1.5">
                        <Badge variant={skill.type === 'explicit' ? 'primary' : 'warning'} size="sm">
                          {skill.type}
                        </Badge>
                        <span className="font-mono text-2xs font-bold text-slate-500">
                          {Math.round(skill.confidence * 100)}%
                        </span>
                      </div>
                    </div>
                    <p className="text-2xs text-slate-500 dark:text-slate-400 line-clamp-2 italic">
                      "{skill.evidence}"
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
