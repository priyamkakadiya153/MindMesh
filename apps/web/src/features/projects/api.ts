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

export async function getProjects(token: string, orgId: string, workspaceId?: string, status?: string, search?: string) {
  const params = new URLSearchParams();
  if (workspaceId) params.append('workspace_id', workspaceId);
  if (status) params.append('status', status);
  if (search) params.append('search', search);

  const query = params.toString() ? `?${params.toString()}` : '';
  const res = await authedFetch(`${API_BASE}/projects/${query}`, token, orgId);
  if (!res.ok) throw new Error('Failed to load projects');
  return res.json();
}

export async function getProject(token: string, orgId: string, id: string) {
  const res = await authedFetch(`${API_BASE}/projects/${id}`, token, orgId);
  if (!res.ok) throw new Error('Failed to load project details');
  return res.json();
}

export async function createProject(token: string, orgId: string, projectData: any) {
  const res = await authedFetch(`${API_BASE}/projects/`, token, orgId, {
    method: 'POST',
    body: JSON.stringify(projectData),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to create project' }));
    throw new Error(err.detail || 'Failed to create project');
  }
  return res.json();
}

export async function updateProject(token: string, orgId: string, id: string, projectData: any) {
  const res = await authedFetch(`${API_BASE}/projects/${id}`, token, orgId, {
    method: 'PATCH',
    body: JSON.stringify(projectData),
  });
  if (!res.ok) throw new Error('Failed to update project');
  return res.json();
}

export async function archiveProject(token: string, orgId: string, id: string) {
  const res = await authedFetch(`${API_BASE}/projects/${id}/archive`, token, orgId, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to archive project');
  return res.json();
}

export async function restoreProject(token: string, orgId: string, id: string) {
  const res = await authedFetch(`${API_BASE}/projects/${id}/restore`, token, orgId, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to restore project');
  return res.json();
}

export async function deleteProject(token: string, orgId: string, id: string) {
  const res = await authedFetch(`${API_BASE}/projects/${id}`, token, orgId, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete project');
  return res.json();
}

// Settings
export async function getProjectSettings(token: string, orgId: string, id: string) {
  const res = await authedFetch(`${API_BASE}/projects/${id}/settings`, token, orgId);
  if (!res.ok) throw new Error('Failed to load project settings');
  return res.json();
}

export async function updateProjectSettings(token: string, orgId: string, id: string, settingsData: any) {
  const res = await authedFetch(`${API_BASE}/projects/${id}/settings`, token, orgId, {
    method: 'PATCH',
    body: JSON.stringify(settingsData),
  });
  if (!res.ok) throw new Error('Failed to update project settings');
  return res.json();
}

// Dashboard
export async function getProjectDashboard(token: string, orgId: string, id: string) {
  const res = await authedFetch(`${API_BASE}/projects/${id}/dashboard`, token, orgId);
  if (!res.ok) throw new Error('Failed to load project dashboard');
  return res.json();
}

// Roster
export async function getProjectMembers(token: string, orgId: string, id: string) {
  const res = await authedFetch(`${API_BASE}/projects/${id}/members`, token, orgId);
  if (!res.ok) throw new Error('Failed to load project members');
  return res.json();
}

export async function addProjectMember(token: string, orgId: string, id: string, email: string, role: string) {
  const res = await authedFetch(`${API_BASE}/projects/${id}/members`, token, orgId, {
    method: 'POST',
    body: JSON.stringify({ email, role }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to add member' }));
    throw new Error(err.detail || 'Failed to add member to project');
  }
  return res.json();
}

export async function updateProjectMember(token: string, orgId: string, id: string, userId: string, role?: string, status?: string) {
  const res = await authedFetch(`${API_BASE}/projects/${id}/members/${userId}`, token, orgId, {
    method: 'PATCH',
    body: JSON.stringify({ role, status }),
  });
  if (!res.ok) throw new Error('Failed to update project member');
  return res.json();
}

export async function removeProjectMember(token: string, orgId: string, id: string, userId: string) {
  const res = await authedFetch(`${API_BASE}/projects/${id}/members/${userId}`, token, orgId, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to remove project member');
  return res.json();
}
