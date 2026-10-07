/**
 * CareerLens useResume Hook
 * Manages resume upload state, progress tracking, and retrieval of ParsedResume entities.
 */

import { useState, useCallback } from 'react';
import { resumeService } from '../services/resumeService';

export function useResume() {
  const [resume, setResume] = useState(null);
  const [history, setHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState(null);

  /**
   * Upload resume document
   */
  const uploadResume = useCallback(async (file, options = {}) => {
    setIsLoading(true);
    setUploadProgress(0);
    setError(null);

    try {
      const result = await resumeService.uploadResume(file, {
        ...options,
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(percent);
          }
        },
      });

      setResume(result.parsed);
      return result;
    } catch (err) {
      setError(err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Fetch specific parsed resume
   */
  const fetchResume = useCallback(async (resumeId) => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await resumeService.getResume(resumeId);
      setResume(data);
      return data;
    } catch (err) {
      setError(err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Load history of uploads
   */
  const fetchHistory = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const list = await resumeService.getResumeHistory();
      setHistory(list);
      return list;
    } catch (err) {
      setError(err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    resume,
    history,
    isLoading,
    uploadProgress,
    error,
    uploadResume,
    fetchResume,
    fetchHistory,
  };
}

export default useResume;
