import { Conversation } from './types';

const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface GroupCreatePayload {
  name: string;
  description?: string;
  organization_id: string;
  workspace_id?: string;
  visibility?: 'public' | 'private' | 'read_only' | 'announcement';
  avatar_url?: string;
  member_user_ids?: string[];
}

export interface ChannelCreatePayload {
  name: string;
  description?: string;
  organization_id: string;
  workspace_id?: string;
  project_id?: string;
  type?: 'project_channel' | 'announcement';
  visibility?: 'public' | 'private' | 'read_only' | 'announcement';
}

export async function createGroup(payload: GroupCreatePayload, token?: string): Promise<Conversation> {
  const res = await fetch(`${API_BASE_URL}/groups`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || err.message || 'Failed to create group');
  }
  return res.json();
}

export async function listGroups(organizationId: string, workspaceId?: string, token?: string): Promise<Conversation[]> {
  const params = new URLSearchParams({ organization_id: organizationId });

  const res = await fetch(`${API_BASE_URL}/groups?${params.toString()}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) {
    return [];
  }
  return res.json();
}

export async function getGroupDetails(id: string, token?: string): Promise<Conversation> {
  const res = await fetch(`${API_BASE_URL}/groups/${id}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) {
    throw new Error('Failed to fetch group details');
  }
  return res.json();
}

export async function updateGroup(id: string, payload: Partial<GroupCreatePayload>, token?: string): Promise<Conversation> {
  const res = await fetch(`${API_BASE_URL}/groups/${id}`, {
    method: 'PATCH',
    headers: getAuthHeaders(token),
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    throw new Error('Failed to update group');
  }
  return res.json();
}

export async function addGroupMember(id: string, userId: string, role = 'member', token?: string) {
  const res = await fetch(`${API_BASE_URL}/groups/${id}/members`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ user_id: userId, role })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || err.message || 'Failed to add group member');
  }
  return res.json();
}

export async function removeGroupMember(id: string, userId: string, token?: string) {
  const res = await fetch(`${API_BASE_URL}/groups/${id}/members/${userId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) {
    throw new Error('Failed to remove group member');
  }
  return res.json();
}

export async function updateMemberRole(id: string, userId: string, role: string, token?: string) {
  const res = await fetch(`${API_BASE_URL}/groups/${id}/members/${userId}/role`, {
    method: 'PATCH',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ role })
  });
  if (!res.ok) {
    throw new Error('Failed to update member role');
  }
  return res.json();
}

export async function toggleArchiveGroup(id: string, token?: string) {
  const res = await fetch(`${API_BASE_URL}/groups/${id}/archive`, {
    method: 'POST',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) {
    throw new Error('Failed to archive group');
  }
  return res.json();
}

export async function deleteGroup(id: string, token?: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/groups/${id}`, {
    method: 'DELETE',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || err.message || 'Failed to delete group');
  }
}

export async function createChannel(payload: ChannelCreatePayload, token?: string): Promise<Conversation> {
  const res = await fetch(`${API_BASE_URL}/channels`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || err.message || 'Failed to create channel');
  }
  return res.json();
}

export async function listChannels(organizationId: string, workspaceId?: string, projectId?: string, token?: string): Promise<Conversation[]> {
  const params = new URLSearchParams({ organization_id: organizationId });
  if (workspaceId) params.append('workspace_id', workspaceId);
  if (projectId) params.append('project_id', projectId);

  const res = await fetch(`${API_BASE_URL}/channels?${params.toString()}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) {
    throw new Error('Failed to fetch project channels');
  }
  return res.json();
}

export async function togglePinConversation(id: string, token?: string) {
  const res = await fetch(`${API_BASE_URL}/conversations/${id}/pin`, {
    method: 'POST',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) {
    throw new Error('Failed to pin conversation');
  }
  return res.json();
}
