const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface TimelineEventItem {
  id: string;
  organization_id: str;
  workspace_id?: str;
  project_id?: str;
  event_type: 'DOCUMENT_CREATED' | 'DOCUMENT_UPDATED' | 'FILE_SHARED' | 'CONVERSATION_STARTED' | 'DECISION_MADE' | 'TASK_CREATED' | 'TASK_COMPLETED' | 'IMPORTANT_FACT_DISCOVERED' | 'PROJECT_CREATED' | 'PROJECT_UPDATED' | 'MILESTONE' | 'KNOWLEDGE_UPDATED';
  importance: 'HIGH' | 'MEDIUM' | 'LOW';
  title: string;
  description?: string;
  source_type: 'document' | 'file' | 'message' | 'conversation' | 'project' | 'task' | 'decision' | 'insight';
  source_id: string;
  occurred_at?: string;
  created_at?: string;
  metadata?: Record<string, any>;
  deep_link?: string;
}

export interface TimelineListResponse {
  events: TimelineEventItem[];
  total_count: number;
  page: number;
  limit: number;
  total_pages: number;
}

export async function fetchTimelineEvents(
  organizationId?: string,
  workspaceId?: string,
  projectId?: string,
  eventType: string = 'all',
  importance: string = 'all',
  searchQuery?: string,
  page: int = 1,
  limit: int = 30,
  token?: string
): Promise<TimelineListResponse> {
  const params = new URLSearchParams({ page: page.toString(), limit: limit.toString() });
  if (workspaceId && workspaceId !== 'all') params.append('workspace_id', workspaceId);
  if (projectId && projectId !== 'all') params.append('project_id', projectId);
  if (eventType && eventType !== 'all') params.append('event_type', eventType);
  if (importance && importance !== 'all') params.append('importance', importance);
  if (searchQuery && searchQuery.trim()) params.append('q', searchQuery.trim());

  const res = await fetch(`${API_BASE_URL}/timeline?${params.toString()}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch timeline events');
  return res.json();
}

export async function triggerTimelineBackfill(token?: string): Promise<{ success: boolean; stats: any }> {
  const res = await fetch(`${API_BASE_URL}/timeline/backfill`, {
    method: 'POST',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to trigger timeline backfill');
  return res.json();
}
