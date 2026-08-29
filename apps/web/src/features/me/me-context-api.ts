const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface UserContextResponse {
  user_id: string;
  workspace_id?: string;
  needs_attention: {
    overdue_count: number;
    blocked_count: number;
    items: Array<{
      id: string;
      title: string;
      status: string;
      reason: string;
    }>;
  };
  my_tasks: Array<{
    id: string;
    title: string;
    status: string;
    priority: string;
    due_date?: string;
    project_id?: string;
  }>;
  my_projects: Array<{
    id: string;
    name: string;
    status: string;
    description?: string;
  }>;
  recent_knowledge: Array<{
    id: string;
    title: string;
    filename?: string;
    updated_at: string;
  }>;
  recent_activity: Array<{
    id: string;
    event_type: string;
    entity_type?: string;
    created_at: string;
  }>;
  important_updates: Array<any>;
}

export interface CatchUpResponse {
  has_activity_history: boolean;
  since_timestamp: string;
  summary: string;
  new_decisions: Array<{ id: string; content: string; created_at: string }>;
  timeline_events: Array<{ id: string; title: string; event_type: string; occurred_at: string }>;
  new_documents: Array<{ id: string; title: string; filename?: string }>;
}

export async function fetchUserContext(
  workspaceId?: string,
  token?: string
): Promise<UserContextResponse> {
  const params = new URLSearchParams();
  if (workspaceId) params.append('workspace_id', workspaceId);

  const res = await fetch(`${API_BASE_URL}/me/context?${params.toString()}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch personal context');
  return res.json();
}

export async function fetchCatchUpSummary(
  workspaceId?: string,
  projectId?: string,
  token?: string
): Promise<CatchUpResponse> {
  const params = new URLSearchParams();
  if (workspaceId) params.append('workspace_id', workspaceId);
  if (projectId) params.append('project_id', projectId);

  const res = await fetch(`${API_BASE_URL}/me/catch-up?${params.toString()}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch catch-up summary');
  return res.json();
}

export async function recordUserActivity(
  eventType: string,
  entityType?: string,
  entityId?: string,
  workspaceId?: string,
  projectId?: string,
  token?: string
): Promise<void> {
  await fetch(`${API_BASE_URL}/me/activity`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({
      event_type: eventType,
      entity_type: entityType,
      entity_id: entityId,
      workspace_id: workspaceId,
      project_id: projectId
    })
  });
}
