import { apiClient } from '../../lib/api-client';

const API_BASE = '/api/v1';

async function authedFetch(url: string, token: string, orgId: string, options: any = {}) {
  const method = (options.method || 'GET').toUpperCase();
  const headers = { ...options.headers } as any;
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (orgId) headers['X-Organization-ID'] = orgId;
  
  const path = url.includes('/api/v1') ? url.substring(url.indexOf('/api/v1') + 7) : url;

  try {
    const response = await apiClient({
      url: path,
      method,
      headers,
      data: options.body instanceof FormData ? options.body : (options.body ? (typeof options.body === 'string' ? JSON.parse(options.body) : options.body) : undefined),
      onUploadProgress: options.onUploadProgress,
      signal: options.signal,
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
  } catch (err: any) {
    if (err.name === 'CanceledError' || err.name === 'AbortError') {
      throw new Error('Upload cancelled.');
    }
    const status = err.response?.status;
    const detail = err.response?.data?.detail || err.response?.data?.message || err.message;
    if (status === 413) throw new Error('File exceeds 50 MB server limit.');
    if (status === 401 || status === 403) throw new Error('Permission denied. Unauthorized action.');
    if (status === 507) throw new Error('Storage space unavailable or quota exceeded.');
    if (detail) throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
    throw err;
  }
}

export async function getDocuments(
  token: string,
  orgId: string,
  workspaceId?: string,
  projectId?: string,
  folderId?: string,
  query?: string,
  fileType?: string,
  isTrash?: boolean
) {
  let url = `${API_BASE}/documents/`;
  const params = new URLSearchParams();
  if (workspaceId) params.append('workspace_id', workspaceId);
  if (projectId) params.append('project_id', projectId);
  if (folderId) params.append('folder_id', folderId);
  if (query) params.append('query', query);
  if (fileType) params.append('file_type', fileType);
  if (isTrash) params.append('is_trash', 'true');
  if (params.toString()) url += `?${params.toString()}`;

  const res = await authedFetch(url, token, orgId);
  if (!res.ok) throw new Error('Failed to fetch documents');
  return res.json();
}

export async function getRecentDocuments(token: string, orgId: string, limit: number = 10) {
  const res = await authedFetch(`${API_BASE}/documents/recent?limit=${limit}`, token, orgId);
  if (!res.ok) throw new Error('Failed to fetch recent documents');
  return res.json();
}

export async function getFavoriteDocuments(token: string, orgId: string, limit: number = 50) {
  const res = await authedFetch(`${API_BASE}/documents/favorites?limit=${limit}`, token, orgId);
  if (!res.ok) throw new Error('Failed to fetch favorite documents');
  return res.json();
}

export async function uploadDocument(
  token: string,
  orgId: string,
  workspaceId: string,
  projectId?: string,
  file?: File,
  folderId?: string,
  title?: string,
  visibility: string = "private",
  onProgress?: (percent: number) => void,
  signal?: AbortSignal
) {
  const formData = new FormData();
  if (file) formData.append('file', file);
  if (workspaceId && workspaceId.trim() !== '') formData.append('workspace_id', workspaceId);
  if (projectId && projectId.trim() !== '') formData.append('project_id', projectId);
  if (folderId && folderId.trim() !== '') formData.append('folder_id', folderId);
  if (title) formData.append('title', title);
  formData.append('visibility', visibility);

  const res = await authedFetch(`${API_BASE}/documents/upload`, token, orgId, {
    method: 'POST',
    body: formData,
    onUploadProgress: (progressEvent: any) => {
      if (progressEvent.total && onProgress) {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percentCompleted);
      }
    },
    signal,
  });
  if (!res.ok) throw new Error('Failed to upload document');
  return res.json();
}

export async function getDocument(token: string, orgId: string, id: string) {
  const res = await authedFetch(`${API_BASE}/documents/${id}`, token, orgId);
  if (!res.ok) throw new Error('Failed to fetch document details');
  return res.json();
}

export async function updateDocument(token: string, orgId: string, id: string, payload: any) {
  const res = await authedFetch(`${API_BASE}/documents/${id}`, token, orgId, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to update document');
  return res.json();
}

export async function deleteDocument(token: string, orgId: string, id: string, permanent: boolean = false) {
  let url = `${API_BASE}/documents/${id}`;
  if (permanent) url += '?permanent=true';
  const res = await authedFetch(url, token, orgId, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete document');
}

export async function restoreDocument(token: string, orgId: string, id: string) {
  const res = await authedFetch(`${API_BASE}/documents/${id}/restore`, token, orgId, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to restore document');
  return res.json();
}

export async function toggleFavoriteDocument(token: string, orgId: string, id: string) {
  const res = await authedFetch(`${API_BASE}/documents/${id}/favorite`, token, orgId, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to toggle favorite');
  return res.json();
}

export async function shareDocument(token: string, orgId: string, id: string, sharedWithUserId: string, permissionLevel: string = "read") {
  const res = await authedFetch(`${API_BASE}/documents/${id}/share`, token, orgId, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ shared_with_user_id: sharedWithUserId, permission_level: permissionLevel }),
  });
  if (!res.ok) throw new Error('Failed to share document');
  return res.json();
}

export async function getDocumentPreview(token: string, orgId: string, id: string) {
  const res = await authedFetch(`${API_BASE}/documents/${id}/preview`, token, orgId);
  if (!res.ok) throw new Error('Failed to fetch preview');
  return res.json();
}

export async function getFolders(token: string, orgId: string, workspaceId: string, parentId?: string) {
  let url = `${API_BASE}/folders?workspace_id=${workspaceId}`;
  if (parentId) url += `&parent_id=${parentId}`;
  const res = await authedFetch(url, token, orgId);
  if (!res.ok) throw new Error('Failed to fetch folders');
  return res.json();
}

export async function createFolder(token: string, orgId: string, workspaceId: string, name: string, parentId?: string) {
  const res = await authedFetch(`${API_BASE}/folders`, token, orgId, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ workspace_id: workspaceId, name, parent_id: parentId }),
  });
  if (!res.ok) throw new Error('Failed to create folder');
  return res.json();
}

export async function deleteFolder(token: string, orgId: string, id: string) {
  const res = await authedFetch(`${API_BASE}/folders/${id}`, token, orgId, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete folder');
}

export async function getDocumentMetadata(token: string, orgId: string, id: string) {
  const res = await authedFetch(`${API_BASE}/documents/${id}/metadata`, token, orgId);
  if (!res.ok) throw new Error('Failed to fetch metadata');
  return res.json();
}

export async function updateDocumentMetadata(
  token: string,
  orgId: string,
  id: string,
  payload: any
) {
  const res = await authedFetch(`${API_BASE}/documents/${id}/metadata`, token, orgId, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to update metadata');
  return res.json();
}

export async function getDocumentVersions(token: string, orgId: string, id: string) {
  const res = await authedFetch(`${API_BASE}/documents/${id}/versions`, token, orgId);
  if (!res.ok) throw new Error('Failed to fetch versions history');
  return res.json();
}

export async function restoreDocumentVersion(
  token: string,
  orgId: string,
  id: string,
  version: number
) {
  const res = await authedFetch(`${API_BASE}/documents/${id}/versions/${version}/restore`, token, orgId, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to restore version');
  return res.json();
}

// ---------------- PHASE 3.2 PROCESSING & CHUNKING APIs ----------------

export async function getDocumentProcessingStatus(token: string, orgId: string, id: string) {
  const res = await authedFetch(`${API_BASE}/documents/${id}/processing`, token, orgId);
  if (!res.ok) throw new Error('Failed to fetch processing status');
  return res.json();
}

export async function getDocumentChunks(token: string, orgId: string, id: string) {
  const res = await authedFetch(`${API_BASE}/documents/${id}/chunks`, token, orgId);
  if (!res.ok) throw new Error('Failed to fetch document chunks');
  return res.json();
}

export async function reprocessDocument(token: string, orgId: string, id: string) {
  const res = await authedFetch(`${API_BASE}/documents/${id}/reprocess`, token, orgId, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to trigger reprocess');
  return res.json();
}

export async function downloadDocumentFile(token: string, orgId: string, docId: string, filename: string) {
  const headers: any = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (orgId) headers['X-Organization-ID'] = orgId;

  const response = await apiClient({
    url: `/documents/${docId}/download`,
    method: 'GET',
    headers,
    responseType: 'blob',
  });

  const blob = new Blob([response.data], { type: response.headers['content-type'] || 'application/octet-stream' });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

export async function getDocumentBlobUrl(token: string, orgId: string, docId: string): Promise<string> {
  const headers: any = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (orgId) headers['X-Organization-ID'] = orgId;

  const response = await apiClient({
    url: `/documents/${docId}/download`,
    method: 'GET',
    headers,
    responseType: 'blob',
  });

  const blob = new Blob([response.data], { type: response.headers['content-type'] || 'application/octet-stream' });
  return window.URL.createObjectURL(blob);
}

// ---------------- PHASE 3.3 EMBEDDING & VECTORIZATION APIs ----------------

export async function getDocumentEmbeddingStatus(token: string, orgId: string, id: string) {
  const res = await authedFetch(`${API_BASE}/documents/${id}/embeddings`, token, orgId);
  if (!res.ok) throw new Error('Failed to fetch embedding status');
  return res.json();
}

export async function generateDocumentEmbeddings(
  token: string,
  orgId: string,
  id: string,
  payload?: { provider?: string; model?: string }
) {
  const res = await authedFetch(`${API_BASE}/documents/${id}/embeddings`, token, orgId, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload || { provider: 'gemini' }),
  });
  if (!res.ok) throw new Error('Failed to generate document embeddings');
  return res.json();
}
