import { apiClient } from '../../lib/api-client';

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
  email: string;
  role: string;
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
  const res = await apiClient.get('/notifications');
  const data = res.data;
  if (Array.isArray(data)) {
    const unread = data.filter((n: any) => !n.is_read).length;
    return { unread_count: unread, notifications: data };
  }
  return data;
}

export async function markNotificationRead(id: string, token?: string) {
  const res = await apiClient.patch(`/notifications/${id}/read`);
  return res.data;
}

export async function markAllNotificationsRead(token?: string) {
  const res = await apiClient.patch('/notifications/read-all');
  return res.data;
}

export async function deleteNotification(id: string, token?: string) {
  const res = await apiClient.delete(`/notifications/${id}`);
  return res.data;
}

export async function getUserInvitations(token?: string): Promise<UserInvitationItem[]> {
  const res = await apiClient.get('/invitations/my');
  return res.data;
}

export async function acceptUserInvitation(idOrToken: string, token?: string) {
  const res = await apiClient.post(`/invitations/${idOrToken}/accept`);
  return res.data;
}

export async function declineUserInvitation(idOrToken: string, token?: string) {
  const res = await apiClient.post(`/invitations/${idOrToken}/decline`);
  return res.data;
}

export async function getActivityFeed(organizationId: string, token?: string): Promise<ActivityItem[]> {
  try {
    const res = await apiClient.get(`/notifications/activity?organization_id=${organizationId}`);
    return res.data;
  } catch {
    return [];
  }
}

