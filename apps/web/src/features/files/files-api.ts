const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Authorization': `Bearer ${authToken}`
  };
}

export interface AttachmentItem {
  id: string;
  organization_id: string;
  workspace_id?: string;
  folder_id?: string;
  conversation_id?: string;
  message_id?: string;
  uploaded_by: string;
  uploader_name?: string;
  original_filename: string;
  storage_filename: string;
  mime_type: string;
  file_size: number;
  checksum?: string;
  storage_path: string;
  thumbnail_path?: string;
  preview_url: string;
  download_url: string;
  version: number;
  status: string;
  processing_status?: string;
  scan_status?: string;
  download_count: number;
  created_at: string;
  updated_at?: string;
  deleted_at?: string;
  source_type?: 'conversation' | 'project' | 'direct' | 'workspace';
  source_title?: string;
  shared_with?: string[];
  is_promoted_to_document?: boolean;
  promoted_document_id?: string;
}

export interface AttachmentVersionItem {
  id: string;
  attachment_id: string;
  version_number: number;
  storage_filename: string;
  file_size: number;
  checksum?: string;
  created_by: string;
  creator_name?: string;
  created_at: string;
}

export interface AttachmentAuditLogItem {
  id: string;
  attachment_id: string;
  user_id: string;
  user_name?: string;
  action: string;
  ip_address?: string;
  accessed_at: string;
}

export interface StorageStatsItem {
  total_bytes: number;
  total_files: number;
  by_category: Record<string, number>;
  largest_files: AttachmentItem[];
}

export type StorageStatsResponse = StorageStatsItem;

export interface PaginatedFilesResponse {
  items: AttachmentItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface DuplicateFileErrorPayload {
  error: 'DuplicateFile';
  message: string;
  existing_file_id: string;
  existing_filename: string;
  uploaded_by: string;
  created_at: string;
}

export interface UploadFileOptions {
  file: File;
  organizationId?: string;
  workspaceId?: string;
  folderId?: string;
  conversationId?: string;
  messageId?: string;
  forceDuplicate?: boolean;
  onProgress?: (percent: number) => void;
  onAbortRef?: (abortFn: () => void) => void;
  token?: string;
}

export async function uploadFile(
  options: UploadFileOptions | File,
  conversationIdParam?: string,
  messageIdParam?: string,
  onProgressParam?: (percent: number) => void,
  tokenParam?: string
): Promise<AttachmentItem> {
  let file: File;
  let organizationId: string | undefined;
  let workspaceId: string | undefined;
  let folderId: string | undefined;
  let conversationId: string | undefined;
  let messageId: string | undefined;
  let forceDuplicate: boolean | undefined;
  let onProgress: ((percent: number) => void) | undefined;
  let onAbortRef: ((abortFn: () => void) => void) | undefined;
  let token: string | undefined;

  if (options instanceof File) {
    file = options;
    conversationId = conversationIdParam;
    messageId = messageIdParam;
    onProgress = onProgressParam;
    token = tokenParam;
  } else {
    file = options.file;
    organizationId = options.organizationId;
    workspaceId = options.workspaceId;
    folderId = options.folderId;
    conversationId = options.conversationId;
    messageId = options.messageId;
    forceDuplicate = options.forceDuplicate;
    onProgress = options.onProgress;
    onAbortRef = options.onAbortRef;
    token = options.token;
  }

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const formData = new FormData();
    formData.append('file', file);
    if (organizationId) formData.append('organization_id', organizationId);
    if (workspaceId) formData.append('workspace_id', workspaceId);
    if (folderId) formData.append('folder_id', folderId);
    if (conversationId) formData.append('conversation_id', conversationId);
    if (messageId) formData.append('message_id', messageId);
    if (forceDuplicate) formData.append('force_duplicate', 'true');

    if (onAbortRef) {
      onAbortRef(() => xhr.abort());
    }

    xhr.open('POST', `${API_BASE_URL}/files/upload`);
    const authToken = token || localStorage.getItem('token') || '';
    if (authToken) {
      xhr.setRequestHeader('Authorization', `Bearer ${authToken}`);
    }

    if (xhr.upload && onProgress) {
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
          const percent = Math.round((e.loaded / e.total) * 100);
          onProgress(percent);
        }
      };
    }

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText));
        } catch (err) {
          reject(err);
        }
      } else {
        try {
          const parsed = JSON.parse(xhr.responseText);
          if (xhr.status === 409 && parsed.detail?.error === 'DuplicateFile') {
            const dupErr: any = new Error(parsed.detail.message || 'Identical file already exists.');
            dupErr.isDuplicate = true;
            dupErr.duplicateInfo = parsed.detail;
            reject(dupErr);
            return;
          }
          reject(new Error(parsed.detail || parsed.message || 'Upload failed'));
        } catch (e) {
          reject(new Error(`Upload failed with status ${xhr.status}`));
        }
      }
    };

    xhr.onerror = () => reject(new Error('Network error during file upload'));
    xhr.onabort = () => reject(new Error('Upload cancelled'));
    xhr.send(formData);
  });
}

export async function listFiles(
  organizationId?: string,
  workspaceId?: string,
  folderId?: string,
  conversationId?: string,
  mimeCategory?: string,
  search?: string,
  sortBy: string = 'newest',
  dateFilter?: string,
  page: number = 1,
  pageSize: number = 25,
  sharingFilter: string = 'all',
  token?: string
): Promise<PaginatedFilesResponse> {
  const params = new URLSearchParams();
  if (organizationId) params.append('organization_id', organizationId);
  if (workspaceId) params.append('workspace_id', workspaceId);
  if (folderId) params.append('folder_id', folderId);
  if (conversationId) params.append('conversation_id', conversationId);
  if (mimeCategory && mimeCategory !== 'all') params.append('mime_category', mimeCategory);
  if (sharingFilter && sharingFilter !== 'all') params.append('sharing_filter', sharingFilter);
  if (search && search.trim()) params.append('search', search.trim());
  if (sortBy) params.append('sort_by', sortBy);
  if (dateFilter && dateFilter !== 'all') params.append('date_filter', dateFilter);
  params.append('page', String(page));
  params.append('page_size', String(pageSize));

  const res = await fetch(`${API_BASE_URL}/files?${params.toString()}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch shared files');
  const data = await res.json();
  if (Array.isArray(data)) {
    return { items: data, total: data.length, page: 1, page_size: data.length, total_pages: 1 };
  }
  return data;
}

export async function promoteFileToDocument(
  fileId: string,
  payload?: { workspace_id?: string; project_id?: string; title?: string },
  token?: string
): Promise<{ status: string; message: string; document_id: string; title: string }> {
  const res = await fetch(`${API_BASE_URL}/files/${fileId}/promote-to-document`, {
    method: 'POST',
    headers: { ...getAuthHeaders(token), 'Content-Type': 'application/json' },
    body: JSON.stringify(payload || {})
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || err.message || 'Failed to add file to documents');
  }
  return res.json();
}

export async function getFileDetails(id: string, token?: string): Promise<AttachmentItem> {
  const res = await fetch(`${API_BASE_URL}/files/${id}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch file details');
  return res.json();
}

export async function renameFile(id: string, newFilename: string, token?: string): Promise<AttachmentItem> {
  const res = await fetch(`${API_BASE_URL}/files/${id}`, {
    method: 'PATCH',
    headers: { ...getAuthHeaders(token), 'Content-Type': 'application/json' },
    body: JSON.stringify({ original_filename: newFilename })
  });
  if (!res.ok) throw new Error('Failed to rename file');
  return res.json();
}

export async function moveFile(id: string, folderId: string | null, token?: string): Promise<AttachmentItem> {
  const res = await fetch(`${API_BASE_URL}/files/${id}`, {
    method: 'PATCH',
    headers: { ...getAuthHeaders(token), 'Content-Type': 'application/json' },
    body: JSON.stringify({ folder_id: folderId })
  });
  if (!res.ok) throw new Error('Failed to move file');
  return res.json();
}

export async function softDeleteFile(id: string, token?: string) {
  const res = await fetch(`${API_BASE_URL}/files/${id}`, {
    method: 'DELETE',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to delete file');
  return res.json();
}

export async function restoreFile(id: string, token?: string) {
  const res = await fetch(`${API_BASE_URL}/files/${id}/restore`, {
    method: 'POST',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to restore file');
  return res.json();
}

export async function listFileVersions(id: string, token?: string): Promise<AttachmentVersionItem[]> {
  const res = await fetch(`${API_BASE_URL}/files/${id}/versions`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch file version history');
  return res.json();
}

export async function uploadFileVersion(id: string, file: File, token?: string): Promise<AttachmentItem> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE_URL}/files/${id}/versions`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: formData
  });
  if (!res.ok) throw new Error('Failed to upload new version');
  return res.json();
}

export async function restoreFileVersion(id: string, versionNumber: number, token?: string): Promise<AttachmentItem> {
  const res = await fetch(`${API_BASE_URL}/files/${id}/versions/${versionNumber}/restore`, {
    method: 'POST',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to restore file version');
  return res.json();
}

export async function getFileAuditLogs(id: string, token?: string): Promise<AttachmentAuditLogItem[]> {
  const res = await fetch(`${API_BASE_URL}/files/${id}/audit`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch file audit logs');
  return res.json();
}

export async function getStorageStats(organizationId?: string, workspaceId?: string, token?: string): Promise<StorageStatsResponse> {
  const params = new URLSearchParams();
  if (organizationId) params.append('organization_id', organizationId);
  if (workspaceId) params.append('workspace_id', workspaceId);

  const res = await fetch(`${API_BASE_URL}/files/storage/stats?${params.toString()}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch storage statistics');
  return res.json();
}
