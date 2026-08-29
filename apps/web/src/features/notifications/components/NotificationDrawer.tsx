import React, { useState, useEffect, useRef } from 'react';
import { useNotificationStore } from '../store';
import { useAuth } from '../../auth/auth-provider';
import { useWorkspaceStore } from '../../workspace/store';
import { NotificationItem } from '../notifications-api';
import { EmptyState } from '../../../shared/components/EmptyState';
import {
  Bell, X, CheckCheck, MessageSquare, AtSign, UserPlus, FileText,
  Info, Loader2, LayoutDashboard, Check, Trash2, Building2, ChevronRight, Filter
} from 'lucide-react';

interface NotificationDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigate?: (tab: string) => void;
}

export const NotificationDrawer: React.FC<NotificationDrawerProps> = ({
  isOpen,
  onClose,
  onNavigate
}) => {
  const { token, refreshUserOrganizations } = useAuth();
  const { fetchWorkspaces } = useWorkspaceStore();
  const {
    notifications,
    userInvitations,
    unreadCount,
    loading,
    fetchNotifications,
    fetchUserInvitations,
    markRead,
    markAllRead,
    deleteNotif,
    acceptInvitation,
    declineInvitation
  } = useNotificationStore();

  const [activeFilter, setActiveFilter] = useState<'all' | 'unread' | 'invitations'>('all');
  const [processingId, setProcessingId] = useState<string | null>(null);
  const drawerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      fetchNotifications(token || undefined);
      fetchUserInvitations(token || undefined);
    }
  }, [isOpen, token]);

  // ESC Key listener and outside click handler
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleAccept = async (invitationIdOrToken: string, notifId?: string) => {
    setProcessingId(invitationIdOrToken);
    try {
      await acceptInvitation(invitationIdOrToken, token || undefined);
      if (notifId) await markRead(notifId, token || undefined);
      if (refreshUserOrganizations) await refreshUserOrganizations();
      await fetchWorkspaces(token || '', '');
      if (onNavigate) onNavigate('dashboard');
    } catch (err: any) {
      alert(err.message || 'Failed to accept invitation');
    } finally {
      setProcessingId(null);
    }
  };

  const handleDecline = async (invitationIdOrToken: string, notifId?: string) => {
    setProcessingId(invitationIdOrToken);
    try {
      await declineInvitation(invitationIdOrToken, token || undefined);
      if (notifId) await markRead(notifId, token || undefined);
    } catch (err: any) {
      alert(err.message || 'Failed to decline invitation');
    } finally {
      setProcessingId(null);
    }
  };

  const filteredNotifications = notifications.filter(n => {
    if (activeFilter === 'unread') return !n.is_read;
    if (activeFilter === 'invitations') return n.type === 'invitation';
    return true;
  });

  // Group notifications by Today, Yesterday, Earlier
  const groupNotifications = (items: NotificationItem[]) => {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
    const yesterday = today - 86400000;

    const groups: { today: NotificationItem[]; yesterday: NotificationItem[]; earlier: NotificationItem[] } = {
      today: [],
      yesterday: [],
      earlier: []
    };

    items.forEach(item => {
      const itemTime = new Date(item.created_at).getTime();
      if (itemTime >= today) {
        groups.today.push(item);
      } else if (itemTime >= yesterday) {
        groups.yesterday.push(item);
      } else {
        groups.earlier.push(item);
      }
    });

    return groups;
  };

  const grouped = groupNotifications(filteredNotifications);

  const getNotifIcon = (type: string) => {
    switch (type) {
      case 'invitation': return <Building2 className="w-4 h-4 text-accentText" />;
      case 'mention': return <AtSign className="w-4 h-4 text-blue-400" />;
      case 'new_message': return <MessageSquare className="w-4 h-4 text-emerald-400" />;
      case 'file_uploaded': return <FileText className="w-4 h-4 text-amber-400" />;
      default: return <Info className="w-4 h-4 text-slate-400" />;
    }
  };

  const formatTimestamp = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
  };

  return (
    <aside 
      role="dialog"
      aria-modal="true"
      aria-label="Notifications Drawer"
      className="fixed inset-0 bg-bgOverlay/60 backdrop-blur-xs z-50 flex justify-end transition-opacity duration-200 animate-fadeIn"
    >
      {/* Overlay Backdrop Click */}
      <div className="absolute inset-0" onClick={onClose} aria-hidden="true" />

      {/* Slide-over Drawer Panel */}
      <div
        ref={drawerRef}
        className="relative w-full max-w-md bg-bgSidebar border-l border-borderColor h-full flex flex-col shadow-2xl z-10 animate-slideInRight"
      >
        {/* Drawer Header */}
        <div className="p-4 border-b border-borderColor flex flex-col gap-3 bg-bgCard/50">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="p-2 rounded-xl bg-accent/10 border border-accent/20" aria-hidden="true">
                <Bell className="w-4 h-4 text-accentText" />
              </div>
              <div>
                <h3 className="font-bold text-textPrimary text-sm flex items-center gap-2">
                  Notifications
                  {unreadCount > 0 && (
                    <span aria-live="polite" className="bg-accent text-white text-[10px] font-extrabold px-2 py-0.5 rounded-full">
                      {unreadCount}
                    </span>
                  )}
                </h3>
                <p className="text-[11px] text-textMuted">Stay updated with team invites & alerts</p>
              </div>
            </div>

            <div className="flex items-center space-x-1">
              {unreadCount > 0 && (
                <button
                  type="button"
                  onClick={() => markAllRead(token || undefined)}
                  className="px-2.5 py-1.5 hover:bg-bgHover text-textMuted hover:text-accentText focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent rounded-lg text-xs font-medium flex items-center gap-1 transition-colors"
                  aria-label="Mark all notifications as read"
                  title="Mark all as read"
                >
                  <CheckCheck className="w-3.5 h-3.5" aria-hidden="true" />
                  <span className="hidden sm:inline">Mark read</span>
                </button>
              )}
              <button
                type="button"
                onClick={onClose}
                aria-label="Close notifications drawer"
                title="Close dialog"
                className="p-1.5 text-textMuted hover:text-textPrimary hover:bg-bgHover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent rounded-xl transition-colors"
              >
                <X className="w-4 h-4" aria-hidden="true" />
              </button>
            </div>
          </div>

          {/* Filter Tabs */}
          <div role="tablist" aria-label="Notification filters" className="flex items-center gap-1.5 p-1 bg-bgInput rounded-xl border border-borderColor text-xs">
            <button
              type="button"
              role="tab"
              aria-selected={activeFilter === 'all'}
              onClick={() => setActiveFilter('all')}
              className={`flex-1 py-1.5 rounded-lg font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
                activeFilter === 'all'
                  ? 'bg-bgCard text-textPrimary shadow-sm border border-borderColor'
                  : 'text-textMuted hover:text-textPrimary'
              }`}
            >
              All ({notifications.length})
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={activeFilter === 'unread'}
              onClick={() => setActiveFilter('unread')}
              className={`flex-1 py-1.5 rounded-lg font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
                activeFilter === 'unread'
                  ? 'bg-bgCard text-textPrimary shadow-sm border border-borderColor'
                  : 'text-textMuted hover:text-textPrimary'
              }`}
            >
              Unread ({unreadCount})
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={activeFilter === 'invitations'}
              onClick={() => setActiveFilter('invitations')}
              className={`flex-1 py-1.5 rounded-lg font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
                activeFilter === 'invitations'
                  ? 'bg-bgCard text-textPrimary shadow-sm border border-borderColor'
                  : 'text-textMuted hover:text-textPrimary'
              }`}
            >
              Invites ({userInvitations.length})
            </button>
          </div>
        </div>

        {/* Notifications Scroll Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-5">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-20 text-xs text-textMuted space-y-2">
              <Loader2 className="w-6 h-6 animate-spin text-accent" />
              <span>Fetching latest notifications...</span>
            </div>
          ) : filteredNotifications.length === 0 && userInvitations.length === 0 ? (
            <EmptyState
              title="You're all caught up!"
              description="No new organization invitations, mentions, or system notifications."
              icon={Bell}
              variant="compact"
            />
          ) : (
            <>
              {/* Group: Today */}
              {grouped.today.length > 0 && (
                <div className="space-y-2.5">
                  <h4 className="text-[11px] font-bold text-textMuted uppercase tracking-wider px-1">Today</h4>
                  {grouped.today.map(notif => renderNotificationCard(notif))}
                </div>
              )}

              {/* Group: Yesterday */}
              {grouped.yesterday.length > 0 && (
                <div className="space-y-2.5">
                  <h4 className="text-[11px] font-bold text-textMuted uppercase tracking-wider px-1">Yesterday</h4>
                  {grouped.yesterday.map(notif => renderNotificationCard(notif))}
                </div>
              )}

              {/* Group: Earlier */}
              {grouped.earlier.length > 0 && (
                <div className="space-y-2.5">
                  <h4 className="text-[11px] font-bold text-textMuted uppercase tracking-wider px-1">Earlier</h4>
                  {grouped.earlier.map(notif => renderNotificationCard(notif))}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </aside>
  );

  function renderNotificationCard(notif: NotificationItem) {
    const isInvitation = notif.type === 'invitation';
    const isProcessing = processingId === (notif.entity_id || notif.id);

    return (
      <div
        key={notif.id}
        className={`p-3.5 rounded-2xl border transition-all space-y-2.5 ${
          notif.is_read
            ? 'bg-bgCard/60 border-borderColor/60 opacity-80'
            : 'bg-accent/5 border-accent/30 shadow-sm hover:border-accent/50'
        }`}
      >
        <div className="flex items-start space-x-3">
          <div className="p-2 rounded-xl bg-bgInput border border-borderColor shrink-0 mt-0.5">
            {getNotifIcon(notif.type)}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between text-xs gap-2">
              <span className="font-bold text-textPrimary truncate">{notif.title}</span>
              <span className="text-[10px] text-textMuted shrink-0 font-medium">{formatTimestamp(notif.created_at)}</span>
            </div>
            <p className="text-xs text-textSecondary mt-1 leading-relaxed">{notif.message || notif.content}</p>
          </div>
        </div>

        {/* Embedded Interactive Accept/Decline Card for Invitations */}
        {isInvitation && notif.entity_id && (
          <div className="pt-2 border-t border-borderColor/50 flex items-center justify-end space-x-2">
            <button
              disabled={isProcessing}
              onClick={() => handleDecline(notif.entity_id!, notif.id)}
              className="px-3 py-1.5 rounded-xl border border-borderColor bg-bgInput hover:bg-bgHover text-textSecondary text-xs font-semibold transition-all disabled:opacity-50"
            >
              Decline
            </button>
            <button
              disabled={isProcessing}
              onClick={() => handleAccept(notif.entity_id!, notif.id)}
              className="px-3.5 py-1.5 rounded-xl bg-accent hover:bg-accentHover text-white text-xs font-bold transition-all flex items-center gap-1.5 shadow-sm disabled:opacity-50"
            >
              {isProcessing ? <Loader2 size={12} className="animate-spin" /> : <Check size={12} />}
              <span>Accept</span>
            </button>
          </div>
        )}

        {/* Card Controls */}
        {!isInvitation && (
          <div className="flex items-center justify-end space-x-3 pt-1 border-t border-borderColor/30 text-[11px]">
            {!notif.is_read && (
              <button
                onClick={() => markRead(notif.id, token || undefined)}
                className="text-accentText hover:underline font-medium"
              >
                Mark read
              </button>
            )}
            <button
              onClick={() => deleteNotif(notif.id, token || undefined)}
              className="text-dangerText hover:underline font-medium flex items-center gap-1"
            >
              <Trash2 size={11} />
              <span>Delete</span>
            </button>
          </div>
        )}
      </div>
    );
  }
};
