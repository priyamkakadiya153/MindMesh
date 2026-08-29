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

export async function getMembersDirectory(
  token: string, orgId: string, workspaceId?: string, projectId?: string, search?: string, role?: string
) {
  const params = new URLSearchParams();
  if (workspaceId) params.append('workspace_id', workspaceId);
  if (projectId) params.append('project_id', projectId);
  if (search) params.append('search', search);
  if (role) params.append('role', role);

  const query = params.toString() ? `?${params.toString()}` : '';
  const res = await authedFetch(`${API_BASE}/members${query}`, token, orgId);
  if (!res.ok) throw new Error('Failed to load member directory');
  return res.json();
}

export async function updateMemberAction(token: string, orgId: string, userId: string, payload: any) {
  const res = await authedFetch(`${API_BASE}/members/${userId}`, token, orgId, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to update member action');
  return res.json();
}

export async function removeMember(
  token: string, orgId: string, userId: string, level = 'organization', workspaceId?: string, projectId?: string
) {
  const params = new URLSearchParams();
  params.append('level', level);
  if (workspaceId) params.append('workspace_id', workspaceId);
  if (projectId) params.append('project_id', projectId);

  const res = await authedFetch(`${API_BASE}/members/${userId}?${params.toString()}`, token, orgId, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to remove member');
}

// Invitations API
export async function issueInvitation(token: string, orgId: string, invitationData: any) {
  const res = await authedFetch(`${API_BASE}/members/invitations`, token, orgId, {
    method: 'POST',
    body: JSON.stringify(invitationData),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to issue invitation' }));
    throw new Error(err.detail || 'Failed to issue invitation');
  }
  return res.json();
}

export async function getPendingInvitations(token: string, orgId: string) {
  const res = await authedFetch(`${API_BASE}/members/invitations`, token, orgId);
  if (!res.ok) throw new Error('Failed to load pending invitations');
  return res.json();
}

export async function acceptInvitation(token: string, tokenOrId: string) {
  const res = await authedFetch(`${API_BASE}/members/invitations/${tokenOrId}/accept`, token, '', {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to accept invitation');
  return res.json();
}

export async function cancelInvitation(token: string, orgId: string, inviteId: string) {
  const res = await authedFetch(`${API_BASE}/members/invitations/${inviteId}`, token, orgId, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to cancel invitation');
  return res.json();
}

// Join Requests API
export async function getJoinRequests(token: string, orgId: string) {
  const res = await authedFetch(`${API_BASE}/members/join-requests`, token, orgId);
  if (!res.ok) throw new Error('Failed to load join requests');
  return res.json();
}

export async function approveJoinRequest(token: string, orgId: string, requestId: string) {
  const res = await authedFetch(`${API_BASE}/members/join-requests/${requestId}/approve`, token, orgId, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to approve join request');
  return res.json();
}

export async function rejectJoinRequest(token: string, orgId: string, requestId: string) {
  const res = await authedFetch(`${API_BASE}/members/join-requests/${requestId}/reject`, token, orgId, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to reject join request');
  return res.json();
}

export async function getPermissionMatrix(token: string, orgId: string) {
  const res = await authedFetch(`${API_BASE}/members/permission-matrix`, token, orgId);
  if (!res.ok) throw new Error('Failed to load permission matrix');
  return res.json();
}
