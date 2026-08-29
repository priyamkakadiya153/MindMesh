import React from 'react';
import { Clock } from 'lucide-react';
import { ActivityLog } from '../types';

interface ActivityWidgetProps {
  activity: ActivityLog[];
}

export function ActivityWidget({ activity }: ActivityWidgetProps) {
  return (
    <div className="glass-panel p-5 bg-bgCard border border-borderColor h-full">
      <div className="flex items-center justify-between mb-4 pb-2 border-b border-borderMuted">
        <h3 className="text-sm font-semibold text-textPrimary tracking-wide flex items-center gap-2">
          <Clock size={16} className="text-accentText" />
          <span>Activity Feed</span>
        </h3>
      </div>

      <div className="space-y-4 max-h-[300px] overflow-y-auto pr-1">
        {activity.map((act) => (
          <div key={act.id} className="flex gap-3 items-start relative group">
            <div className="absolute left-1.5 top-3.5 bottom-0 w-[1px] bg-borderMuted" />
            <div className="h-3 w-3 rounded-full bg-accentSubtle border border-accent flex items-center justify-center mt-1 z-10 shrink-0">
              <div className="h-1 w-1 rounded-full bg-accentText" />
            </div>
            
            <div className="text-xs">
              <div className="font-semibold text-textPrimary">{act.event_type}</div>
              <span className="text-[8px] text-textMuted font-medium block mt-1">
                {new Date(act.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
