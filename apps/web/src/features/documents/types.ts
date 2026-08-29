export interface Document {
  id: string;
  organization_id?: string;
  workspace_id?: string;
  project_id?: string;
  folder_id?: string;
  uploaded_by?: string;
  title?: string;
  filename: string;
  original_filename?: string;
  mime_type: string;
  extension: string;
  size: number;
  size_bytes?: number;
  checksum_sha256?: string;
  storage_provider?: string;
  storage_path?: string;
  processing_status?: string;
  status?: string;
  visibility?: 'private' | 'workspace' | 'organization' | 'shared';
  version?: number;
  is_favorite?: boolean;
  deleted_at?: string;
  created_at: string;
  updated_at?: string;
}

export interface Folder {
  id: string;
  organization_id: string;
  workspace_id: string;
  parent_id?: string;
  name: string;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface UploadQueueItem {
  id: string;
  name: string;
  size?: number;
  progress: number;
  speed?: string;
  remainingTime?: string;
  status: 'queued' | 'uploading' | 'processing' | 'completed' | 'failed' | 'cancelled';
  error?: string;
  file?: File;
}

export interface DocumentMetadata {
  id: string;
  document_id: string;
  title: string;
  description?: string;
  author?: string;
  language?: string;
  keywords?: { keywords?: string[] };
  labels?: { labels?: string[] };
  categories?: { categories?: string[] };
  department?: string;
  business_unit?: string;
  confidentiality: 'public' | 'internal' | 'confidential' | 'restricted';
  custom_metadata?: Record<string, any>;
  updated_at: string;
}

export interface DocumentVersion {
  id: string;
  document_id: string;
  version_number: number;
  storage_path: string;
  checksum_sha256: string;
  file_size: number;
  uploaded_by?: string;
  change_summary?: string;
  created_at: string;
}

export interface DocumentAuditLog {
  id: string;
  document_id: string;
  user_id?: string;
  action: string;
  metadata?: Record<string, any>;
  timestamp: string;
}

