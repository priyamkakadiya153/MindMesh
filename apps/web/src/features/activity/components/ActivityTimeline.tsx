import React, { useState, useEffect } from 'react';
import { ActivityItem, getActivityFeed } from '../../notifications/notifications-api';
import { Activity, Clock, User, FileText, Folder, MessageSquare, Loader2 } from 'lucide-react';

interface ActivityTimelineProps {
  organizationId: string;
  token?: string;
}

export const ActivityTimeline: React.FC<ActivityTimelineProps> = ({ organizationId, token }) => {
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!organizationId) return;
    setIsLoading(true);
    getActivityFeed(organizationId, token)
      .then(setActivities)
      .catch(err => console.error('Failed to fetch activity feed:', err))
      .finally(() => setIsLoading(false));
  }, [organizationId, token]);

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'file': return <FileText className="w-4 h-4 text-emerald-400" />;
      case 'project': return <Folder className="w-4 h-4 text-purple-400" />;
      case 'message': return <MessageSquare className="w-4 h-4 text-blue-400" />;
      default: return <User className="w-4 h-4 text-slate-400" />;
    }
  };

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-4 select-none space-y-4">
      <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
        <Activity className="w-5 h-5 text-indigo-400" />
        <h3 className="text-sm font-semibold text-slate-100">Activity Timeline</h3>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-8 text-xs text-slate-500">
          <Loader2 className="w-4 h-4 animate-spin mr-2" />
          Loading activity feed...
        </div>
      ) : activities.length === 0 ? (
        <div className="py-8 text-center text-xs text-slate-500">
          No recent activity recorded
        </div>
      ) : (
        <div className="relative pl-6 space-y-4 before:absolute before:left-2 font-medium text-xs text-slate-300 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
          {activities.map(act => (
            <div key={act.id} className="relative flex items-start space-x-3">
              <div className="absolute -left-6 p-1 bg-slate-900 border border-slate-700 rounded-full">
                {getActivityIcon(act.entity_type)}
              </div>
              <div className="flex-1 bg-slate-800/40 border border-slate-800 p-2.5 rounded-xl space-y-1">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="font-semibold text-slate-200">{act.user_name || 'User'}</span>
                  <span className="text-[9px] text-slate-500">{new Date(act.created_at).toLocaleString()}</span>
                </div>
                <p className="text-xs text-slate-300">{act.action}</p>
                {act.details && <p className="text-[10px] text-slate-500 font-mono">{act.details}</p>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
