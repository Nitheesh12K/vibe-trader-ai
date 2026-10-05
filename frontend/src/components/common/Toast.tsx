import React, { createContext, useContext, useState, useCallback } from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  AlertOctagon,
  Info,
  Sparkles,
  XCircle,
  X,
} from 'lucide-react';

export type ToastType = 'success' | 'warning' | 'risk' | 'info' | 'ai' | 'error';

export interface ToastItem {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number;
}

interface ToastContextType {
  showToast: (title: string, type?: ToastType, message?: string, duration?: number) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback(
    (title: string, type: ToastType = 'info', message?: string, duration: number = 4500) => {
      const id = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      setToasts((prev) => [...prev, { id, type, title, message, duration }]);

      if (duration > 0) {
        setTimeout(() => {
          removeToast(id);
        }, duration);
      }
    },
    [removeToast]
  );

  return (
    <ToastContext.Provider value={{ showToast, removeToast }}>
      {children}
      {/* Toast Notification Container */}
      <div
        aria-live="polite"
        aria-atomic="true"
        className="fixed bottom-4 right-4 z-50 flex flex-col gap-2.5 max-w-sm w-full pointer-events-none px-4 sm:px-0"
      >
        {toasts.map((toast) => {
          const { icon: Icon, border, bg, text, iconColor } = getToastStyles(toast.type);
          return (
            <div
              key={toast.id}
              role="alert"
              className={`pointer-events-auto flex items-start gap-3 p-3.5 rounded-xl border backdrop-blur-xl shadow-2xl transition-all duration-300 transform translate-y-0 ${bg} ${border} ${text}`}
            >
              <Icon className={`w-5 h-5 shrink-0 mt-0.5 ${iconColor}`} />
              <div className="flex-1 min-w-0">
                <div className="font-semibold text-xs text-white leading-snug">{toast.title}</div>
                {toast.message && (
                  <div className="text-[11px] text-slate-300 mt-0.5 leading-relaxed break-words">
                    {toast.message}
                  </div>
                )}
              </div>
              <button
                onClick={() => removeToast(toast.id)}
                aria-label="Dismiss notification"
                className="text-slate-400 hover:text-white p-0.5 rounded transition-colors shrink-0"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
};

export const useToast = (): ToastContextType => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

function getToastStyles(type: ToastType) {
  switch (type) {
    case 'success':
      return {
        icon: CheckCircle2,
        bg: 'bg-[#0D1E1E]/95',
        border: 'border-emerald-500/30',
        text: 'text-emerald-200',
        iconColor: 'text-emerald-400',
      };
    case 'risk':
    case 'error':
      return {
        icon: AlertOctagon,
        bg: 'bg-[#220E15]/95',
        border: 'border-rose-500/30',
        text: 'text-rose-200',
        iconColor: 'text-rose-400',
      };
    case 'warning':
      return {
        icon: AlertTriangle,
        bg: 'bg-[#22170B]/95',
        border: 'border-amber-500/30',
        text: 'text-amber-200',
        iconColor: 'text-amber-400',
      };
    case 'ai':
      return {
        icon: Sparkles,
        bg: 'bg-[#18112A]/95',
        border: 'border-indigo-500/30',
        text: 'text-indigo-200',
        iconColor: 'text-indigo-400',
      };
    case 'info':
    default:
      return {
        icon: Info,
        bg: 'bg-[#0E1626]/95',
        border: 'border-cyan-500/30',
        text: 'text-cyan-200',
        iconColor: 'text-cyan-400',
      };
  }
}
