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

export interface CitationItem {
  id: string;
  message_id: string;
  conversation_id?: string;
  document_id: string;
  chunk_id: string;
  document_title: string;
  page_number?: number;
  section_title?: string;
  similarity_score: number;
  confidence_score: 'High' | 'Medium' | 'Low';
  citation_order: number;
  citation_tag: string;
  chunk_snippet?: string;
}

export interface ChunkPreview {
  document_id: string;
  chunk_id: string;
  document_title: string;
  page_number?: number;
  section_title?: string;
  text: string;
  character_count: number;
}

export async function getMessageCitations(token: string, orgId: string, messageId: string): Promise<CitationItem[]> {
  const res = await authedFetch(`${API_BASE}/chat/messages/${messageId}/citations`, token, orgId);
  if (!res.ok) throw new Error('Failed to fetch citations');
  return res.json();
}

export async function getDocumentChunkPreview(
  token: string,
  orgId: string,
  documentId: string,
  chunkId: string
): Promise<ChunkPreview> {
  const res = await authedFetch(`${API_BASE}/documents/${documentId}/chunks/${chunkId}`, token, orgId);
  if (!res.ok) throw new Error('Failed to fetch document chunk preview');
  return res.json();
}

export async function validateCitations(token: string, orgId: string, payload: any) {
  const res = await authedFetch(`${API_BASE}/chat/citations/validate`, token, orgId, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to validate citations');
  return res.json();
}
