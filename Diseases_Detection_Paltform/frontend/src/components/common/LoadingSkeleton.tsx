import React from 'react';

export const LoadingSkeleton: React.FC<{ rows?: number; type?: 'card' | 'table' | 'chart' }> = ({
  rows = 4,
  type = 'card',
}) => {
  if (type === 'table') {
    return (
      <div className="card-scientific animate-pulse space-y-4">
        <div className="h-6 bg-slate-200 rounded w-1/4"></div>
        <div className="space-y-3">
          {Array.from({ length: rows }).map((_, i) => (
            <div key={i} className="grid grid-cols-5 gap-4">
              <div className="h-4 bg-slate-200 rounded col-span-1"></div>
              <div className="h-4 bg-slate-200 rounded col-span-1"></div>
              <div className="h-4 bg-slate-200 rounded col-span-1"></div>
              <div className="h-4 bg-slate-200 rounded col-span-1"></div>
              <div className="h-4 bg-slate-200 rounded col-span-1"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (type === 'chart') {
    return (
      <div className="card-scientific animate-pulse space-y-4">
        <div className="h-5 bg-slate-200 rounded w-1/3"></div>
        <div className="h-64 bg-slate-100 rounded-lg flex items-center justify-center text-slate-300">
          Loading visualization...
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 animate-pulse">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="card-scientific space-y-3">
          <div className="h-3 bg-slate-200 rounded w-1/2"></div>
          <div className="h-8 bg-slate-200 rounded w-3/4"></div>
          <div className="h-3 bg-slate-200 rounded w-1/3"></div>
        </div>
      ))}
    </div>
  );
};
