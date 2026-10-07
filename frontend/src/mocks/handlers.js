/**
 * CareerLens MSW (Mock Service Worker) Handlers
 * Simulates:
 * 1. POST /resumes/upload (with progress, abort capability, file validation)
 * 2. GET /resumes/:resumeId/status (step-by-step polling with 2s progression)
 * 3. Scenarios: Happy path, Scanned OCR doc, Upload failure, Corrupt file,
 *    OCR failure, NER failure, Scoring failure, Timeout.
 *
 * Conforms to shared API error contract: {"error": {"code": str, "message": str}}
 */

import { http, HttpResponse, delay } from 'msw';
import { mockParsedResume } from '../data/mockData';

// Shared state for simulation
let currentScenario = 'happy_path';
const resumePollCounters = new Map();

const isTest = typeof process !== 'undefined' && process.env?.NODE_ENV === 'test';

/**
 * Configure the active MSW scenario dynamically
 * @param {'happy_path'|'scanned_ocr'|'upload_error'|'corrupt_file'|'step_ocr_error'|'step_ner_error'|'step_scoring_error'|'timeout'} scenario
 */
export function setMockScenario(scenario) {
  currentScenario = scenario;
  resumePollCounters.clear();
  if (typeof window !== 'undefined' && window.localStorage) {
    window.localStorage.setItem('careerlens_msw_scenario', scenario);
  }
}

export function getMockScenario() {
  return currentScenario;
}

export function resetMockState() {
  currentScenario = 'happy_path';
  resumePollCounters.clear();
  if (typeof window !== 'undefined' && window.localStorage) {
    window.localStorage.removeItem('careerlens_msw_scenario');
  }
}

/**
 * Get active scenario from header, query param, localStorage, or state
 */
function resolveScenario(request) {
  const url = new URL(request.url);
  const queryScenario = url.searchParams.get('scenario');
  if (queryScenario) return queryScenario;

  const headerScenario = request.headers.get('x-careerlens-scenario');
  if (headerScenario) return headerScenario;

  if (currentScenario && currentScenario !== 'happy_path') {
    return currentScenario;
  }

  if (typeof window !== 'undefined' && window.localStorage) {
    const stored = window.localStorage.getItem('careerlens_msw_scenario');
    if (stored) return stored;
  }

  return currentScenario;
}

export const handlers = [
  // 1. POST /resumes/upload (and absolute FastAPI URL)
  http.post('*/resumes/upload', async ({ request }) => {
    const scenario = resolveScenario(request);

    // Simulate network latency in browser demos, instantaneous in tests
    if (!isTest) {
      await delay(350);
    }

    // Scenario: Upload Failure (Server Error 500)
    if (scenario === 'upload_error') {
      return HttpResponse.json(
        {
          error: {
            code: 'UPLOAD_GATEWAY_ERROR',
            message: 'FastAPI gateway failed to process incoming multipart file stream. Disk write error.',
          },
        },
        { status: 500 }
      );
    }

    // Scenario: Corrupt File (Unprocessable Entity 422)
    if (scenario === 'corrupt_file') {
      return HttpResponse.json(
        {
          error: {
            code: 'CORRUPTED_FILE_STREAM',
            message: 'Uploaded PDF file has invalid magic bytes or header is corrupted. PyMuPDF cannot read.',
          },
        },
        { status: 422 }
      );
    }

    // Happy path upload
    const resumeId = `res_${Date.now().toString(36)}`;
    resumePollCounters.set(resumeId, 0);

    return HttpResponse.json(
      {
        resume_id: resumeId,
        status: 'uploaded',
        message: 'Resume document received and validated by FastAPI ingestion gateway.',
        created_at: new Date().toISOString(),
      },
      { status: 200 }
    );
  }),

  // 2. GET /resumes/:resumeId/status (and absolute URL)
  http.get('*/resumes/:resumeId/status', async ({ request, params }) => {
    const { resumeId } = params;
    const scenario = resolveScenario(request);

    // Simulate slight API latency in browser demo
    if (!isTest) {
      await delay(100);
    }

    // If scenario is timeout, delay excessively or keep at 0
    if (scenario === 'timeout') {
      return HttpResponse.json({
        resume_id: resumeId,
        status: 'text_extraction',
        step_index: 1,
        progress_pct: 35,
        current_step: 'Text extraction/OCR',
        message: 'Pipeline queue overloaded; waiting for GPU compute worker...',
        ocr_in_use: false,
      });
    }

    const currentCount = resumePollCounters.get(resumeId) || 0;
    resumePollCounters.set(resumeId, currentCount + 1);

    const isScanned = scenario === 'scanned_ocr';

    // Step 0: Uploaded (Poll count 0)
    if (currentCount === 0) {
      return HttpResponse.json({
        resume_id: resumeId,
        status: 'uploaded',
        step_index: 0,
        progress_pct: 20,
        current_step: 'Uploaded',
        message: 'File checksum verified. Sending to NLP text extraction worker...',
        ocr_in_use: isScanned,
      });
    }

    // Step 1: Text extraction / OCR (Poll count 1)
    if (currentCount === 1) {
      if (scenario === 'step_ocr_error') {
        return HttpResponse.json(
          {
            error: {
              code: 'OCR_EXTRACTION_FAILED',
              message: 'TrOCR pipeline failed: Document scan resolution is below the 150 DPI threshold.',
            },
          },
          { status: 502 }
        );
      }

      return HttpResponse.json({
        resume_id: resumeId,
        status: 'text_extraction',
        step_index: 1,
        progress_pct: 40,
        current_step: 'Text extraction/OCR',
        message: isScanned
          ? 'Scanned document detected: Running TrOCR character recognition...'
          : 'Extracting text streams and formatting layout with PyMuPDF...',
        ocr_in_use: isScanned,
      });
    }

    // Step 2: Entity extraction (Poll count 2)
    if (currentCount === 2) {
      if (scenario === 'step_ner_error') {
        return HttpResponse.json(
          {
            error: {
              code: 'NER_EXTRACTION_FAILED',
              message: 'Hugging Face Transformer NER pipeline crashed on out-of-vocabulary candidate tokens.',
            },
          },
          { status: 500 }
        );
      }

      return HttpResponse.json({
        resume_id: resumeId,
        status: 'entity_extraction',
        step_index: 2,
        progress_pct: 60,
        current_step: 'Entity extraction',
        message: 'Isolating candidate name, education, work experience, and bullet points...',
        ocr_in_use: isScanned,
      });
    }

    // Step 3: Skill extraction (Poll count 3)
    if (currentCount === 3) {
      return HttpResponse.json({
        resume_id: resumeId,
        status: 'skill_extraction',
        step_index: 3,
        progress_pct: 80,
        current_step: 'Skill extraction',
        message: 'Classifying explicit & implicit skills and computing confidence scores...',
        ocr_in_use: isScanned,
      });
    }

    // Step 4: Scoring (Poll count 4)
    if (currentCount === 4) {
      if (scenario === 'step_scoring_error') {
        return HttpResponse.json(
          {
            error: {
              code: 'SCORING_SERVICE_UNAVAILABLE',
              message: 'LightGBM scoring & market-fit prediction service timed out or unavailable.',
            },
          },
          { status: 504 }
        );
      }

      return HttpResponse.json({
        resume_id: resumeId,
        status: 'scoring',
        step_index: 4,
        progress_pct: 95,
        current_step: 'Scoring',
        message: 'Comparing candidate skills against live job-market demand index in ChromaDB...',
        ocr_in_use: isScanned,
      });
    }

    // Final Step: Completed (Poll count 5+)
    return HttpResponse.json({
      resume_id: resumeId,
      status: 'completed',
      step_index: 5,
      progress_pct: 100,
      current_step: 'Completed',
      message: 'Analysis complete! LightGBM predictions and ATS scores generated.',
      ocr_in_use: isScanned,
    });
  }),

  // 3. GET /resumes/:resumeId (and absolute URL)
  http.get('*/resumes/:resumeId', async ({ params, request }) => {
    const { resumeId } = params;
    const currentCount = resumePollCounters.get(resumeId) || 0;
    if (currentCount < 5 && request.headers.get('accept')?.includes('application/json')) {
      return HttpResponse.json({
        resume_id: resumeId,
        status: currentCount === 0 ? 'uploaded' : 'in_progress',
        progress_pct: Math.min(100, (currentCount + 1) * 20),
        message: 'Processing resume in NLP pipeline...',
      });
    }

    return HttpResponse.json({
      ...mockParsedResume,
      resume_id: resumeId,
    });
  }),
];
