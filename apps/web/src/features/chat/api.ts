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

export interface BuildPromptPayload {
  query: string;
  conversation_id?: string;
  workspace_id?: string;
  template_name?: string;
  top_k?: number;
  max_tokens?: number;
}

export async function buildAssembledPrompt(
  token: string,
  orgId: string,
  payload: BuildPromptPayload
) {
  const res = await authedFetch(`${API_BASE}/prompt/build`, token, orgId, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to assemble prompt');
  return res.json();
}

export interface StreamChatPayload {
  query: string;
  conversation_id?: string;
  workspace_id?: string;
  template_name?: string;
  provider?: string;
  model?: string;
}

export async function streamChatResponse(
  token: string,
  orgId: string,
  payload: StreamChatPayload,
  onEvent: (event: any) => void,
  onError: (err: any) => void,
  signal?: AbortSignal
) {
  try {
    const response = await fetch(`${API_BASE}/ai/gateway/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        'X-Organization-ID': orgId
      },
      body: JSON.stringify({
        message: payload.query,
        query: payload.query,
        conversation_id: payload.conversation_id,
        workspace_id: payload.workspace_id,
        provider: payload.provider || 'gemini',
        model: payload.model || 'gemini-2.5-flash',
        stream: true
      }),
      signal
    });

    if (!response.ok || !response.body) {
      throw new Error(`Streaming failed with HTTP status ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';

      for (const block of lines) {
        if (!block.trim()) continue;
        const eventMatch = block.match(/^event:\s*(.+)$/m);
        const dataMatch = block.match(/^data:\s*(.+)$/m);
        if (dataMatch) {
          try {
            const parsed = JSON.parse(dataMatch[1]);
            onEvent(parsed);
          } catch (e) {
            console.error('Failed to parse SSE data block:', e);
          }
        }
      }
    }
  } catch (err: any) {
    if (err.name === 'AbortError') {
      onEvent({ event: 'cancelled', message: 'Stream aborted by user.' });
    } else {
      onError(err);
    }
  }
}
