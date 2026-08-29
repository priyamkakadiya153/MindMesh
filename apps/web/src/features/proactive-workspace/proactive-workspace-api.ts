const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface ProactiveInsightItem {
  insight_id: string;
  type: string;
  priority: string;
  title: string;
  summary: string;
  reason: string;
  evidence: string[];
  related_entities: string[];
  suggested_action: string;
  status: string;
  created_at: string;
  expires_at: string;
}

export interface IntelligenceInboxResponse {
  unread_count: number;
  critical_count: number;
  important_count: number;
  items: ProactiveInsightItem[];
}

export async function fetchProactiveFeed(
  projectId?: string,
  filterStatus: string = 'UNREAD',
  token?: string
): Promise<ProactiveInsightItem[]> {
  const params = new URLSearchParams();
  if (projectId) params.append('project_id', projectId);
  params.append('filter_status', filterStatus);

  const res = await fetch(`${API_BASE_URL}/proactive/feed?${params.toString()}`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch proactive feed');
  return res.json();
}

export async function dismissInsight(
  insightId: string,
  reason?: string,
  token?: string
): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE_URL}/proactive/insights/${insightId}/dismiss`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ reason })
  });
  if (!res.ok) throw new Error('Failed to dismiss insight');
  return res.json();
}

export async function snoozeInsight(
  insightId: string,
  duration: string = '1d',
  token?: string
): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE_URL}/proactive/insights/${insightId}/snooze`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ duration })
  });
  if (!res.ok) throw new Error('Failed to snooze insight');
  return res.json();
}

export async function followEntity(
  entityId: string,
  token?: string
): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE_URL}/proactive/insights/follow`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ entity_id: entityId })
  });
  if (!res.ok) throw new Error('Failed to follow entity');
  return res.json();
}

export async function fetchIntelligenceInbox(
  token?: string
): Promise<IntelligenceInboxResponse> {
  const res = await fetch(`${API_BASE_URL}/proactive/inbox`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch intelligence inbox');
  return res.json();
}
