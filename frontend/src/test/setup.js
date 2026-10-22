import '@testing-library/jest-dom';
import { beforeAll, afterEach, afterAll } from 'vitest';
import { server } from '../mocks/server';

// Polyfill ResizeObserver for Recharts ResponsiveContainer in jsdom
if (typeof window !== 'undefined' && !window.ResizeObserver) {
  window.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
}

// Establish API mocking before all tests
beforeAll(() => {
  if (typeof window !== 'undefined') {
    window.__MSW_ACTIVE__ = true;
  }
  server.listen({ onUnhandledRequest: 'bypass' });
});

// Reset any runtime request handlers added during tests
afterEach(() => server.resetHandlers());

// Clean up once tests are done
afterAll(() => {
  server.close();
  if (typeof window !== 'undefined') {
    delete window.__MSW_ACTIVE__;
  }
});
