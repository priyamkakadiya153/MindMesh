const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface ProactiveInsightItem {
  id: string;
  organization_id: string;
  workspace_id: string;
  target_user_id: string;
  project_id?: string;
  project_name: string;
  event_type: string;
  importance: 'CRITICAL' | 'IMPORTANT' | 'NORMAL' | 'LOW' | string;
  title: string;
  description: string;
  source_type: string;
  source_id: string;
  context_explanation: string;
  status: 'UNREAD' | 'READ' | 'DISMISSED' | string;
  created_at: string;
  action_payload?: {
    action_type: string;
    label: string;
  };
}

export interface UserInsightsResponse {
  total_insights: number;
  unread_count: number;
  insights: ProactiveInsightItem[];
}

export async function fetchProactiveInsights(
  filterType: string = 'ALL',
  workspaceId?: string,
  token?: string
): Promise<UserInsightsResponse> {
  const params = new URLSearchParams({ filter_type: filterType });
  if (workspaceId) params.append('workspace_id', workspaceId);

  const res = await fetch(`${API_BASE_URL}/proactive/insights?${params.toString()}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch proactive insights');
  return res.json();
}

export async function markInsightsRead(
  insightIds: string[],
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/proactive/insights/read`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ insight_ids: insightIds })
  });
  if (!res.ok) throw new Error('Failed to mark insights read');
  return res.json();
}

export async function dismissInsight(
  insightId: string,
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/proactive/insights/dismiss`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ insight_id: insightId })
  });
  if (!res.ok) throw new Error('Failed to dismiss insight');
  return res.json();
}

export async function updateNotificationPreferences(
  preferences: Record<string, boolean>,
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/proactive/preferences`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ preferences })
  });
  if (!res.ok) throw new Error('Failed to update notification preferences');
  return res.json();
}
