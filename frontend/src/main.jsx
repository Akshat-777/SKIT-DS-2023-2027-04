import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App.jsx';
import { startWorker } from './mocks/browser';

// In development or when mock mode is requested, initialize MSW worker
if (import.meta.env.DEV || import.meta.env.VITE_USE_MOCK === 'true') {
  startWorker().catch((err) => console.warn('[CareerLens] MSW initial startup note:', err));
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>
);
