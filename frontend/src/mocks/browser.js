/**
 * CareerLens MSW Browser Worker Setup (for browser development/demo)
 */
import { setupWorker } from 'msw/browser';
import { handlers } from './handlers';

export const worker = setupWorker(...handlers);

/**
 * Start the browser worker if MSW is enabled
 */
export async function startWorker() {
  if (typeof window === 'undefined') return;

  try {
    await worker.start({
      onUnhandledRequest: 'bypass',
      serviceWorker: {
        url: '/mockServiceWorker.js',
      },
    });
    console.log('[MSW] CareerLens Mock Service Worker started successfully.');
  } catch (err) {
    console.warn('[MSW] Could not start worker:', err);
  }
}
