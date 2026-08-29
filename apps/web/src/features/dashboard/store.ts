import { create } from 'zustand';
import * as api from './api';
import { 
  DashboardData, 
  Widget, 
  Stats, 
  RecentProject, 
  RecentDocument, 
  RecentChat, 
  Notification, 
  ActivityLog, 
  FavoriteItem,
  WidgetSectionState
} from './types';

interface DashboardState {
  // Granular widget states for independent loading, auto-retry, & 500 error boundaries
  statisticsState: WidgetSectionState<Stats>;
  recentProjectsState: WidgetSectionState<RecentProject[]>;
  recentDocumentsState: WidgetSectionState<RecentDocument[]>;
  recentChatsState: WidgetSectionState<RecentChat[]>;
  notificationsState: WidgetSectionState<Notification[]>;
  activityState: WidgetSectionState<ActivityLog[]>;
  favoritesState: WidgetSectionState<FavoriteItem[]>;
  aiSummaryState: WidgetSectionState<{ insights: string; last_generation: string; status: string }>;
  
  widgets: Widget[];
  isGlobalLoading: boolean;
  globalError: string | null;

  // Derived full dashboardData object for backward compatibility
  dashboardData: DashboardData | null;

  // Actions
  initDashboard: (token: string, orgId: string, workspaceId?: string) => Promise<void>;
  fetchWidgetSection: (section: string, token: string, orgId: string, workspaceId?: string) => Promise<void>;
  fetchWidgets: (token: string, orgId: string) => Promise<void>;
  toggleFavorite: (token: string, orgId: string, itemType: string, itemId: string, name: string, slug?: string) => Promise<void>;
  markAsRead: (token: string, orgId: string, notifId: string) => Promise<void>;
  markAllAsRead: (token: string, orgId: string) => Promise<void>;
  deleteNotification: (token: string, orgId: string, notifId: string) => Promise<void>;
}

const getCacheKey = (orgId: string, workspaceId?: string) => 
  `mindmesh_dashboard_cache_${orgId}_${workspaceId || 'all'}`;

const loadLocalCache = (orgId: string, workspaceId?: string): DashboardData | null => {
  try {
    const raw = localStorage.getItem(getCacheKey(orgId, workspaceId));
    if (raw) return JSON.parse(raw);
  } catch (e) {
    if (import.meta.env.DEV) {
      console.warn("[SWR Cache] Failed to load dashboard local cache:", e);
    }
  }
  return null;
};

const saveLocalCache = (orgId: string, workspaceId: string | undefined, data: DashboardData) => {
  try {
    localStorage.setItem(getCacheKey(orgId, workspaceId), JSON.stringify(data));
  } catch (e) {
    if (import.meta.env.DEV) {
      console.warn("[SWR Cache] Failed to save dashboard local cache:", e);
    }
  }
};

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Auto-retry helper with exponential backoff (1s, 2s, 5s - max 3 attempts)
 */
async function fetchWithAutoRetry<T>(
  fetcher: () => Promise<T>,
  maxAttempts = 3,
  delays = [1000, 2000, 5000]
): Promise<T> {
  let lastError: any = null;
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fetcher();
    } catch (err: any) {
      lastError = err;
      if (attempt < maxAttempts) {
        const delayMs = delays[attempt - 1] || 2000;
        if (import.meta.env.DEV) {
          console.warn(`[AutoRetry] Attempt ${attempt} failed. Retrying in ${delayMs}ms...`, err);
        }
        await sleep(delayMs);
      }
    }
  }
  throw lastError;
}

const defaultStats: Stats = {
  workspaces_count: 0,
  projects_count: 0,
  documents_count: 0,
  chats_count: 0,
  storage_used: 0,
  members_count: 0
};

export const useDashboardStore = create<DashboardState>((set, get) => ({
  statisticsState: { data: null, loading: true, error: null },
  recentProjectsState: { data: null, loading: true, error: null },
  recentDocumentsState: { data: null, loading: true, error: null },
  recentChatsState: { data: null, loading: true, error: null },
  notificationsState: { data: null, loading: true, error: null },
  activityState: { data: null, loading: true, error: null },
  favoritesState: { data: null, loading: true, error: null },
  aiSummaryState: { data: null, loading: true, error: null },

  widgets: [],
  isGlobalLoading: false,
  globalError: null,
  dashboardData: null,

  initDashboard: async (token: string, orgId: string, workspaceId?: string) => {
    // 1. Check SWR Local Storage Cache
    const cached = loadLocalCache(orgId, workspaceId);
    
    if (cached) {
      set({
        statisticsState: { data: cached.statistics, loading: false, error: null, isRevalidating: true, isCachedFallback: false },
        recentProjectsState: { data: cached.recent_projects, loading: false, error: null, isRevalidating: true, isCachedFallback: false },
        recentDocumentsState: { data: cached.recent_documents, loading: false, error: null, isRevalidating: true, isCachedFallback: false },
        recentChatsState: { data: cached.recent_chats, loading: false, error: null, isRevalidating: true, isCachedFallback: false },
        notificationsState: { data: cached.notifications, loading: false, error: null, isRevalidating: true, isCachedFallback: false },
        activityState: { data: cached.activity, loading: false, error: null, isRevalidating: true, isCachedFallback: false },
        favoritesState: { data: cached.favorites, loading: false, error: null, isRevalidating: true, isCachedFallback: false },
        aiSummaryState: { data: cached.ai_summary, loading: false, error: null, isRevalidating: true, isCachedFallback: false },
        dashboardData: cached,
        isGlobalLoading: false,
        globalError: null
      });
    } else {
      set({
        statisticsState: { data: null, loading: true, error: null },
        recentProjectsState: { data: null, loading: true, error: null },
        recentDocumentsState: { data: null, loading: true, error: null },
        recentChatsState: { data: null, loading: true, error: null },
        notificationsState: { data: null, loading: true, error: null },
        activityState: { data: null, loading: true, error: null },
        favoritesState: { data: null, loading: true, error: null },
        aiSummaryState: { data: null, loading: true, error: null },
        isGlobalLoading: true,
        globalError: null
      });
    }

    // 2. Parallel Background Revalidation with Auto-Retry and SWR Fallback Preservation
    const fetchStats = fetchWithAutoRetry(() => api.getStats(token, orgId, workspaceId))
      .then(res => {
        const stats = res.statistics || res;
        set(s => ({ statisticsState: { data: stats, loading: false, error: null, isRevalidating: false, isCachedFallback: false } }));
        return stats;
      })
      .catch(() => {
        set(s => {
          const currentData = s.statisticsState.data;
          if (currentData) {
            // Keep working cached data visible!
            return { statisticsState: { data: currentData, loading: false, error: null, isRevalidating: false, isCachedFallback: true } };
          }
          return { statisticsState: { data: null, loading: false, error: "Unable to load dashboard statistics.", isRevalidating: false, isCachedFallback: false } };
        });
        return null;
      });

    const fetchProjects = fetchWithAutoRetry(() => api.getRecentProjects(token, orgId, workspaceId))
      .then(res => {
        const projs = res.recent_projects || [];
        set(s => ({ recentProjectsState: { data: projs, loading: false, error: null, isRevalidating: false, isCachedFallback: false } }));
        return projs;
      })
      .catch(() => {
        set(s => {
          const currentData = s.recentProjectsState.data;
          if (currentData && currentData.length > 0) {
            // Keep working cached data visible!
            return { recentProjectsState: { data: currentData, loading: false, error: null, isRevalidating: false, isCachedFallback: true } };
          }
          return { recentProjectsState: { data: null, loading: false, error: "Unable to load recent projects.", isRevalidating: false, isCachedFallback: false } };
        });
        return null;
      });

    const fetchDocs = fetchWithAutoRetry(() => api.getRecentDocuments(token, orgId, workspaceId))
      .then(res => {
        const docs = res.recent_documents || [];
        set(s => ({ recentDocumentsState: { data: docs, loading: false, error: null, isRevalidating: false, isCachedFallback: false } }));
        return docs;
      })
      .catch(() => {
        set(s => {
          const currentData = s.recentDocumentsState.data;
          if (currentData && currentData.length > 0) {
            return { recentDocumentsState: { data: currentData, loading: false, error: null, isRevalidating: false, isCachedFallback: true } };
          }
          return { recentDocumentsState: { data: null, loading: false, error: "Unable to load knowledge documents.", isRevalidating: false, isCachedFallback: false } };
        });
        return null;
      });

    const fetchChats = fetchWithAutoRetry(() => api.getRecentChats(token, orgId, workspaceId))
      .then(res => {
        const chats = res.recent_chats || [];
        set(s => ({ recentChatsState: { data: chats, loading: false, error: null, isRevalidating: false, isCachedFallback: false } }));
        return chats;
      })
      .catch(() => {
        set(s => {
          const currentData = s.recentChatsState.data;
          if (currentData && currentData.length > 0) {
            return { recentChatsState: { data: currentData, loading: false, error: null, isRevalidating: false, isCachedFallback: true } };
          }
          return { recentChatsState: { data: null, loading: false, error: "Unable to load conversations.", isRevalidating: false, isCachedFallback: false } };
        });
        return null;
      });

    const fetchNotifs = fetchWithAutoRetry(() => api.getNotifications(token, orgId))
      .then(res => {
        const notifs = Array.isArray(res) ? res : (res?.notifications || []);
        set(s => ({ notificationsState: { data: notifs, loading: false, error: null, isRevalidating: false, isCachedFallback: false } }));
        return notifs;
      })
      .catch(() => {
        set(s => {
          const currentData = s.notificationsState.data;
          if (currentData && Array.isArray(currentData) && currentData.length > 0) {
            return { notificationsState: { data: currentData, loading: false, error: null, isRevalidating: false, isCachedFallback: true } };
          }
          return { notificationsState: { data: [], loading: false, error: "Unable to load notifications.", isRevalidating: false, isCachedFallback: false } };
        });
        return null;
      });

    const fetchActs = fetchWithAutoRetry(() => api.getActivityFeed(token, orgId))
      .then(res => {
        const acts = res || [];
        set(s => ({ activityState: { data: acts, loading: false, error: null, isRevalidating: false, isCachedFallback: false } }));
        return acts;
      })
      .catch(() => {
        set(s => {
          const currentData = s.activityState.data;
          if (currentData && currentData.length > 0) {
            return { activityState: { data: currentData, loading: false, error: null, isRevalidating: false, isCachedFallback: true } };
          }
          return { activityState: { data: null, loading: false, error: "Unable to load activity feed.", isRevalidating: false, isCachedFallback: false } };
        });
        return null;
      });

    const fetchFavs = fetchWithAutoRetry(() => api.getFavorites(token, orgId))
      .then(res => {
        const favs = res || [];
        set(s => ({ favoritesState: { data: favs, loading: false, error: null, isRevalidating: false, isCachedFallback: false } }));
        return favs;
      })
      .catch(() => {
        set(s => {
          const currentData = s.favoritesState.data;
          if (currentData && currentData.length > 0) {
            return { favoritesState: { data: currentData, loading: false, error: null, isRevalidating: false, isCachedFallback: true } };
          }
          return { favoritesState: { data: null, loading: false, error: "Unable to load starred items.", isRevalidating: false, isCachedFallback: false } };
        });
        return null;
      });

    const fetchAISummary = fetchWithAutoRetry(() => api.getAISummary(token, orgId, workspaceId))
      .then(res => {
        const summary = res.ai_summary || res;
        set(s => ({ aiSummaryState: { data: summary, loading: false, error: null, isRevalidating: false, isCachedFallback: false } }));
        return summary;
      })
      .catch(() => {
        set(s => {
          const currentData = s.aiSummaryState.data;
          if (currentData) {
            return { aiSummaryState: { data: currentData, loading: false, error: null, isRevalidating: false, isCachedFallback: true } };
          }
          return { aiSummaryState: { data: null, loading: false, error: "Unable to load AI summary.", isRevalidating: false, isCachedFallback: false } };
        });
        return null;
      });

    // Fire all requests concurrently with Promise.allSettled
    await Promise.allSettled([
      fetchStats,
      fetchProjects,
      fetchDocs,
      fetchChats,
      fetchNotifs,
      fetchActs,
      fetchFavs,
      fetchAISummary
    ]);

    set({ isGlobalLoading: false });

    // Update derived dashboardData and cache
    const currentState = get();
    const constructedData: DashboardData = {
      organization: { id: orgId, name: '', slug: '' },
      workspace: workspaceId ? { id: workspaceId, name: '', slug: '' } : null,
      statistics: currentState.statisticsState.data || defaultStats,
      recent_projects: currentState.recentProjectsState.data || [],
      recent_documents: currentState.recentDocumentsState.data || [],
      recent_chats: currentState.recentChatsState.data || [],
      notifications: currentState.notificationsState.data || [],
      activity: currentState.activityState.data || [],
      favorites: currentState.favoritesState.data || [],
      ai_summary: currentState.aiSummaryState.data || { insights: 'No data', last_generation: '', status: 'idle' }
    };

    set({ dashboardData: constructedData });
    saveLocalCache(orgId, workspaceId, constructedData);
  },

  fetchWidgetSection: async (section: string, token: string, orgId: string, workspaceId?: string) => {
    if (section === 'stats') {
      set(s => ({ statisticsState: { ...s.statisticsState, loading: true, error: null, isCachedFallback: false } }));
      try {
        const res = await fetchWithAutoRetry(() => api.getStats(token, orgId, workspaceId));
        set(s => ({ statisticsState: { data: res.statistics || res, loading: false, error: null, isCachedFallback: false } }));
      } catch (err: any) {
        set(s => {
          if (s.statisticsState.data) {
            return { statisticsState: { ...s.statisticsState, loading: false, isCachedFallback: true } };
          }
          return { statisticsState: { data: null, loading: false, error: "Unable to load dashboard statistics.", isCachedFallback: false } };
        });
      }
    } else if (section === 'recent_projects') {
      set(s => ({ recentProjectsState: { ...s.recentProjectsState, loading: true, error: null, isCachedFallback: false } }));
      try {
        const res = await fetchWithAutoRetry(() => api.getRecentProjects(token, orgId, workspaceId));
        set(s => ({ recentProjectsState: { data: res.recent_projects || [], loading: false, error: null, isCachedFallback: false } }));
      } catch (err: any) {
        set(s => {
          if (s.recentProjectsState.data && s.recentProjectsState.data.length > 0) {
            return { recentProjectsState: { ...s.recentProjectsState, loading: false, isCachedFallback: true } };
          }
          return { recentProjectsState: { data: null, loading: false, error: "Unable to load recent projects.", isCachedFallback: false } };
        });
      }
    } else if (section === 'recent_documents') {
      set(s => ({ recentDocumentsState: { ...s.recentDocumentsState, loading: true, error: null, isCachedFallback: false } }));
      try {
        const res = await fetchWithAutoRetry(() => api.getRecentDocuments(token, orgId, workspaceId));
        set(s => ({ recentDocumentsState: { data: res.recent_documents || [], loading: false, error: null, isCachedFallback: false } }));
      } catch (err: any) {
        set(s => {
          if (s.recentDocumentsState.data && s.recentDocumentsState.data.length > 0) {
            return { recentDocumentsState: { ...s.recentDocumentsState, loading: false, isCachedFallback: true } };
          }
          return { recentDocumentsState: { data: null, loading: false, error: "Unable to load knowledge documents.", isCachedFallback: false } };
        });
      }
    } else if (section === 'recent_chats') {
      set(s => ({ recentChatsState: { ...s.recentChatsState, loading: true, error: null, isCachedFallback: false } }));
      try {
        const res = await fetchWithAutoRetry(() => api.getRecentChats(token, orgId, workspaceId));
        set(s => ({ recentChatsState: { data: res.recent_chats || [], loading: false, error: null, isCachedFallback: false } }));
      } catch (err: any) {
        set(s => {
          if (s.recentChatsState.data && s.recentChatsState.data.length > 0) {
            return { recentChatsState: { ...s.recentChatsState, loading: false, isCachedFallback: true } };
          }
          return { recentChatsState: { data: null, loading: false, error: "Unable to load conversations.", isCachedFallback: false } };
        });
      }
    } else if (section === 'activity') {
      set(s => ({ activityState: { ...s.activityState, loading: true, error: null, isCachedFallback: false } }));
      try {
        const res = await fetchWithAutoRetry(() => api.getActivityFeed(token, orgId));
        set(s => ({ activityState: { data: res || [], loading: false, error: null, isCachedFallback: false } }));
      } catch (err: any) {
        set(s => {
          if (s.activityState.data && s.activityState.data.length > 0) {
            return { activityState: { ...s.activityState, loading: false, isCachedFallback: true } };
          }
          return { activityState: { data: null, loading: false, error: "Unable to load activity feed.", isCachedFallback: false } };
        });
      }
    } else if (section === 'notifications') {
      set(s => ({ notificationsState: { ...s.notificationsState, loading: true, error: null, isCachedFallback: false } }));
      try {
        const res = await fetchWithAutoRetry(() => api.getNotifications(token, orgId));
        const notifs = Array.isArray(res) ? res : (res?.notifications || []);
        set(s => ({ notificationsState: { data: notifs, loading: false, error: null, isCachedFallback: false } }));
      } catch (err: any) {
        set(s => {
          if (s.notificationsState.data && Array.isArray(s.notificationsState.data) && s.notificationsState.data.length > 0) {
            return { notificationsState: { ...s.notificationsState, loading: false, isCachedFallback: true } };
          }
          return { notificationsState: { data: [], loading: false, error: "Unable to load notifications.", isCachedFallback: false } };
        });
      }
    } else if (section === 'favorites') {
      set(s => ({ favoritesState: { ...s.favoritesState, loading: true, error: null, isCachedFallback: false } }));
      try {
        const res = await fetchWithAutoRetry(() => api.getFavorites(token, orgId));
        set(s => ({ favoritesState: { data: res || [], loading: false, error: null, isCachedFallback: false } }));
      } catch (err: any) {
        set(s => {
          if (s.favoritesState.data && s.favoritesState.data.length > 0) {
            return { favoritesState: { ...s.favoritesState, loading: false, isCachedFallback: true } };
          }
          return { favoritesState: { data: null, loading: false, error: "Unable to load starred items.", isCachedFallback: false } };
        });
      }
    } else if (section === 'ai_summary') {
      set(s => ({ aiSummaryState: { ...s.aiSummaryState, loading: true, error: null, isCachedFallback: false } }));
      try {
        const res = await fetchWithAutoRetry(() => api.getAISummary(token, orgId, workspaceId));
        set(s => ({ aiSummaryState: { data: res.ai_summary || res, loading: false, error: null, isCachedFallback: false } }));
      } catch (err: any) {
        set(s => {
          if (s.aiSummaryState.data) {
            return { aiSummaryState: { ...s.aiSummaryState, loading: false, isCachedFallback: true } };
          }
          return { aiSummaryState: { data: null, loading: false, error: "Unable to load AI summary.", isCachedFallback: false } };
        });
      }
    }
  },

  fetchWidgets: async (token: string, orgId: string) => {
    if (get().widgets.length > 0) return;
    try {
      const { widgets } = await api.getWidgets(token, orgId);
      set({ widgets });
    } catch (err) {
      set({
        widgets: [
          { id: 'recent_projects', name: 'Recent Projects', enabled: true, col_span: 1 },
          { id: 'recent_documents', name: 'Recent Documents', enabled: true, col_span: 2 },
          { id: 'recent_chats', name: 'Recent Chats', enabled: true, col_span: 1 },
          { id: 'activity_feed', name: 'Activity Feed Log', enabled: true, col_span: 1 },
          { id: 'notifications', name: 'Notifications', enabled: true, col_span: 1 },
          { id: 'ai_insights', name: 'AI Insights', enabled: true, col_span: 1 },
          { id: 'favorites', name: 'Favorites Bookmarks', enabled: true, col_span: 1 }
        ]
      });
    }
  },

  toggleFavorite: async (token, orgId, itemType, itemId, name, slug) => {
    const currentFavsState = get().favoritesState;
    const existingFavs = currentFavsState.data || [];
    const existingFav = existingFavs.find(f => f.item_id === itemId && f.item_type === itemType);

    try {
      if (existingFav) {
        await api.deleteFavorite(token, orgId, existingFav.id);
        const updated = existingFavs.filter(f => f.id !== existingFav.id);
        set({ favoritesState: { ...currentFavsState, data: updated } });
      } else {
        const newFav = await api.addFavorite(token, orgId, itemType, itemId, name, slug);
        const updated = [...existingFavs, newFav];
        set({ favoritesState: { ...currentFavsState, data: updated } });
      }
    } catch (err: any) {
      if (import.meta.env.DEV) {
        console.warn("Toggle favorite failed:", err);
      }
    }
  },

  markAsRead: async (token, orgId, notifId) => {
    const currentNotifState = get().notificationsState;
    const notifs = currentNotifState.data || [];
    try {
      await api.markNotificationRead(token, orgId, notifId);
      const updated = notifs.map(n => n.id === notifId ? { ...n, is_read: true } : n);
      set({ notificationsState: { ...currentNotifState, data: updated } });
    } catch (err: any) {
      if (import.meta.env.DEV) {
        console.warn("Mark notification read failed:", err);
      }
    }
  },

  markAllAsRead: async (token, orgId) => {
    const currentNotifState = get().notificationsState;
    const notifs = currentNotifState.data || [];
    try {
      const unread = notifs.filter(n => !n.is_read);
      await Promise.all(unread.map(n => api.markNotificationRead(token, orgId, n.id)));
      const updated = notifs.map(n => ({ ...n, is_read: true }));
      set({ notificationsState: { ...currentNotifState, data: updated } });
    } catch (err: any) {
      if (import.meta.env.DEV) {
        console.warn("Mark all notifications read failed:", err);
      }
    }
  },

  deleteNotification: async (token, orgId, notifId) => {
    const currentNotifState = get().notificationsState;
    const notifs = currentNotifState.data || [];
    try {
      await api.deleteNotification(token, orgId, notifId);
      const updated = notifs.filter(n => n.id !== notifId);
      set({ notificationsState: { ...currentNotifState, data: updated } });
    } catch (err: any) {
      if (import.meta.env.DEV) {
        console.warn("Delete notification failed:", err);
      }
    }
  }
}));
