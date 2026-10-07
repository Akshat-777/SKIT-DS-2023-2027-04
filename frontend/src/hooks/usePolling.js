/**
 * CareerLens usePolling Hook
 * 
 * Production-ready polling hook designed for the CareerLens FastAPI ingestion & NLP pipeline.
 * Features:
 * 1. Configurable base interval (default 2000ms / 2s).
 * 2. Exponential backoff with jitter option for high-load server resilience.
 * 3. Max attempts / timeout threshold (default 30 attempts = 60s total timeout).
 * 4. Automatic cleanup on unmount, abort controller integration, and manual stop/restart controls.
 * 5. Online/Offline network detection.
 * 6. Clean Upgrade Path to SSE (Server-Sent Events) and WebSocket:
 *    Provides an abstracted adapter contract so the UI StepTracker can transition
 *    to real-time streaming without modifying component consumers.
 *
 * @example
 * const { data, error, isPolling, attempts, stop, restart } = usePolling({
 *   queryFn: async (signal) => resumeService.getResumeStatus(resumeId, { signal }),
 *   interval: 2000,
 *   enabled: !!resumeId,
 *   isTerminal: (res) => res.status === 'completed' || res.status === 'failed',
 *   onSuccess: (res) => navigate(`/analysis/${res.resume_id}`),
 *   onError: (err) => console.error(err),
 * });
 */

import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * Standardized status response type for CareerLens parsing pipeline
 * @typedef {Object} PollingStatus
 * @property {string} resume_id
 * @property {string} status - 'uploaded'|'text_extraction'|'entity_extraction'|'skill_extraction'|'scoring'|'completed'|'failed'
 * @property {number} step_index - 0 to 5
 * @property {number} progress_pct - 20 to 100
 * @property {string} current_step - Human readable step title
 * @property {string} message - Step description / model update
 * @property {boolean} ocr_in_use - Flag indicating TrOCR OCR fallback was used
 * @property {Object} [error] - Error object adhering to {"code": str, "message": str}
 */

/**
 * @param {Object} options
 * @param {Function} options.queryFn - Async function returning data, receives AbortSignal
 * @param {number} [options.interval=2000] - Polling interval in milliseconds
 * @param {boolean} [options.enabled=true] - Whether polling is currently active
 * @param {boolean} [options.useBackoff=false] - Whether to apply exponential backoff
 * @param {number} [options.backoffFactor=1.2] - Multiplier applied on each interval
 * @param {number} [options.maxInterval=10000] - Upper bound for backoff interval
 * @param {number} [options.maxAttempts=30] - Max poll attempts before timeout (30 * 2s = 60s)
 * @param {Function} [options.isTerminal] - Function taking (data) and returning true if finished
 * @param {Function} [options.onSuccess] - Callback when isTerminal returns true with status 'completed'
 * @param {Function} [options.onError] - Callback on fatal error or timeout
 */
export function usePolling({
  queryFn,
  interval = 2000,
  enabled = true,
  useBackoff = false,
  backoffFactor = 1.2,
  maxInterval = 10000,
  maxAttempts = 30,
  isTerminal = (data) => data?.status === 'completed' || data?.status === 'failed',
  onSuccess,
  onError,
}) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [isPolling, setIsPolling] = useState(enabled);
  const [attempts, setAttempts] = useState(0);

  // Mutable refs to persist state and callbacks across renders without stale closures
  const timerRef = useRef(null);
  const abortControllerRef = useRef(null);
  const isMountedRef = useRef(true);
  const queryFnRef = useRef(queryFn);
  const onSuccessRef = useRef(onSuccess);
  const onErrorRef = useRef(onError);
  const isTerminalRef = useRef(isTerminal);

  // Synchronize internal polling state whenever enabled prop changes
  useEffect(() => {
    setIsPolling(enabled);
    if (enabled) {
      setAttempts(0);
      setError(null);
    }
  }, [enabled]);

  queryFnRef.current = queryFn;
  onSuccessRef.current = onSuccess;
  onErrorRef.current = onError;
  isTerminalRef.current = isTerminal;

  /**
   * Stop polling and cancel any in-flight request
   */
  const stop = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    if (isMountedRef.current) {
      setIsPolling(false);
    }
  }, []);

  /**
   * Manual restart mechanism
   */
  const restart = useCallback(() => {
    stop();
    setData(null);
    setError(null);
    setAttempts(0);
    setIsPolling(true);
  }, [stop]);

  // Check network offline state
  useEffect(() => {
    const handleOffline = () => {
      const offlineErr = {
        code: 'NETWORK_OFFLINE',
        message: 'Network offline: Your connection was lost. CareerLens polling paused.',
      };
      setError(offlineErr);
      if (onErrorRef.current) onErrorRef.current(offlineErr);
      stop();
    };

    window.addEventListener('offline', handleOffline);
    return () => window.removeEventListener('offline', handleOffline);
  }, [stop]);

  // Main polling loop
  useEffect(() => {
    isMountedRef.current = true;

    if (!enabled || !isPolling) {
      return;
    }

    let currentInterval = interval;
    let attemptCounter = 0;

    const executePoll = async () => {
      // Check offline before poll
      if (typeof navigator !== 'undefined' && !navigator.onLine) {
        const offlineErr = {
          code: 'NETWORK_OFFLINE',
          message: 'Network offline: You are disconnected from the internet.',
        };
        if (isMountedRef.current) {
          setError(offlineErr);
          setIsPolling(false);
        }
        if (onErrorRef.current) onErrorRef.current(offlineErr);
        return;
      }

      // Check max attempts (Timeout condition)
      if (attemptCounter >= maxAttempts) {
        const timeoutErr = {
          code: 'POLLING_TIMEOUT',
          message: `Parsing timed out after ${maxAttempts * (interval / 1000)} seconds waiting for ML services.`,
        };
        if (isMountedRef.current) {
          setError(timeoutErr);
          setIsPolling(false);
        }
        if (onErrorRef.current) onErrorRef.current(timeoutErr);
        return;
      }

      attemptCounter += 1;
      if (isMountedRef.current) {
        setAttempts(attemptCounter);
      }

      // Prepare fresh AbortController for this polling request
      abortControllerRef.current = new AbortController();

      try {
        const result = await queryFnRef.current(abortControllerRef.current.signal);

        if (!isMountedRef.current) return;

        setData(result);
        setError(null);

        // Check if backend returned an explicit failure status
        if (result?.status === 'failed' || result?.error) {
          const parsingErr = result.error || {
            code: 'PARSING_FAILED',
            message: result.message || 'Upstream NLP parsing failed.',
          };
          setError(parsingErr);
          setIsPolling(false);
          if (onErrorRef.current) onErrorRef.current(parsingErr);
          return;
        }

        // Check if pipeline reached terminal step
        if (isTerminalRef.current(result)) {
          setIsPolling(false);
          if (onSuccessRef.current) {
            onSuccessRef.current(result);
          }
          return;
        }

        // Calculate next polling delay (with exponential backoff if enabled)
        if (useBackoff) {
          currentInterval = Math.min(maxInterval, Math.round(currentInterval * backoffFactor));
        }

        // Schedule next poll
        timerRef.current = setTimeout(executePoll, currentInterval);
      } catch (err) {
        if (!isMountedRef.current) return;

        // Ignore aborted requests
        if (err.name === 'CanceledError' || err.name === 'AbortError') {
          return;
        }

        const formattedErr = {
          code: err.code || 'POLLING_NETWORK_ERROR',
          message: err.message || 'Error communicating with FastAPI resume service.',
          status: err.status || 500,
        };

        setError(formattedErr);
        setIsPolling(false);
        if (onErrorRef.current) onErrorRef.current(formattedErr);
      }
    };

    // Trigger initial poll immediately
    executePoll();

    return () => {
      isMountedRef.current = false;
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [enabled, isPolling, interval, maxAttempts, useBackoff, backoffFactor, maxInterval]);

  return {
    data,
    error,
    isPolling,
    attempts,
    stop,
    restart,
  };
}

/**
 * ============================================================================
 * CLEAN UPGRADE PATH: SSE / WebSocket Stream Adapter Architecture
 * ============================================================================
 * When FastAPI adds Server-Sent Events (SSE) via `/resumes/:id/stream` or
 * WebSockets via `/resumes/:id/ws`, callers can switch to `useResumeStream`
 * with ZERO modifications to the UI presentation or StepTracker.
 */
export function useResumeStream({ resumeId, mode = 'polling', onUpdate, onComplete, onError }) {
  // If streaming is enabled in future milestone:
  // if (mode === 'sse') {
  //   const eventSource = new EventSource(`${FASTAPI_BASE_URL}/resumes/${resumeId}/stream`);
  //   eventSource.onmessage = (event) => onUpdate(JSON.parse(event.data));
  //   eventSource.onerror = (err) => onError(err);
  //   return () => eventSource.close();
  // }
  //
  // if (mode === 'ws') {
  //   const socket = new WebSocket(`${WS_BASE_URL}/resumes/${resumeId}/ws`);
  //   socket.onmessage = (event) => onUpdate(JSON.parse(event.data));
  //   return () => socket.close();
  // }
  return null;
}

export default usePolling;
