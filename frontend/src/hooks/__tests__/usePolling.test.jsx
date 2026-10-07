import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { usePolling } from '../usePolling';

describe('usePolling Hook', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.clearAllTimers();
    vi.useRealTimers();
  });

  it('polls queryFn every interval until isTerminal condition is met', async () => {
    let callCount = 0;
    const queryFn = vi.fn().mockImplementation(async () => {
      callCount += 1;
      if (callCount < 3) {
        return { status: 'in_progress', step_index: callCount };
      }
      return { status: 'completed', step_index: 5, resume_id: 'res-123' };
    });

    const onSuccess = vi.fn();

    const { result } = renderHook(() =>
      usePolling({
        queryFn,
        interval: 2000,
        enabled: true,
        isTerminal: (res) => res?.status === 'completed',
        onSuccess,
      })
    );

    // Initial poll
    await act(async () => {
      await Promise.resolve();
    });
    expect(queryFn).toHaveBeenCalledTimes(1);
    expect(result.current.isPolling).toBe(true);

    // Fast-forward 2000ms
    await act(async () => {
      vi.advanceTimersByTime(2000);
      await Promise.resolve();
    });
    expect(queryFn).toHaveBeenCalledTimes(2);

    // Fast-forward another 2000ms to reach terminal status
    await act(async () => {
      vi.advanceTimersByTime(2000);
      await Promise.resolve();
    });
    expect(queryFn).toHaveBeenCalledTimes(3);
    expect(result.current.isPolling).toBe(false);
    expect(result.current.data?.status).toBe('completed');
    expect(onSuccess).toHaveBeenCalledWith(
      expect.objectContaining({ status: 'completed', resume_id: 'res-123' })
    );
  });

  it('triggers timeout error when maxAttempts is reached', async () => {
    const queryFn = vi.fn().mockResolvedValue({ status: 'in_progress' });
    const onError = vi.fn();

    const { result } = renderHook(() =>
      usePolling({
        queryFn,
        interval: 2000,
        maxAttempts: 3,
        enabled: true,
        isTerminal: (res) => res?.status === 'completed',
        onError,
      })
    );

    // 1st attempt
    await act(async () => {
      await Promise.resolve();
    });

    // 2nd attempt
    await act(async () => {
      vi.advanceTimersByTime(2000);
      await Promise.resolve();
    });

    // 3rd attempt
    await act(async () => {
      vi.advanceTimersByTime(2000);
      await Promise.resolve();
    });

    // 4th attempt exceeds maxAttempts=3 -> triggers timeout
    await act(async () => {
      vi.advanceTimersByTime(2000);
      await Promise.resolve();
    });

    expect(result.current.isPolling).toBe(false);
    expect(result.current.error).toEqual(
      expect.objectContaining({
        code: 'POLLING_TIMEOUT',
      })
    );
    expect(onError).toHaveBeenCalledWith(
      expect.objectContaining({ code: 'POLLING_TIMEOUT' })
    );
  });

  it('cleans up timers and aborts in-flight request when stopped or unmounted', async () => {
    const queryFn = vi.fn().mockResolvedValue({ status: 'in_progress' });

    const { result, unmount } = renderHook(() =>
      usePolling({
        queryFn,
        interval: 2000,
        enabled: true,
      })
    );

    await act(async () => {
      await Promise.resolve();
    });

    expect(result.current.isPolling).toBe(true);

    // Unmount hook
    unmount();

    // Advance time after unmount
    await act(async () => {
      vi.advanceTimersByTime(10000);
      await Promise.resolve();
    });

    // No further calls after unmount
    expect(queryFn).toHaveBeenCalledTimes(1);
  });
});
