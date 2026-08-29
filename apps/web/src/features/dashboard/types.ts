export interface Stats {
  workspaces_count: number;
  projects_count: number;
  projects_indexed_count?: number;
  projects_pending_count?: number;
  documents_count: number;
  documents_indexed_count?: number;
  chunks_count?: number;
  chats_count: number;
  messages_today_count?: number;
  storage_used: number;
  members_count: number;
  indexing_status?: string;
}

export interface RecentProject {
  id: string;
  name: string;
  slug: string;
  created_at: string;
  updated_at?: string;
  status?: string;
}

export interface RecentDocument {
  id: string;
  name: string;
  mime_type: string;
  size: number;
  created_at: string;
  processing_status?: string;
  uploader_name?: string;
  storage_path?: string;
  checksum_sha256?: string;
}

export interface RecentChat {
  id: string;
  name: string;
  created_at: string;
  updated_at?: string;
  status?: string;
}

export interface Notification {
  id: string;
  user_id: string;
  title: string;
  message: string;
  priority: string;
  is_read: boolean;
  created_at: string;
}

export interface ActivityLog {
  id: string;
  event_type: string;
  user_id: string;
  created_at: string;
  metadata: any;
}

export interface FavoriteItem {
  id: string;
  user_id: string;
  item_type: string;
  item_id: string;
  name: string;
  slug: string;
  created_at?: string;
}

export interface RecentItem {
  id: string;
  user_id: string;
  item_type: string;
  item_id: string;
  name: string;
  slug: string;
  opened_at: string;
}

export interface DashboardData {
  organization: {
    id: string;
    name: string;
    slug: string;
  };
  workspace: {
    id: string;
    name: string;
    slug: string;
  } | null;
  statistics: Stats;
  recent_projects: RecentProject[];
  recent_documents: RecentDocument[];
  recent_chats: RecentChat[];
  notifications: Notification[];
  activity: ActivityLog[];
  favorites: FavoriteItem[];
  ai_summary: {
    insights: string;
    last_generation: string;
    status: string;
  };
}

export interface Widget {
  id: string;
  name: string;
  enabled: boolean;
  col_span: number;
}

export interface WidgetSectionState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  isRevalidating?: boolean;
  isCachedFallback?: boolean;
}

