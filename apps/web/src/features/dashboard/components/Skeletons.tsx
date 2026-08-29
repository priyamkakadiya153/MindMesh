import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export const WidgetSkeleton: React.FC<{ className?: string; height?: string }> = ({ 
  className = '', 
  height = 'h-24' 
}) => (
  <div className={`animate-pulse bg-bgTertiary border border-borderMuted rounded-xl p-3.5 flex flex-col justify-between ${height} ${className}`}>
    <div className="flex items-center justify-between">
      <div className="h-3 w-1/3 bg-borderMuted rounded"></div>
      <div className="h-6 w-6 bg-borderMuted rounded-lg"></div>
    </div>
    <div className="h-6 w-1/2 bg-borderMuted rounded mt-2"></div>
    <div className="h-2 w-3/4 bg-borderMuted rounded mt-2"></div>
  </div>
);

export const StatsSkeleton: React.FC = () => (
  <div className="grid grid-cols-[repeat(auto-fit,minmax(min(100%,200px),1fr))] gap-3 mb-3.5">
    {[1, 2, 3, 4].map((i) => (
      <div key={i} className="animate-pulse glass-panel p-3.5 bg-bgCard border border-borderColor rounded-xl flex flex-col justify-between h-24">
        <div className="flex items-start justify-between">
          <div className="space-y-1.5 w-full">
            <div className="h-2.5 w-20 bg-borderMuted rounded"></div>
            <div className="h-7 w-12 bg-borderMuted rounded"></div>
          </div>
          <div className="h-7 w-7 rounded-lg bg-borderMuted"></div>
        </div>
        <div className="h-2 w-28 bg-borderMuted rounded mt-2"></div>
      </div>
    ))}
  </div>
);

export const RecentListSkeleton: React.FC<{ title: string; count?: number }> = ({ title, count = 3 }) => (
  <div className="bg-bgCard border border-borderColor rounded-2xl p-3.5 shadow-sm flex flex-col justify-between h-full min-h-[220px]">
    <div>
      <div className="flex items-center justify-between mb-2.5 pb-1.5 border-b border-borderColor">
        <div className="h-4 w-28 bg-borderMuted rounded animate-pulse"></div>
        <div className="h-4 w-12 bg-borderMuted rounded-full animate-pulse"></div>
      </div>
      <div className="space-y-2">
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="p-2.5 bg-bgTertiary border border-borderMuted rounded-xl flex items-center justify-between animate-pulse">
            <div className="flex items-center gap-2.5 w-full">
              <div className="h-6 w-6 rounded-lg bg-borderMuted shrink-0"></div>
              <div className="space-y-1 w-2/3">
                <div className="h-3 bg-borderMuted rounded w-3/4"></div>
                <div className="h-2 bg-borderMuted rounded w-1/2"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  </div>
);

export const TimelineSkeleton: React.FC = () => (
  <div className="bg-bgCard border border-borderColor rounded-2xl p-3.5 shadow-sm flex flex-col justify-between h-full min-h-[220px]">
    <div className="flex items-center justify-between mb-2.5 pb-1.5 border-b border-borderColor">
      <div className="h-4 w-32 bg-borderMuted rounded animate-pulse"></div>
    </div>
    <div className="space-y-2.5">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="flex items-start gap-2.5 animate-pulse">
          <div className="h-6 w-6 rounded-full bg-borderMuted shrink-0"></div>
          <div className="space-y-1 w-full">
            <div className="h-3 bg-borderMuted rounded w-4/5"></div>
            <div className="h-2 bg-borderMuted rounded w-1/3"></div>
          </div>
        </div>
      ))}
    </div>
  </div>
);

export const AIInsightsSkeleton: React.FC = () => (
  <div className="bg-bgCard border border-borderColor rounded-2xl p-3.5 shadow-sm flex flex-col justify-between h-full min-h-[140px] animate-pulse">
    <div className="flex items-center gap-2 mb-2">
      <div className="h-6 w-6 rounded-lg bg-borderMuted"></div>
      <div className="h-4 w-24 bg-borderMuted rounded"></div>
    </div>
    <div className="space-y-1.5 my-2">
      <div className="h-3 bg-borderMuted rounded w-full"></div>
      <div className="h-3 bg-borderMuted rounded w-5/6"></div>
    </div>
    <div className="h-2 w-20 bg-borderMuted rounded"></div>
  </div>
);

export interface WidgetErrorCardProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export const WidgetErrorCard: React.FC<WidgetErrorCardProps> = ({
  title = "Failed to load data",
  message = "This widget could not retrieve data from the server.",
  onRetry
}) => (
  <div className="bg-bgCard border border-dangerBorder/30 rounded-2xl p-3.5 shadow-sm flex flex-col items-center justify-center text-center space-y-2.5 min-h-[140px]">
    <AlertTriangle size={24} className="text-dangerText" />
    <div>
      <h4 className="text-xs font-bold text-textPrimary">{title}</h4>
      <p className="text-[10px] text-textMuted max-w-xs">{message}</p>
    </div>
    {onRetry && (
      <button
        onClick={onRetry}
        className="px-3 py-1 bg-accentSubtle hover:bg-accent/20 text-accentText border border-accent/20 rounded-lg text-[10px] font-semibold flex items-center gap-1 transition-all"
      >
        <RefreshCw size={11} /> Retry
      </button>
    )}
  </div>
);
