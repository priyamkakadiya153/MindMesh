import { Conversation, Message } from './types';

const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export async function getOrCreatePrivateConversation(
  targetUserId: string,
  organizationId: string,
  workspaceId?: string,
  token?: string
): Promise<Conversation> {
  const res = await fetch(`${API_BASE_URL}/conversations/private`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({
      target_user_id: targetUserId,
      organization_id: organizationId,
      workspace_id: workspaceId || null
    })
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || errorData.message || 'Failed to initialize private conversation');
  }
  return res.json();
}

export async function listConversations(
  organizationId: string,
  workspaceId?: string,
  token?: string
): Promise<Conversation[]> {
  const params = new URLSearchParams({ organization_id: organizationId });
  if (workspaceId) params.append('workspace_id', workspaceId);

  const res = await fetch(`${API_BASE_URL}/conversations?${params.toString()}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) {
    throw new Error('Failed to fetch conversations');
  }
  return res.json();
}

export async function getConversationDetails(
  id: string,
  token?: string
): Promise<Conversation> {
  const res = await fetch(`${API_BASE_URL}/conversations/${id}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) {
    throw new Error('Failed to fetch conversation details');
  }
  return res.json();
}

export async function markConversationAsRead(
  id: string,
  token?: string
): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE_URL}/conversations/${id}/read`, {
    method: 'POST',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) {
    throw new Error('Failed to mark conversation as read');
  }
  return res.json();
}

import { AttachmentItem } from './types';

export async function uploadAttachment(
  file: File,
  conversationId: string,
  token?: string
): Promise<AttachmentItem> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('conversation_id', conversationId);

  const authToken = token || localStorage.getItem('token') || '';
  const res = await fetch(`${API_BASE_URL}/files/upload`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${authToken}`
    },
    body: formData
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const message = typeof err.detail === 'string' ? err.detail : (err.message || 'File upload failed');
    throw new Error(message);
  }
  return res.json();
}

export async function sendMessage(
  conversationId: string,
  content: string,
  messageType = 'text',
  replyToId?: string,
  token?: string,
  clientMsgId?: string,
  attachmentIds?: string[]
): Promise<Message> {
  const res = await fetch(`${API_BASE_URL}/messages`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({
      conversation_id: conversationId,
      content,
      message_type: messageType,
      reply_to_id: replyToId || null,
      client_msg_id: clientMsgId || null,
      attachment_ids: attachmentIds || null
    })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || err.message || 'Failed to send message');
  }
  return res.json();
}

export async function getMessages(
  conversationId: string,
  limit = 50,
  offset = 0,
  token?: string
): Promise<Message[]> {
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString()
  });
  const res = await fetch(`${API_BASE_URL}/messages/${conversationId}?${params.toString()}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) {
    throw new Error('Failed to fetch message history');
  }
  return res.json();
}

export async function editMessage(
  messageId: string,
  content: string,
  token?: string
): Promise<Message> {
  const res = await fetch(`${API_BASE_URL}/messages/${messageId}`, {
    method: 'PATCH',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ content })
  });
  if (!res.ok) {
    throw new Error('Failed to edit message');
  }
  return res.json();
}

export async function deleteMessage(
  messageId: string,
  token?: string
): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE_URL}/messages/${messageId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) {
    throw new Error('Failed to delete message');
  }
  return res.json();
}

export async function searchMessages(
  query: string,
  conversationId?: string,
  token?: string
): Promise<Message[]> {
  const params = new URLSearchParams({ query });
  if (conversationId) params.append('conversation_id', conversationId);

  const res = await fetch(`${API_BASE_URL}/messages?${params.toString()}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) {
    throw new Error('Failed to search messages');
  }
  return res.json();
}
