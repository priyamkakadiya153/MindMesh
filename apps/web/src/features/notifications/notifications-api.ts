const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface NotificationItem {
  id: string;
  user_id: string;
  organization_id?: string;
  type: string;
  title: string;
  message?: string;
  content?: string;
  priority?: string;
  is_read: boolean;
  link?: string;
  entity_type?: string;
  entity_id?: string;
  created_at: string;
}

export interface NotificationsResponse {
  unread_count: number;
  notifications: NotificationItem[];
}

export interface UserInvitationItem {
  id: string;
  organization_id: string;
  org_name?: string;
  email: str;
  role: str;
  token: string;
  invited_by?: string;
  status: string;
  expires_at: string;
  created_at: string;
}

export interface ActivityItem {
  id: string;
  organization_id: string;
  user_id: string;
  user_name?: string;
  action: string;
  entity_type: string;
  entity_id: string;
  details?: string;
  created_at: string;
}

export async function getNotifications(token?: string): Promise<NotificationsResponse> {
  const res = await fetch(`${API_BASE_URL}/notifications`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch notifications');
  const data = await res.json();
  if (Array.isArray(data)) {
    const unread = data.filter((n: any) => !n.is_read).length;
    return { unread_count: unread, notifications: data };
  }
  return data;
}

export async function markNotificationRead(id: string, token?: string) {
  const res = await fetch(`${API_BASE_URL}/notifications/${id}/read`, {
    method: 'PATCH',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to mark notification read');
  return res.json();
}

export async function markAllNotificationsRead(token?: string) {
  const res = await fetch(`${API_BASE_URL}/notifications/read-all`, {
    method: 'PATCH',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to mark all read');
  return res.json();
}

export async function deleteNotification(id: string, token?: string) {
  const res = await fetch(`${API_BASE_URL}/notifications/${id}`, {
    method: 'DELETE',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to delete notification');
  return res.json();
}

export async function getUserInvitations(token?: string): Promise<UserInvitationItem[]> {
  const res = await fetch(`${API_BASE_URL}/invitations/my`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch invitations');
  return res.json();
}

export async function acceptUserInvitation(idOrToken: string, token?: string) {
  const res = await fetch(`${API_BASE_URL}/invitations/${idOrToken}/accept`, {
    method: 'POST',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to accept invitation' }));
    throw new Error(err.detail || 'Failed to accept invitation');
  }
  return res.json();
}

export async function declineUserInvitation(idOrToken: string, token?: string) {
  const res = await fetch(`${API_BASE_URL}/invitations/${idOrToken}/decline`, {
    method: 'POST',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to decline invitation' }));
    throw new Error(err.detail || 'Failed to decline invitation');
  }
  return res.json();
}

export async function getActivityFeed(organizationId: string, token?: string): Promise<ActivityItem[]> {
  const res = await fetch(`${API_BASE_URL}/notifications/activity?organization_id=${organizationId}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) return [];
  return res.json();
}
