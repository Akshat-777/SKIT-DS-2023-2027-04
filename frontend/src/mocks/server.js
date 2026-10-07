/**
 * CareerLens MSW Server Setup (Node environment for Vitest/RTL)
 */
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

export const server = setupServer(...handlers);
