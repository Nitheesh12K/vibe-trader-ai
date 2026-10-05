import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface ErrorBannerProps {
  message: string;
  onRetry?: () => void;
  title?: string;
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({
  message,
  onRetry,
  title = 'Data Connection Error',
}) => {
  return (
    <div className="bg-rose-500/10 border border-rose-500/30 rounded-lg p-4 my-2 text-rose-200">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-400 mt-0.5 shrink-0" />
          <div>
            <h4 className="font-semibold text-sm text-rose-300">{title}</h4>
            <p className="text-xs text-rose-300/80 mt-1">{message}</p>
          </div>
        </div>
        {onRetry && (
          <button
            onClick={onRetry}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-rose-500/20 hover:bg-rose-500/30 border border-rose-500/40 rounded transition-colors text-rose-100 shrink-0"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Retry
          </button>
        )}
      </div>
    </div>
  );
};
