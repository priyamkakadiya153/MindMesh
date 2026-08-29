import React from 'react';
import { Bell, Check, Trash, ShieldAlert } from 'lucide-react';
import { Notification } from '../types';
import { EmptyState } from '../../../shared/components/EmptyState';

import { TimelineSkeleton, WidgetErrorCard } from './Skeletons';

interface NotificationPanelProps {
  notifications: Notification[];
  onMarkAsRead: (id: string) => void;
  onDelete: (id: string) => void;
  onMarkAllRead?: () => void;
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
}

export function NotificationPanel({
  notifications = [],
  onMarkAsRead,
  onDelete,
  onMarkAllRead,
  loading,
  error,
  onRetry
}: NotificationPanelProps) {
  if (error) {
    return <WidgetErrorCard title="Unable to load notifications" message={error} onRetry={onRetry} />;
  }

  if (loading) {
    return <TimelineSkeleton />;
  }

  const list: Notification[] = Array.isArray(notifications)
    ? notifications
    : (notifications && Array.isArray((notifications as any).notifications)
      ? (notifications as any).notifications
      : []);

  const unreadCount = list.filter(n => !n.is_read).length;

  return (
    <div className="glass-panel p-3.5 bg-bgCard border border-borderColor h-full rounded-2xl">
      <div className="flex items-center justify-between mb-2.5 pb-1.5 border-b border-borderMuted">
        <h2 className="text-xs font-semibold text-textPrimary tracking-wide flex items-center gap-2">
          <Bell size={15} className="text-accentText" aria-hidden="true" />
          <span>Alerts & Notifications</span>
        </h2>
        <div className="flex items-center gap-2">
          {unreadCount > 0 && onMarkAllRead && (
            <button
              type="button"
              onClick={onMarkAllRead}
              className="text-[9px] text-accentText hover:underline font-semibold focus-visible:outline-none"
            >
              Mark all read
            </button>
          )}
          {unreadCount > 0 && (
            <span aria-live="polite" className="text-[9px] bg-accent text-white font-bold px-2 py-0.5 rounded-full">
              {unreadCount} Unread
            </span>
          )}
        </div>
      </div>

      <div className="space-y-1.5 max-h-[300px] overflow-y-auto pr-1" aria-live="polite">
        {list.length > 0 ? (
          list.map((notif) => (
            <div 
              key={notif.id} 
              className={`p-2.5 rounded-xl border transition-all flex items-start justify-between gap-2.5 ${
                notif.is_read 
                  ? 'bg-bgTertiary border-borderMuted opacity-60' 
                  : 'bg-accentSubtle border-accent/20'
              }`}
            >
              <div className="flex gap-2">
                <div className={`p-1.5 rounded-lg mt-0.5 ${
                  notif.priority === 'high' 
                    ? 'bg-dangerBg text-dangerText' 
                    : 'bg-accentSubtle text-accentText'
                }`} aria-hidden="true">
                  <ShieldAlert size={12} />
                </div>
                <div>
                  <h3 className={`text-xs font-semibold ${notif.is_read ? 'text-textMuted' : 'text-textPrimary'}`}>
                    {notif.title}
                  </h3>
                  <p className="text-[10px] text-textMuted mt-0.5 leading-relaxed">{notif.message}</p>
                  <span className="text-[8px] text-textMuted font-medium block mt-1">
                    {new Date(notif.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-1 shrink-0">
                {!notif.is_read && (
                  <button 
                    type="button"
                    onClick={() => onMarkAsRead(notif.id)}
                    aria-label={`Mark notification ${notif.title} as read`}
                    title="Mark as read"
                    className="p-1 rounded-lg bg-successBg hover:bg-emerald-600 text-successText hover:text-white transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
                  >
                    <Check size={10} aria-hidden="true" />
                  </button>
                )}
                <button 
                  type="button"
                  onClick={() => onDelete(notif.id)}
                  aria-label={`Delete notification ${notif.title}`}
                  title="Delete notification"
                  className="p-1 rounded-lg bg-dangerBg hover:bg-red-600 text-dangerText hover:text-white transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-dangerText"
                >
                  <Trash size={10} aria-hidden="true" />
                </button>
              </div>
            </div>
          ))
        ) : (
          <EmptyState
            title="You're all caught up"
            description="New mentions, replies, and updates will appear here."
            icon={Bell}
            variant="compact"
          />
        )}
      </div>
    </div>
  );
}
