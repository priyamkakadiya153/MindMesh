const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface UniversalSearchResultItem {
  entity_id: string;
  entity_type: string;
  title: string;
  snippet: string;
  project_name: string;
  score: number;
  created_at: string;
}

export interface UniversalSearchResponse {
  query: string;
  total_matches: number;
  results: UniversalSearchResultItem[];
  matching_concepts: string[];
  suggested_questions: string[];
}

export interface EntityDetailResponse {
  identity: {
    entity_id: string;
    entity_type: string;
    name: string;
    status: string;
    owner: string;
    created_at: string;
  };
  relationships: Array<{
    relation_type: string;
    target_type: string;
    target_id: string;
    label: string;
  }>;
  activity: Array<{
    timestamp: string;
    action: string;
    actor: string;
    summary: string;
  }>;
  evidence: string[];
  lineage: Array<{
    step: number;
    type: string;
    label: string;
  }>;
  ai_insights: string[];
}

export interface ContextPackItem {
  pack_id: string;
  pack_title: string;
  scope: string;
  chips: Array<{ type: string; id: string; label: string }>;
  created_at: string;
}

export interface ActivityEventItem {
  event_id: string;
  entity_type: string;
  entity_name: string;
  action: string;
  actor: string;
  project: string;
  timestamp: string;
}

export interface PersonalWorkspaceResponse {
  user_name: string;
  my_tasks: Array<{ task_id: string; title: string; status: string }>;
  my_decisions: Array<{ decision_id: string; title: string; status: string }>;
  my_projects: Array<{ project_id: string; name: string; role: string }>;
  saved_context_packs: ContextPackItem[];
  recent_items: Array<{ type: string; name: string }>;
}

export interface ProjectWorkspaceResponse {
  project_id: string;
  project_name: string;
  overview: {
    status: string;
    progress_percent: number;
    current_sprint: string;
  };
  counts: {
    documents: number;
    decisions: number;
    tasks: number;
    risks: number;
    workflows: number;
    insights: number;
  };
  lineage_summary: string;
  provenance_label: string;
}

export async function executeUniversalSearch(
  query: string,
  types?: string[],
  token?: string
): Promise<UniversalSearchResponse> {
  const params = new URLSearchParams();
  params.append('q', query);
  if (types) {
    types.forEach(t => params.append('types', t));
  }
  const res = await fetch(`${API_BASE_URL}/knowledge-os/universal-search?${params.toString()}`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to execute universal search');
  return res.json();
}

export async function fetchEntityDetail(
  entityType: string,
  entityId: string,
  token?: string
): Promise<EntityDetailResponse> {
  const res = await fetch(`${API_BASE_URL}/knowledge-os/entity/${entityType}/${entityId}`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch entity detail');
  return res.json();
}

export async function createContextPack(
  title: string,
  chips: Array<{ type: string; id: string; label: string }>,
  token?: string
): Promise<ContextPackItem> {
  const res = await fetch(`${API_BASE_URL}/knowledge-os/context-pack`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ title, chips })
  });
  if (!res.ok) throw new Error('Failed to create context pack');
  return res.json();
}

export async function fetchActivityFeed(
  token?: string
): Promise<ActivityEventItem[]> {
  const res = await fetch(`${API_BASE_URL}/knowledge-os/activity`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch activity feed');
  return res.json();
}

export async function executeUniversalCommand(
  commandText: string,
  contextEntityId?: string,
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/knowledge-os/command`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ command_text: commandText, context_entity_id: contextEntityId })
  });
  if (!res.ok) throw new Error('Failed to execute universal command');
  return res.json();
}

export async function fetchPersonalWorkspace(
  token?: string
): Promise<PersonalWorkspaceResponse> {
  const res = await fetch(`${API_BASE_URL}/knowledge-os/personal-workspace`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch personal workspace');
  return res.json();
}

export async function fetchProjectWorkspace(
  projectId: string,
  token?: string
): Promise<ProjectWorkspaceResponse> {
  const res = await fetch(`${API_BASE_URL}/knowledge-os/project-workspace/${projectId}`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch project workspace');
  return res.json();
}
