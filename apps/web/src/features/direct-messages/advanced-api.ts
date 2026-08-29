import { Message } from './types';

const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface PinnedMessageItem {
  id: string;
  conversation_id: string;
  message_id: string;
  pinned_by: string;
  pinned_by_name: string;
  pinned_at: string;
  message: Message;
}

export async function replyToMessage(id: string, content: string, token?: string): Promise<Message> {
  const res = await fetch(`${API_BASE_URL}/messages/${id}/reply`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ content })
  });
  if (!res.ok) throw new Error('Failed to reply to message');
  return res.json();
}

export async function forwardMessage(id: string, targetConversationIds: string[], token?: string): Promise<Message[]> {
  const res = await fetch(`${API_BASE_URL}/messages/${id}/forward`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ target_conversation_ids: targetConversationIds })
  });
  if (!res.ok) throw new Error('Failed to forward message');
  return res.json();
}

export async function addReaction(id: string, emoji: string, token?: string) {
  const res = await fetch(`${API_BASE_URL}/messages/${id}/react`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ emoji })
  });
  if (!res.ok) throw new Error('Failed to add reaction');
  return res.json();
}

export async function removeReaction(id: string, emoji: string, token?: string) {
  const res = await fetch(`${API_BASE_URL}/messages/${id}/react?emoji=${encodeURIComponent(emoji)}`, {
    method: 'DELETE',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to remove reaction');
  return res.json();
}

export async function pinMessage(id: string, token?: string) {
  const res = await fetch(`${API_BASE_URL}/messages/${id}/pin`, {
    method: 'POST',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to pin message');
  return res.json();
}

export async function unpinMessage(id: string, token?: string) {
  const res = await fetch(`${API_BASE_URL}/messages/${id}/pin`, {
    method: 'DELETE',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to unpin message');
  return res.json();
}

export async function getMessageThread(id: string, token?: string): Promise<Message[]> {
  const res = await fetch(`${API_BASE_URL}/messages/${id}/thread`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch thread replies');
  return res.json();
}

export async function getPinnedMessages(conversationId: string, token?: string): Promise<PinnedMessageItem[]> {
  const res = await fetch(`${API_BASE_URL}/conversations/${conversationId}/pins`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch pinned messages');
  return res.json();
}

export async function toggleFavoriteConversation(conversationId: string, token?: string) {
  const res = await fetch(`${API_BASE_URL}/conversations/${conversationId}/favorite`, {
    method: 'POST',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to toggle favorite');
  return res.json();
}

export async function toggleMuteConversation(conversationId: string, isMuted: boolean, token?: string) {
  const res = await fetch(`${API_BASE_URL}/conversations/${conversationId}/mute`, {
    method: 'PATCH',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ is_muted: isMuted })
  });
  if (!res.ok) throw new Error('Failed to toggle mute');
  return res.json();
}

export async function saveMessageDraft(conversationId: string, content: string, token?: string) {
  const res = await fetch(`${API_BASE_URL}/messages/drafts`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ conversation_id: conversationId, content })
  });
  if (!res.ok) throw new Error('Failed to save draft');
  return res.json();
}

export async function getMessageDraft(conversationId: string, token?: string): Promise<{ content: string }> {
  const res = await fetch(`${API_BASE_URL}/messages/drafts?conversation_id=${conversationId}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) return { content: '' };
  return res.json();
}
