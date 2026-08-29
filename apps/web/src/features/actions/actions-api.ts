const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface ActionRecommendation {
  id: string;
  action_type: 'CREATE_TASK' | 'UPDATE_TASK' | 'VERIFY_KNOWLEDGE' | 'RESOLVE_CONFLICT' | 'CREATE_DRAFT' | string;
  title: string;
  why: string;
  source_type: string;
  source_id: string;
  expected_result: string;
  payload: Record<string, any>;
  priority: 'LOW' | 'NORMAL' | 'HIGH';
}

export interface ActionExecuteResponse {
  success: boolean;
  is_duplicate?: boolean;
  message: string;
  entity_type?: string;
  entity_id?: string;
}

export async function fetchActionRecommendations(
  workspaceId?: string,
  projectId?: string,
  token?: string
): Promise<ActionRecommendation[]> {
  const params = new URLSearchParams();
  if (workspaceId) params.append('workspace_id', workspaceId);
  if (projectId) params.append('project_id', projectId);

  const res = await fetch(`${API_BASE_URL}/actions/recommendations?${params.toString()}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch action recommendations');
  return res.json();
}

export async function executeAction(
  actionType: string,
  payload: Record<string, any>,
  workspaceId?: string,
  token?: string
): Promise<ActionExecuteResponse> {
  const res = await fetch(`${API_BASE_URL}/actions/execute`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ action_type: actionType, payload, workspace_id: workspaceId })
  });
  if (!res.ok) throw new Error('Failed to execute action');
  return res.json();
}

export async function createDocumentationDraft(
  topic: string,
  projectId?: string,
  workspaceId?: string,
  token?: string
): Promise<ActionExecuteResponse> {
  const res = await fetch(`${API_BASE_URL}/actions/draft-documentation`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ topic, project_id: projectId, workspace_id: workspaceId })
  });
  if (!res.ok) throw new Error('Failed to create documentation draft');
  return res.json();
}
