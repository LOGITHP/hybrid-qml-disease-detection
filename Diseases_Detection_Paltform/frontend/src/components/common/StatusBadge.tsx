import React from 'react';

interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const normalized = (status || '').toLowerCase();

  let styles = 'bg-slate-100 text-slate-700 border-slate-200';

  if (['completed', 'active', 'healthy', 'low', 'online', 'approved'].includes(normalized)) {
    styles = 'bg-emerald-50 text-emerald-700 border-emerald-200';
  } else if (['running', 'planning', 'training', 'busy', 'medium'].includes(normalized)) {
    styles = 'bg-amber-50 text-amber-700 border-amber-200';
  } else if (['failed', 'unhealthy', 'high', 'offline', 'rejected', 'error'].includes(normalized)) {
    styles = 'bg-red-50 text-red-700 border-red-200';
  } else if (['vqc', 'quantum', 'noisy_simulator'].includes(normalized)) {
    styles = 'bg-quantum-50 text-quantum-700 border-quantum-200';
  } else if (['pending', 'queued', 'awaiting_approval'].includes(normalized)) {
    styles = 'bg-blue-50 text-blue-700 border-blue-200';
  }

  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs';

  return (
    <span className={`inline-flex items-center rounded-full font-medium border capitalize ${styles} ${sizeClasses}`}>
      <span className="w-1.5 h-1.5 rounded-full mr-1.5 bg-current opacity-70" />
      {status}
    </span>
  );
};
