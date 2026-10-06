import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import UploadPage from '../UploadPage';
import { setMockScenario, resetMockState } from '../../mocks/handlers';
import { ToastProvider } from '../../components/ui/Toast';
import { AuthProvider } from '../../context/AuthContext';

// Mock useNavigate from react-router-dom
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

function renderUploadPage(props = {}) {
  return render(
    <MemoryRouter initialEntries={['/upload']}>
      <AuthProvider>
        <ToastProvider>
          <UploadPage pollInterval={100} {...props} />
        </ToastProvider>
      </AuthProvider>
    </MemoryRouter>
  );
}

describe('UploadPage Integration Tests', () => {
  beforeEach(() => {
    resetMockState();
    mockNavigate.mockReset();
  });

  afterEach(() => {
    resetMockState();
  });

  it('renders initial upload view with role selector, dropzone, and OCR toggle', () => {
    renderUploadPage();

    expect(
      screen.getByRole('heading', { name: /resume ingestion & market benchmarking/i })
    ).toBeInTheDocument();
    expect(screen.getByTestId('target-role-trigger')).toBeInTheDocument();
    expect(screen.getByTestId('ocr-checkbox')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /upload resume file dropzone/i })).toBeInTheDocument();
    expect(screen.getByTestId('begin-analysis-button')).toBeDisabled();
  });

  it('allows searching and selecting a different target job role', async () => {
    const user = userEvent.setup();
    renderUploadPage();

    const trigger = screen.getByTestId('target-role-trigger');
    await user.click(trigger);

    expect(screen.getByTestId('target-role-listbox')).toBeInTheDocument();

    const searchInput = screen.getByTestId('target-role-search-input');
    await user.type(searchInput, 'MLOps');

    const mlopsOption = screen.getByText(/mlops & cloud infrastructure engineer/i);
    expect(mlopsOption).toBeInTheDocument();

    await user.click(mlopsOption);

    expect(trigger).toHaveTextContent(/mlops & cloud infrastructure engineer/i);
  });

  it('completes the full happy path: upload file -> progress -> step tracker -> auto navigate', async () => {
    setMockScenario('happy_path');
    renderUploadPage();

    const input = screen.getByTestId('resume-file-input');
    const validPdf = new File(['%PDF mock stream'], 'Aarav_Sharma_Resume.pdf', {
      type: 'application/pdf',
    });

    fireEvent.change(input, { target: { files: [validPdf] } });

    // File preview card should be rendered
    expect(screen.getByTestId('file-preview-card')).toBeInTheDocument();
    expect(screen.getByText('Aarav_Sharma_Resume.pdf')).toBeInTheDocument();

    // Begin analysis button is now enabled
    const beginBtn = screen.getByTestId('begin-analysis-button');
    expect(beginBtn).toBeEnabled();

    // Start upload
    fireEvent.click(beginBtn);

    // Should transition to step tracker
    await waitFor(
      () => {
        expect(screen.getByTestId('step-tracker-container')).toBeInTheDocument();
      },
      { timeout: 5000 }
    );

    // Verify 5-step items are present
    expect(screen.getByTestId('step-item-uploaded')).toBeInTheDocument();
    expect(screen.getByTestId('step-item-text_extraction')).toBeInTheDocument();
    expect(screen.getByTestId('step-item-entity_extraction')).toBeInTheDocument();
    expect(screen.getByTestId('step-item-skill_extraction')).toBeInTheDocument();
    expect(screen.getByTestId('step-item-scoring')).toBeInTheDocument();

    // Eventually auto-navigates on completion
    await waitFor(
      () => {
        expect(mockNavigate).toHaveBeenCalledWith(expect.stringMatching(/\/analysis\/res_/));
      },
      { timeout: 15000 }
    );
  }, 20000);

  it('displays "OCR in use for scanned document" notice when scenario is scanned_ocr', async () => {
    setMockScenario('scanned_ocr');
    renderUploadPage();

    const input = screen.getByTestId('resume-file-input');
    const scannedPdf = new File(['%PDF scanned stream'], 'Scanned_Marksheet_Resume.pdf', {
      type: 'application/pdf',
    });

    fireEvent.change(input, { target: { files: [scannedPdf] } });
    await screen.findByTestId('file-preview-card');
    const beginBtn = screen.getByTestId('begin-analysis-button');
    await waitFor(() => expect(beginBtn).toBeEnabled());
    fireEvent.click(beginBtn);

    // Wait for step-tracker and OCR banner
    await waitFor(
      () => {
        expect(screen.getByTestId('ocr-notice-banner')).toBeInTheDocument();
      },
      { timeout: 8000 }
    );

    expect(screen.getByText(/ocr in use for scanned document/i)).toBeInTheDocument();
    expect(screen.getByText(/TrOCR Active/i)).toBeInTheDocument();
  }, 15000);

  it('displays upload failure error card and allows retry when upload fails (500)', async () => {
    setMockScenario('upload_error');
    renderUploadPage();

    const input = screen.getByTestId('resume-file-input');
    const validPdf = new File(['%PDF stream'], 'Resume.pdf', { type: 'application/pdf' });

    fireEvent.change(input, { target: { files: [validPdf] } });
    await screen.findByTestId('file-preview-card');
    const beginBtn = screen.getByTestId('begin-analysis-button');
    await waitFor(() => expect(beginBtn).toBeEnabled());
    fireEvent.click(beginBtn);

    // Should display UploadErrorCard
    await waitFor(
      () => {
        expect(screen.getByTestId('upload-error-card')).toBeInTheDocument();
      },
      { timeout: 5000 }
    );

    expect(screen.getByTestId('error-code-badge')).toHaveTextContent(/UPLOAD_GATEWAY_ERROR/i);
    expect(screen.getByTestId('retry-error-button')).toBeInTheDocument();
    expect(screen.getByTestId('reupload-button')).toBeInTheDocument();
  });

  it('displays parsing failure error card when OCR extraction fails (502)', async () => {
    setMockScenario('step_ocr_error');
    renderUploadPage();

    const input = screen.getByTestId('resume-file-input');
    const validPdf = new File(['%PDF stream'], 'Resume.pdf', { type: 'application/pdf' });

    fireEvent.change(input, { target: { files: [validPdf] } });
    await screen.findByTestId('file-preview-card');
    const beginBtn = screen.getByTestId('begin-analysis-button');
    await waitFor(() => expect(beginBtn).toBeEnabled());
    fireEvent.click(beginBtn);

    // Wait for polling step failure
    await waitFor(
      () => {
        expect(screen.getByTestId('upload-error-card')).toBeInTheDocument();
      },
      { timeout: 8000 }
    );

    expect(screen.getByTestId('error-code-badge')).toHaveTextContent(/OCR_EXTRACTION_FAILED/i);
    expect(screen.getByTestId('retry-error-button')).toBeInTheDocument();
  }, 15000);
});
