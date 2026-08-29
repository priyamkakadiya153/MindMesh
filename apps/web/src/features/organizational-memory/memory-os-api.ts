const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface FeedUpdateItem {
  title: string;
  type: string;
  governance_status: string;
  why_it_matters: string;
  action: string;
}

export interface FeedGroup {
  id: string;
  group_title: string;
  updates_count: number;
  items: FeedUpdateItem[];
}

export interface ProjectMemoryOverview {
  id: string;
  name: string;
  status: string;
  current_state: string;
  important_decisions: number;
  open_tasks: number;
  blockers: number;
}

export interface MemoryHomeResponse {
  scope: string;
  project_memory: ProjectMemoryOverview;
  knowledge_feed: FeedGroup[];
  recent_knowledge: Array<{
    id: string;
    title: string;
    type: string;
    status: string;
    updated_at: string;
  }>;
  suggested_exploration: string[];
}

export interface EntityMemoryResponse {
  entity_id: string;
  entity_type: string;
  identity: {
    title: string;
    status: string;
  };
  context: {
    project_name: string;
    workspace_name: string;
  };
  source: {
    title: string;
    citation: string;
  };
  relationships: Array<{
    type: string;
    title: string;
  }>;
  governance_state: string;
  history: Array<{
    event: string;
    timestamp: string;
  }>;
  available_actions: string[];
}

export interface MemoryQueryResult {
  query: string;
  scope: string;
  query_type: string;
  answer: any;
}

export interface MemoryHealthResponse {
  search_index: string;
  knowledge_graph: string;
  governance_engine: string;
  timeline_engine: string;
  ai_synthesis_engine: string;
  overall_status: string;
  message: string;
}

export async function fetchMemoryHome(
  scope: string = 'ORGANIZATION',
  token?: string
): Promise<MemoryHomeResponse> {
  const params = new URLSearchParams({ scope });
  const res = await fetch(`${API_BASE_URL}/memory/home?${params.toString()}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch memory home');
  return res.json();
}

export async function fetchEntityMemory(
  entityType: string,
  entityId: string,
  token?: string
): Promise<EntityMemoryResponse> {
  const res = await fetch(`${API_BASE_URL}/memory/entity/${entityType}/${entityId}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch entity memory');
  return res.json();
}

export async function queryMemoryOS(
  query: string,
  scope: string = 'CURRENT_PROJECT',
  token?: string
): Promise<MemoryQueryResult> {
  const res = await fetch(`${API_BASE_URL}/memory/query`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ query, scope })
  });
  if (!res.ok) throw new Error('Failed to query memory OS');
  return res.json();
}

export async function fetchMemoryHealth(
  token?: string
): Promise<MemoryHealthResponse> {
  const res = await fetch(`${API_BASE_URL}/memory/health`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch memory health');
  return res.json();
}

export async function triggerMemoryReindex(
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/memory/reindex`, {
    method: 'POST',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to reindex memory OS');
  return res.json();
}
