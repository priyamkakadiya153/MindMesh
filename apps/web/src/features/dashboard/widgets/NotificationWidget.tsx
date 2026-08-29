import React from 'react';
import { Bell } from 'lucide-react';
import { Notification } from '../types';

interface NotificationWidgetProps {
  notifications: Notification[];
}

export function NotificationWidget({ notifications }: NotificationWidgetProps) {
  return (
    <div className="glass-panel p-5 bg-bgCard border border-borderColor h-full">
      <div className="flex items-center justify-between mb-4 pb-2 border-b border-borderMuted">
        <h3 className="text-sm font-semibold text-textPrimary tracking-wide flex items-center gap-2">
          <Bell size={16} className="text-accentText" />
          <span>Alerts Inbox</span>
        </h3>
      </div>

      <div className="space-y-3 max-h-[300px] overflow-y-auto pr-1">
        {notifications.map((n) => (
          <div key={n.id} className="p-3 bg-bgTertiary border border-borderMuted rounded-xl flex flex-col gap-1">
            <h4 className="text-xs font-semibold text-textPrimary">{n.title}</h4>
            <p className="text-[10px] text-textMuted leading-normal">{n.message}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
