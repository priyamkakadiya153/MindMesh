const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface KnowledgeCounts {
  documents: number;
  decisions: number;
  tasks: number;
  conversations: number;
  projects: number;
}

export interface KnowledgeItem {
  id: string;
  type: string;
  title: string;
  description: string;
  source_type: string;
  source_id: string;
  timestamp: string;
  deep_link: string;
  workspace_id?: string;
  project_id?: string;
}

export interface ActivityItem {
  id: string;
  event_type: string;
  title: string;
  description: string;
  occurred_at: string;
  source_type: string;
  source_id: string;
}

export interface HubOverviewResponse {
  counts: KnowledgeCounts;
  recent_knowledge: KnowledgeItem[];
  recent_activity: ActivityItem[];
}

export interface ProjectKnowledgeOverviewResponse {
  project_id: string;
  name: string;
  description?: string;
  status: string;
  counts: Record<string, number>;
  key_decisions: string[];
  open_tasks: string[];
}

export async function fetchHubOverview(
  workspaceId?: string,
  limit: number = 30,
  token?: string
): Promise<HubOverviewResponse> {
  const params = new URLSearchParams({ limit: limit.toString() });
  if (workspaceId && workspaceId !== 'all') params.append('workspace_id', workspaceId);

  const res = await fetch(`${API_BASE_URL}/knowledge/hub/overview?${params.toString()}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch Knowledge Hub overview');
  return res.json();
}

export async function fetchProjectKnowledgeOverview(
  projectId: string,
  token?: string
): Promise<ProjectKnowledgeOverviewResponse> {
  const res = await fetch(`${API_BASE_URL}/knowledge/hub/project/${projectId}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch project knowledge overview');
  return res.json();
}
