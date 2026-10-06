import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import FileDropzone, { formatBytes } from '../FileDropzone';

describe('FileDropzone Component', () => {
  it('formats bytes properly into KB and MB', () => {
    expect(formatBytes(0)).toBe('0 Bytes');
    expect(formatBytes(1024)).toBe('1 KB');
    expect(formatBytes(1.5 * 1024 * 1024)).toBe('1.5 MB');
    expect(formatBytes(5 * 1024 * 1024)).toBe('5 MB');
  });

  it('renders dropzone when no file is selected and is keyboard accessible', () => {
    render(
      <FileDropzone
        file={null}
        onFileSelect={vi.fn()}
        onFileRemove={vi.fn()}
        onError={vi.fn()}
      />
    );

    const dropzone = screen.getByRole('button', { name: /upload resume file dropzone/i });
    expect(dropzone).toBeInTheDocument();
    expect(dropzone).toHaveAttribute('tabIndex', '0');
    expect(screen.getByText(/drag & drop your resume here/i)).toBeInTheDocument();
    expect(screen.getByText(/choose file from device/i)).toBeInTheDocument();
  });

  it('rejects unsupported file formats (.png) with error code UNSUPPORTED_TYPE', async () => {
    const onError = vi.fn();
    const onFileSelect = vi.fn();

    render(
      <FileDropzone
        file={null}
        onFileSelect={onFileSelect}
        onFileRemove={vi.fn()}
        onError={onError}
      />
    );

    const input = screen.getByTestId('resume-file-input');
    const invalidFile = new File(['fake-png-content'], 'resume.png', { type: 'image/png' });

    fireEvent.change(input, { target: { files: [invalidFile] } });

    expect(onError).toHaveBeenCalledWith(
      expect.objectContaining({
        code: 'UNSUPPORTED_TYPE',
        message: expect.stringContaining('Unsupported file type'),
      })
    );
    expect(onFileSelect).not.toHaveBeenCalled();
  });

  it('rejects files exceeding 5MB with error code FILE_TOO_LARGE', async () => {
    const onError = vi.fn();
    const onFileSelect = vi.fn();

    render(
      <FileDropzone
        file={null}
        onFileSelect={onFileSelect}
        onFileRemove={vi.fn()}
        onError={onError}
      />
    );

    const input = screen.getByTestId('resume-file-input');
    // 6 MB file
    const oversizedBlob = new Blob(['x'.repeat(6 * 1024 * 1024)], { type: 'application/pdf' });
    const largeFile = new File([oversizedBlob], 'large_resume.pdf', { type: 'application/pdf' });

    fireEvent.change(input, { target: { files: [largeFile] } });

    expect(onError).toHaveBeenCalledWith(
      expect.objectContaining({
        code: 'FILE_TOO_LARGE',
        message: expect.stringContaining('5MB limit'),
      })
    );
    expect(onFileSelect).not.toHaveBeenCalled();
  });

  it('rejects empty (0-byte) files with error code EMPTY_OR_UNREADABLE', async () => {
    const onError = vi.fn();
    const onFileSelect = vi.fn();

    render(
      <FileDropzone
        file={null}
        onFileSelect={onFileSelect}
        onFileRemove={vi.fn()}
        onError={onError}
      />
    );

    const input = screen.getByTestId('resume-file-input');
    const emptyFile = new File([], 'empty_resume.pdf', { type: 'application/pdf' });

    fireEvent.change(input, { target: { files: [emptyFile] } });

    expect(onError).toHaveBeenCalledWith(
      expect.objectContaining({
        code: 'EMPTY_OR_UNREADABLE',
        message: expect.stringContaining('empty (0 bytes)'),
      })
    );
    expect(onFileSelect).not.toHaveBeenCalled();
  });

  it('accepts valid PDF file and fires onFileSelect', () => {
    const onFileSelect = vi.fn();
    const onError = vi.fn();

    render(
      <FileDropzone
        file={null}
        onFileSelect={onFileSelect}
        onFileRemove={vi.fn()}
        onError={onError}
      />
    );

    const input = screen.getByTestId('resume-file-input');
    const validPdf = new File(['%PDF-1.4 mock content'], 'Candidate_Resume.pdf', {
      type: 'application/pdf',
    });

    fireEvent.change(input, { target: { files: [validPdf] } });

    expect(onFileSelect).toHaveBeenCalledWith(validPdf);
    expect(onError).not.toHaveBeenCalled();
  });

  it('accepts valid DOCX file and fires onFileSelect', () => {
    const onFileSelect = vi.fn();
    const onError = vi.fn();

    render(
      <FileDropzone
        file={null}
        onFileSelect={onFileSelect}
        onFileRemove={vi.fn()}
        onError={onError}
      />
    );

    const input = screen.getByTestId('resume-file-input');
    const validDocx = new File(['PK mock zip docx'], 'Candidate_Resume.docx', {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    });

    fireEvent.change(input, { target: { files: [validDocx] } });

    expect(onFileSelect).toHaveBeenCalledWith(validDocx);
    expect(onError).not.toHaveBeenCalled();
  });

  it('displays preview card when file is selected and triggers onFileRemove', async () => {
    const user = userEvent.setup();
    const onFileRemove = vi.fn();

    const mockFile = new File(['%PDF sample'], 'Aarav_Sharma_Resume.pdf', {
      type: 'application/pdf',
    });

    render(
      <FileDropzone
        file={mockFile}
        onFileSelect={vi.fn()}
        onFileRemove={onFileRemove}
        onError={vi.fn()}
      />
    );

    expect(screen.getByTestId('file-preview-card')).toBeInTheDocument();
    expect(screen.getByText('Aarav_Sharma_Resume.pdf')).toBeInTheDocument();
    expect(screen.getByText(/portable document format/i)).toBeInTheDocument();

    const removeBtn = screen.getByTestId('remove-file-button');
    await user.click(removeBtn);

    expect(onFileRemove).toHaveBeenCalledTimes(1);
  });
});
