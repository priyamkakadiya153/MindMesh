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

export async function getAIProviders(token: string, orgId: string) {
  const res = await authedFetch(`${API_BASE}/ai/providers`, token, orgId);
  if (!res.ok) throw new Error('Failed to fetch providers');
  return res.json();
}

export async function getAIModels(token: string, orgId: string) {
  const res = await authedFetch(`${API_BASE}/ai/models`, token, orgId);
  if (!res.ok) throw new Error('Failed to fetch models');
  return res.json();
}

export async function getAISettings(token: string, orgId: string, workspaceId: string) {
  const res = await authedFetch(`${API_BASE}/ai/settings?workspace_id=${workspaceId}`, token, orgId);
  if (!res.ok) throw new Error('Failed to fetch AI settings');
  return res.json();
}

export async function updateAISettings(token: string, orgId: string, payload: any) {
  const res = await authedFetch(`${API_BASE}/ai/settings`, token, orgId, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to update AI settings');
  return res.json();
}

export async function getAIHealth(token: string, orgId: string) {
  const res = await authedFetch(`${API_BASE}/ai/health`, token, orgId);
  if (!res.ok) throw new Error('Failed to fetch AI health status');
  return res.json();
}

export async function testAIConnection(token: string, orgId: string, payload: any) {
  const res = await authedFetch(`${API_BASE}/ai/test`, token, orgId, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to execute AI test connection');
  return res.json();
}
