import { apiClient } from '../../lib/api-client';

const API_BASE = 'http://127.0.0.1:4000/api/v1';

async function authedFetch(url: string, token: string, orgId: string, options: RequestInit = {}) {
  const method = (options.method || 'GET').toUpperCase();
  const headers = { ...options.headers } as any;
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (orgId) headers['X-Organization-ID'] = orgId;
  
  const path = url.includes('/api/v1') ? url.substring(url.indexOf('/api/v1') + 7) : url;

  const response = await apiClient({
    url: path,
    method,
    headers,
    data: options.body instanceof FormData ? options.body : (options.body ? JSON.parse(options.body as string) : undefined),
  });

  return {
    ok: true,
    status: response.status,
    json: async () => response.data,
    text: async () => typeof response.data === 'string' ? response.data : JSON.stringify(response.data),
    headers: {
      get: (name: string) => response.headers[name.toLowerCase()],
    },
  } as any;
}

export async function getDashboard(token: string, orgId: string, workspaceId?: string) {
  const url = workspaceId 
    ? `${API_BASE}/dashboard/?workspace_id=${workspaceId}` 
    : `${API_BASE}/dashboard/`;
  const res = await authedFetch(url, token, orgId);
  if (!res.ok) throw new Error('Failed to load dashboard data');
  return res.json();
}

export async function getWidgets(token: string, orgId: string) {
  const res = await authedFetch(`${API_BASE}/dashboard/widgets`, token, orgId);
  if (!res.ok) throw new Error('Failed to load widgets configuration');
  return res.json();
}

export async function getSummary(token: string, orgId: string, workspaceId?: string) {
  const url = workspaceId ? `${API_BASE}/dashboard/summary?workspace_id=${workspaceId}` : `${API_BASE}/dashboard/summary`;
  const res = await authedFetch(url, token, orgId);
  if (!res.ok) throw new Error('Failed to load dashboard summary');
  return res.json();
}

export async function getStats(token: string, orgId: string, workspaceId?: string) {
  return getSummary(token, orgId, workspaceId);
}

export async function getRecentProjects(token: string, orgId: string, workspaceId?: string) {
  const url = workspaceId ? `${API_BASE}/dashboard/recent-projects?workspace_id=${workspaceId}` : `${API_BASE}/dashboard/recent-projects`;
  const res = await authedFetch(url, token, orgId);
  if (!res.ok) throw new Error('Failed to load recent projects');
  return res.json();
}

export async function getRecentDocuments(token: string, orgId: string, workspaceId?: string) {
  const url = workspaceId ? `${API_BASE}/dashboard/recent-documents?workspace_id=${workspaceId}` : `${API_BASE}/dashboard/recent-documents`;
  const res = await authedFetch(url, token, orgId);
  if (!res.ok) throw new Error('Failed to load recent documents');
  return res.json();
}

export async function getRecentChats(token: string, orgId: string, workspaceId?: string) {
  const url = workspaceId ? `${API_BASE}/dashboard/recent-chats?workspace_id=${workspaceId}` : `${API_BASE}/dashboard/recent-chats`;
  const res = await authedFetch(url, token, orgId);
  if (!res.ok) throw new Error('Failed to load recent chats');
  return res.json();
}

export async function getAISummary(token: string, orgId: string, workspaceId?: string) {
  const url = workspaceId ? `${API_BASE}/dashboard/ai-summary?workspace_id=${workspaceId}` : `${API_BASE}/dashboard/ai-summary`;
  const res = await authedFetch(url, token, orgId);
  if (!res.ok) throw new Error('Failed to load AI summary');
  return res.json();
}

export async function getActivityFeed(token: string, orgId: string) {
  return getActivities(token, orgId);
}

export async function getActivities(token: string, orgId: string) {
  const res = await authedFetch(`${API_BASE}/activity/`, token, orgId);
  if (!res.ok) throw new Error('Failed to load activity logs');
  return res.json();
}

export async function getNotifications(token: string, orgId: string) {
  const res = await authedFetch(`${API_BASE}/notifications/`, token, orgId);
  if (!res.ok) throw new Error('Failed to load notifications');
  return res.json();
}

export async function markNotificationRead(token: string, orgId: string, notifId: string) {
  const res = await authedFetch(`${API_BASE}/notifications/${notifId}/read`, token, orgId, {
    method: 'PATCH',
  });
  if (!res.ok) throw new Error('Failed to mark notification as read');
  return res.json();
}

export async function deleteNotification(token: string, orgId: string, notifId: string) {
  const res = await authedFetch(`${API_BASE}/notifications/${notifId}`, token, orgId, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete notification');
  return res.ok;
}

export async function getFavorites(token: string, orgId: string) {
  const res = await authedFetch(`${API_BASE}/favorites/`, token, orgId);
  if (!res.ok) throw new Error('Failed to load favorites');
  return res.json();
}

export async function addFavorite(token: string, orgId: string, itemType: string, itemId: string, name: string, slug?: string) {
  const res = await authedFetch(`${API_BASE}/favorites/`, token, orgId, {
    method: 'POST',
    body: JSON.stringify({ item_type: itemType, item_id: itemId, name, slug }),
  });
  if (!res.ok) throw new Error('Failed to add favorite');
  return res.json();
}

export async function deleteFavorite(token: string, orgId: string, favId: string) {
  const res = await authedFetch(`${API_BASE}/favorites/${favId}`, token, orgId, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete favorite');
  return res.ok;
}

export async function getRecents(token: string, orgId: string) {
  const res = await authedFetch(`${API_BASE}/recent/`, token, orgId);
  if (!res.ok) throw new Error('Failed to load recents');
  return res.json();
}

export async function clearRecents(token: string, orgId: string) {
  const res = await authedFetch(`${API_BASE}/recent/`, token, orgId, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to clear recents');
  return res.ok;
}
