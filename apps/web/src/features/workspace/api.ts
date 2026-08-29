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

export async function getWorkspaces(token: string, orgId: string) {
  const res = await authedFetch(`${API_BASE}/workspaces/`, token, orgId);
  if (!res.ok) throw new Error('Failed to load workspaces');
  return res.json();
}

export async function createWorkspace(token: string, orgId: string, name: string, slug: string) {
  const res = await authedFetch(`${API_BASE}/workspaces/`, token, orgId, {
    method: 'POST',
    body: JSON.stringify({ name, slug }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to create workspace' }));
    throw new Error(err.detail || 'Failed to create workspace');
  }
  return res.json();
}

export async function getWorkspace(token: string, orgId: string, id: string) {
  const res = await authedFetch(`${API_BASE}/workspaces/${id}`, token, orgId);
  if (!res.ok) throw new Error('Failed to load workspace');
  return res.json();
}

export async function updateWorkspace(token: string, orgId: string, id: string, name: string, slug: string) {
  const res = await authedFetch(`${API_BASE}/workspaces/${id}`, token, orgId, {
    method: 'PATCH',
    body: JSON.stringify({ name, slug }),
  });
  if (!res.ok) throw new Error('Failed to update workspace');
  return res.json();
}

export async function deleteWorkspace(token: string, orgId: string, id: string) {
  const res = await authedFetch(`${API_BASE}/workspaces/${id}`, token, orgId, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete workspace');
  return res.json();
}

export async function archiveWorkspace(token: string, orgId: string, id: string) {
  const res = await authedFetch(`${API_BASE}/workspaces/${id}/archive`, token, orgId, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to archive workspace');
  return res.json();
}

export async function restoreWorkspace(token: string, orgId: string, id: string) {
  const res = await authedFetch(`${API_BASE}/workspaces/${id}/restore`, token, orgId, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to restore workspace');
  return res.json();
}

export async function getWorkspaceSettings(token: string, orgId: string, id: string) {
  const res = await authedFetch(`${API_BASE}/workspaces/${id}/settings`, token, orgId);
  if (!res.ok) throw new Error('Failed to load workspace settings');
  return res.json();
}

export async function updateWorkspaceSettings(token: string, orgId: string, id: string, settingsData: any) {
  const res = await authedFetch(`${API_BASE}/workspaces/${id}/settings`, token, orgId, {
    method: 'PATCH',
    body: JSON.stringify(settingsData),
  });
  if (!res.ok) throw new Error('Failed to update workspace settings');
  return res.json();
}

export async function getWorkspaceMembers(token: string, orgId: string, id: string) {
  const res = await authedFetch(`${API_BASE}/workspaces/${id}/members`, token, orgId);
  if (!res.ok) throw new Error('Failed to load workspace members');
  return res.json();
}

export async function inviteWorkspaceMember(token: string, orgId: string, id: string, email: string, role: string) {
  const res = await authedFetch(`${API_BASE}/workspaces/${id}/members`, token, orgId, {
    method: 'POST',
    body: JSON.stringify({ email, role }),
  });
  if (!res.ok) throw new Error('Failed to invite member to workspace');
  return res.json();
}

export async function removeWorkspaceMember(token: string, orgId: string, workspaceId: string, userId: string) {
  const res = await authedFetch(`${API_BASE}/workspaces/${workspaceId}/members/${userId}`, token, orgId, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to remove workspace member');
  return res.json();
}

