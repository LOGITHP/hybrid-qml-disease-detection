import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Unable to Load Data',
  message = 'An unexpected error occurred while communicating with the backend gateway.',
  onRetry,
}) => {
  return (
    <div className="card-scientific border-red-200 bg-red-50/30 text-center py-10 px-6 flex flex-col items-center justify-center rounded-xl">
      <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center text-red-600 mb-3">
        <AlertCircle className="w-6 h-6" />
      </div>
      <h3 className="text-base font-semibold text-slate-900 mb-1">{title}</h3>
      <p className="text-sm text-slate-600 max-w-md mb-5">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="btn-secondary flex items-center space-x-2">
          <RefreshCw className="w-4 h-4 mr-2" />
          <span>Retry Connection</span>
        </button>
      )}
    </div>
  );
};
