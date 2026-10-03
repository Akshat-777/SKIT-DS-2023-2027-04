import React, { createContext, useContext, useState, useCallback } from 'react';
import { CheckCircle2, AlertTriangle, AlertOctagon, Info, X } from 'lucide-react';

const ToastContext = createContext(null);

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback(({ title, message, type = 'info', duration = 4000 }) => {
    const id = Date.now() + Math.random().toString(36).substring(2, 9);
    const newToast = { id, title, message, type, duration };

    setToasts((prev) => [...prev, newToast]);

    if (duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, duration);
    }
    return id;
  }, []);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toastMethods = {
    toast: addToast,
    success: (title, message, duration) => addToast({ title, message, type: 'success', duration }),
    error: (title, message, duration) => addToast({ title, message, type: 'error', duration }),
    warning: (title, message, duration) => addToast({ title, message, type: 'warning', duration }),
    info: (title, message, duration) => addToast({ title, message, type: 'info', duration }),
    dismiss: removeToast,
  };

  return (
    <ToastContext.Provider value={toastMethods}>
      {children}
      {/* Toast Render Portal / Container */}
      <div
        aria-live="polite"
        className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none"
      >
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} onDismiss={() => removeToast(toast.id)} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}

function ToastItem({ toast, onDismiss }) {
  const { title, message, type } = toast;

  const typeConfig = {
    success: {
      icon: <CheckCircle2 className="w-5 h-5 text-emerald-500" />,
      border: 'border-emerald-500/30',
      bg: 'bg-white dark:bg-slate-900',
    },
    error: {
      icon: <AlertOctagon className="w-5 h-5 text-rose-500" />,
      border: 'border-rose-500/30',
      bg: 'bg-white dark:bg-slate-900',
    },
    warning: {
      icon: <AlertTriangle className="w-5 h-5 text-amber-500" />,
      border: 'border-amber-500/30',
      bg: 'bg-white dark:bg-slate-900',
    },
    info: {
      icon: <Info className="w-5 h-5 text-sky-500" />,
      border: 'border-sky-500/30',
      bg: 'bg-white dark:bg-slate-900',
    },
  };

  const config = typeConfig[type] || typeConfig.info;

  return (
    <div
      role="alert"
      className={`pointer-events-auto p-4 rounded-xl shadow-modal border ${config.border} ${config.bg} flex items-start gap-3 transform transition-all duration-200 animate-in slide-in-from-bottom-3`}
    >
      <div className="flex-shrink-0 mt-0.5">{config.icon}</div>
      <div className="flex-1">
        {title && (
          <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100">
            {title}
          </h4>
        )}
        {message && (
          <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5 leading-relaxed">
            {message}
          </p>
        )}
      </div>
      <button
        type="button"
        onClick={onDismiss}
        aria-label="Dismiss notification"
        className="flex-shrink-0 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1 rounded-md transition-colors"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}

export default ToastProvider;
