import React from 'react';
import { Clock, RefreshCcw, Activity } from 'lucide-react';
import { ActivityLog } from '../types';
import { TimelineSkeleton, WidgetErrorCard } from './Skeletons';
import { EmptyState } from '../../../shared/components/EmptyState';

interface ActivityTimelineProps {
  activity: ActivityLog[];
  onRefresh: () => void;
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
}

export function ActivityTimeline({ activity = [], onRefresh, loading, error, onRetry }: ActivityTimelineProps) {
  if (error) {
    return <WidgetErrorCard title="Unable to load activity feed" message={error} onRetry={onRetry} />;
  }

  if (loading) {
    return <TimelineSkeleton />;
  }

  const getRelativeTime = (dateStr: string) => {
    try {
      const now = new Date();
      const past = new Date(dateStr);
      const diffMs = now.getTime() - past.getTime();
      const diffMins = Math.floor(diffMs / (1000 * 60));
      const diffHours = Math.floor(diffMins / 60);
      const diffDays = Math.floor(diffHours / 24);

      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffHours < 24) return `${diffHours}h ago`;
      if (diffDays < 7) return `${diffDays}d ago`;
      return past.toLocaleDateString([], { month: 'short', day: 'numeric' });
    } catch (e) {
      return 'Recently';
    }
  };

  const getEventDescription = (type: string, meta: any) => {
    if (meta?.description) return meta.description;
    switch (type) {
      case 'Workspace Created':
        return 'Initialized new organization workspace context';
      case 'Project Created':
        return 'Created new project workspace';
      case 'Document Uploaded':
        return 'Uploaded and indexed knowledge document';
      case 'Document Deleted':
        return 'Removed document from knowledge base';
      case 'Document Restored':
        return 'Restored document to active status';
      case 'Invitation Accepted':
        return 'New member joined organization';
      case 'User Logged In':
        return 'Session authorized via JWT';
      default:
        return 'Organization event processed';
    }
  };

  return (
    <div className="glass-panel p-3.5 bg-bgCard border border-borderColor h-full rounded-2xl flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-2.5 pb-1.5 border-b border-borderMuted">
          <h2 className="text-xs font-semibold text-textPrimary tracking-wide flex items-center gap-2">
            <Clock size={15} className="text-accentText" aria-hidden="true" />
            <span>Organization Activity Feed</span>
          </h2>
          <button 
            type="button"
            onClick={onRefresh}
            aria-label="Refresh activity feed"
            title="Refresh activity feed"
            className="p-1 rounded-lg text-textMuted hover:text-accentText hover:bg-bgHover transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          >
            <RefreshCcw size={12} aria-hidden="true" />
          </button>
        </div>

        <div className="space-y-2.5 max-h-[300px] overflow-y-auto pr-1">
          {activity.length > 0 ? (
            activity.map((act) => (
              <div key={act.id} className="flex gap-3 items-start relative group">
                {/* Timeline Connector Line */}
                <div className="absolute left-1.5 top-3.5 bottom-0 w-[1px] bg-borderMuted group-last:bg-transparent" />

                <div className="h-3 w-3 rounded-full bg-accentSubtle border border-accent flex items-center justify-center mt-1 z-10 shrink-0">
                  <div className="h-1 w-1 rounded-full bg-accentText" />
                </div>
                
                <div className="text-xs">
                  <div className="font-semibold text-textPrimary group-hover:text-accentText transition-colors flex items-center gap-2">
                    <span>{act.event_type}</span>
                    <span className="text-[9px] text-textMuted font-normal">{getRelativeTime(act.created_at)}</span>
                  </div>
                  <div className="text-[10px] text-textMuted mt-0.5">
                    {getEventDescription(act.event_type, act.metadata)}
                  </div>
                </div>
              </div>
            ))
          ) : (
            <EmptyState
              title="No Activity Recorded"
              description="Real-time events like document uploads, project creation, and team invites will appear here."
              icon={Activity}
              variant="compact"
            />
          )}
        </div>
      </div>
    </div>
  );
}
