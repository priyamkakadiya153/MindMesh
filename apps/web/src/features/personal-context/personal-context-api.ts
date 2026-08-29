const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface UserPersonalContextResponse {
  user_id: string;
  username: string;
  active_project_id?: string;
  active_project_name: string;
  pinned_project_ids: string[];
  assigned_tasks_count: number;
  assigned_tasks: Array<{ id: string; title: string; status: string }>;
  context_priority: string[];
}

export interface FocusRecommendationItem {
  id: string;
  type: string;
  title: string;
  reason: string;
  priority: string;
}

export interface AwaySummaryResponse {
  period: string;
  summary_items: Array<{
    project_name: string;
    change_type: string;
    title: string;
    reason: string;
    timestamp: string;
  }>;
}

export async function fetchPersonalContext(
  activeProjectId?: string,
  token?: string
): Promise<UserPersonalContextResponse> {
  const url = activeProjectId ? `${API_BASE_URL}/me/context?active_project_id=${activeProjectId}` : `${API_BASE_URL}/me/context`;
  const res = await fetch(url, { headers: getAuthHeaders(token) });
  if (!res.ok) throw new Error('Failed to fetch personal context');
  return res.json();
}

export async function fetchFocusRecommendations(
  activeProjectId?: string,
  token?: string
): Promise<FocusRecommendationItem[]> {
  const url = activeProjectId ? `${API_BASE_URL}/me/context/focus?active_project_id=${activeProjectId}` : `${API_BASE_URL}/me/context/focus`;
  const res = await fetch(url, { method: 'POST', headers: getAuthHeaders(token) });
  if (!res.ok) throw new Error('Failed to fetch focus recommendations');
  return res.json();
}

export async function fetchAwaySummary(
  token?: string
): Promise<AwaySummaryResponse> {
  const res = await fetch(`${API_BASE_URL}/me/context/away-summary`, { method: 'POST', headers: getAuthHeaders(token) });
  if (!res.ok) throw new Error('Failed to fetch away summary');
  return res.json();
}

export async function pinProject(
  projectId: string,
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/me/context/pin`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ project_id: projectId })
  });
  if (!res.ok) throw new Error('Failed to pin project');
  return res.json();
}

export async function unpinProject(
  projectId: string,
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/me/context/unpin`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ project_id: projectId })
  });
  if (!res.ok) throw new Error('Failed to unpin project');
  return res.json();
}
