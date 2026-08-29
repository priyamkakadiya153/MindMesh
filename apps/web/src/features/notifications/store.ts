import { create } from 'zustand';
import {
  NotificationItem,
  UserInvitationItem,
  getNotifications,
  getUserInvitations,
  markNotificationRead,
  markAllNotificationsRead,
  deleteNotification,
  acceptUserInvitation,
  declineUserInvitation
} from './notifications-api';

interface NotificationState {
  notifications: NotificationItem[];
  userInvitations: UserInvitationItem[];
  unreadCount: number;
  isDrawerOpen: boolean;
  loading: boolean;
  error: string | null;

  fetchNotifications: (token?: string) => Promise<void>;
  fetchUserInvitations: (token?: string) => Promise<void>;
  markRead: (id: string, token?: string) => Promise<void>;
  markAllRead: (token?: string) => Promise<void>;
  deleteNotif: (id: string, token?: string) => Promise<void>;
  acceptInvitation: (idOrToken: string, token?: string) => Promise<any>;
  declineInvitation: (idOrToken: string, token?: string) => Promise<any>;
  setDrawerOpen: (isOpen: boolean) => void;
  toggleDrawer: () => void;
}

let userInvitationsPromise: Promise<any> | null = null;
let lastInvitationsFetchTime = 0;

export const useNotificationStore = create<NotificationState>((set, get) => ({
  notifications: [],
  userInvitations: [],
  unreadCount: 0,
  isDrawerOpen: false,
  loading: false,
  error: null,

  fetchNotifications: async (token?: string) => {
    try {
      set({ loading: true, error: null });
      const data = await getNotifications(token);
      set({
        notifications: data.notifications || [],
        unreadCount: data.unread_count || 0,
        loading: false
      });
    } catch (err: any) {
      set({ loading: false, error: err.message || 'Failed to load notifications' });
    }
  },

  fetchUserInvitations: async (token?: string) => {
    const now = Date.now();
    if (userInvitationsPromise) {
      await userInvitationsPromise;
      return;
    }
    if (now - lastInvitationsFetchTime < 5000 && get().userInvitations.length > 0) {
      return;
    }

    try {
      userInvitationsPromise = getUserInvitations(token);
      const invitations = await userInvitationsPromise;
      lastInvitationsFetchTime = Date.now();
      set({ userInvitations: invitations || [] });
    } catch (err) {
      // Non-blocking
    } finally {
      userInvitationsPromise = null;
    }
  },

  markRead: async (id: string, token?: string) => {
    try {
      await markNotificationRead(id, token);
      const notifications = get().notifications.map(n =>
        n.id === id ? { ...n, is_read: true } : n
      );
      const unreadCount = Math.max(get().unreadCount - 1, 0);
      set({ notifications, unreadCount });
    } catch (err) {
      console.error('Failed to mark notification read:', err);
    }
  },

  markAllRead: async (token?: string) => {
    try {
      await markAllNotificationsRead(token);
      const notifications = get().notifications.map(n => ({ ...n, is_read: true }));
      set({ notifications, unreadCount: 0 });
    } catch (err) {
      console.error('Failed to mark all read:', err);
    }
  },

  deleteNotif: async (id: string, token?: string) => {
    try {
      await deleteNotification(id, token);
      const target = get().notifications.find(n => n.id === id);
      const notifications = get().notifications.filter(n => n.id !== id);
      const unreadCount = target && !target.is_read ? Math.max(get().unreadCount - 1, 0) : get().unreadCount;
      set({ notifications, unreadCount });
    } catch (err) {
      console.error('Failed to delete notification:', err);
    }
  },

  acceptInvitation: async (idOrToken: string, token?: string) => {
    const res = await acceptUserInvitation(idOrToken, token);
    await get().fetchNotifications(token);
    await get().fetchUserInvitations(token);
    return res;
  },

  declineInvitation: async (idOrToken: string, token?: string) => {
    const res = await declineUserInvitation(idOrToken, token);
    await get().fetchNotifications(token);
    await get().fetchUserInvitations(token);
    return res;
  },

  setDrawerOpen: (isOpen: boolean) => set({ isDrawerOpen: isOpen }),

  toggleDrawer: () => set(state => ({ isDrawerOpen: !state.isDrawerOpen }))
}));
