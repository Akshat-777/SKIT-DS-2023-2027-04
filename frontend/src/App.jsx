import React from 'react';
import { ToastProvider } from './components/ui/Toast';
import DemoPage from './components/DemoPage';

/**
 * CareerLens Main App Entry
 * Wraps application in ToastProvider and renders the master DemoPage dashboard.
 */
function App() {
  return (
    <ToastProvider>
      <DemoPage />
    </ToastProvider>
  );
}

export default App;
