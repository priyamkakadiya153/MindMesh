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
    data: options.body instanceof FormData ? options.body : (options.body ? (typeof options.body === 'string' ? JSON.parse(options.body) : options.body) : undefined),
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

export interface MemoryItem {
  id: string;
  conversation_id?: string;
  workspace_id: string;
  organization_id: string;
  memory_type: string;
  importance: number;
  content: string;
  is_pinned: boolean;
  expiration_status: string;
}

export interface SummaryItem {
  id: string;
  conversation_id: string;
  workspace_id: string;
  organization_id: string;
  summary: string;
  message_range_start: number;
  message_range_end: number;
  key_decisions?: { items?: string[] };
  action_items?: { items?: string[] };
  topics?: { items?: string[] };
}

export async function getChatMemories(
  token: string,
  orgId: string,
  workspaceId: string,
  conversationId?: string
): Promise<MemoryItem[]> {
  let url = `${API_BASE}/chat/memory?workspace_id=${workspaceId}`;
  if (conversationId) url += `&conversation_id=${conversationId}`;
  const res = await authedFetch(url, token, orgId);
  if (!res.ok) throw new Error('Failed to fetch memories');
  return res.json();
}

export async function getChatSummaries(
  token: string,
  orgId: string,
  conversationId: string
): Promise<SummaryItem[]> {
  const res = await authedFetch(`${API_BASE}/chat/summaries?conversation_id=${conversationId}`, token, orgId);
  if (!res.ok) throw new Error('Failed to fetch summaries');
  return res.json();
}

export async function triggerSummarize(
  token: string,
  orgId: string,
  payload: { conversation_id: string; workspace_id: string; provider?: string; model?: string }
): Promise<SummaryItem> {
  const res = await authedFetch(`${API_BASE}/chat/summarize`, token, orgId, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to generate summary');
  return res.json();
}

export async function updateMemory(
  token: string,
  orgId: string,
  memoryId: string,
  payload: { is_pinned?: boolean; importance?: number; content?: string }
): Promise<MemoryItem> {
  const res = await authedFetch(`${API_BASE}/chat/memory/${memoryId}`, token, orgId, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to update memory');
  return res.json();
}

export async function deleteMemory(token: string, orgId: string, memoryId: string) {
  const res = await authedFetch(`${API_BASE}/chat/memory/${memoryId}`, token, orgId, {
    method: 'DELETE'
  });
  if (!res.ok) throw new Error('Failed to delete memory');
  return res.json();
}
