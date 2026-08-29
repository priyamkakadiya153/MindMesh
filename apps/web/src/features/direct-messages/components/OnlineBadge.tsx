import React from 'react';
import { PresenceStatus } from '../types';

interface OnlineBadgeProps {
  status: PresenceStatus;
  size?: 'sm' | 'md' | 'lg';
}

export const OnlineBadge: React.FC<OnlineBadgeProps> = ({ status, size = 'md' }) => {
  const sizeClasses = {
    sm: 'w-2 h-2',
    md: 'w-3 h-3',
    lg: 'w-4 h-4'
  };

  const statusColors = {
    online: 'bg-emerald-500 ring-2 ring-bgCard',
    away: 'bg-amber-500 ring-2 ring-bgCard',
    busy: 'bg-rose-500 ring-2 ring-bgCard',
    offline: 'bg-slate-400 ring-2 ring-bgCard'
  };

  return (
    <span
      aria-label={`Status: ${status}`}
      className={`block rounded-full ${sizeClasses[size]} ${statusColors[status] || statusColors.offline}`}
    />
  );
};
