import { useEffect, useCallback } from 'react';
import { useDashboardStore } from './store';

export function useDashboard(token: string | null, orgId: string | null, workspaceId?: string) {
  const {
    statisticsState,
    recentProjectsState,
    recentDocumentsState,
    recentChatsState,
    notificationsState,
    activityState,
    favoritesState,
    aiSummaryState,
    widgets,
    isGlobalLoading,
    globalError,
    dashboardData,
    initDashboard,
    fetchWidgetSection,
    fetchWidgets,
    toggleFavorite,
    markAsRead,
    markAllAsRead,
    deleteNotification
  } = useDashboardStore();

  const refresh = useCallback(async () => {
    if (token && orgId) {
      await Promise.all([
        initDashboard(token, orgId, workspaceId),
        fetchWidgets(token, orgId)
      ]);
    }
  }, [token, orgId, workspaceId, initDashboard, fetchWidgets]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // Live synchronization: Listen to scoped workspace, project, and document events
  useEffect(() => {
    const handleDataChange = () => {
      refresh();
    };

    window.addEventListener('mindmesh:workspace-changed', handleDataChange);
    window.addEventListener('mindmesh:project-changed', handleDataChange);
    window.addEventListener('mindmesh:document-changed', handleDataChange);
    return () => {
      window.removeEventListener('mindmesh:workspace-changed', handleDataChange);
      window.removeEventListener('mindmesh:project-changed', handleDataChange);
      window.removeEventListener('mindmesh:document-changed', handleDataChange);
    };
  }, [refresh]);

  const retrySection = useCallback((section: string) => {
    if (token && orgId) {
      fetchWidgetSection(section, token, orgId, workspaceId);
    }
  }, [token, orgId, workspaceId, fetchWidgetSection]);

  return {
    statisticsState,
    recentProjectsState,
    recentDocumentsState,
    recentChatsState,
    notificationsState,
    activityState,
    favoritesState,
    aiSummaryState,
    widgets,
    loading: isGlobalLoading && !dashboardData,
    error: globalError,
    dashboardData,
    refresh,
    retrySection,
    toggleFavorite: useCallback(
      (itemType: string, itemId: string, name: string, slug?: string) => {
        if (token && orgId) {
          toggleFavorite(token, orgId, itemType, itemId, name, slug);
        }
      },
      [token, orgId, toggleFavorite]
    ),
    markAsRead: useCallback(
      (notifId: string) => {
        if (token && orgId) {
          markAsRead(token, orgId, notifId);
        }
      },
      [token, orgId, markAsRead]
    ),
    markAllAsRead: useCallback(
      () => {
        if (token && orgId) {
          markAllAsRead(token, orgId);
        }
      },
      [token, orgId, markAllAsRead]
    ),
    deleteNotification: useCallback(
      (notifId: string) => {
        if (token && orgId) {
          deleteNotification(token, orgId, notifId);
        }
      },
      [token, orgId, deleteNotification]
    )
  };
}
