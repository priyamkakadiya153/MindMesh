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
  insight_type: string;
  severity: string;
  title: string;
  summary: string;
  what_changed: string;
  why_it_matters: string;
  blast_radius: {
    direct_impact: string[];
    indirect_impact: string[];
  };
  evidence: string[];
  status: string;
  created_at: string;
}

export interface ProactiveDashboardResponse {
  insights: ProactiveInsightItem[];
  total_active: number;
  high_risk_count: number;
  medium_count: number;
  low_count: number;
  informational_count: number;
}

export interface DailyBriefResponse {
  brief_title: string;
  generated_at: string;
  sections: Array<{
    heading: string;
    items: string[];
  }>;
  provenance_label: string;
}

export interface InsightActionResponse {
  insight_id: string;
  action_type: string;
  status: string;
  message: string;
}

export interface ProactiveDigestResponse {
  total_signals_scanned: number;
  meaningful_insights_surfaced: number;
  alert_clusters_deduplicated: number;
  dismissed_false_positives: number;
  decisions_prepared_proactively: number;
}

export async function fetchProactiveDashboard(
  token?: string
): Promise<ProactiveDashboardResponse> {
  const res = await fetch(`${API_BASE_URL}/proactive-intelligence/dashboard`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch proactive dashboard');
  return res.json();
}

export async function fetchDailyBrief(
  token?: string
): Promise<DailyBriefResponse> {
  const res = await fetch(`${API_BASE_URL}/proactive-intelligence/brief`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch daily brief');
  return res.json();
}

export async function scanSystemSignals(
  projectId: string,
  token?: string
): Promise<ProactiveInsightItem[]> {
  const res = await fetch(`${API_BASE_URL}/proactive-intelligence/scan`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ project_id: projectId })
  });
  if (!res.ok) throw new Error('Failed to scan system signals');
  return res.json();
}

export async function handleInsightAction(
  insightId: string,
  actionType: string,
  token?: string
): Promise<InsightActionResponse> {
  const res = await fetch(`${API_BASE_URL}/proactive-intelligence/action`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ insight_id: insightId, action_type: actionType })
  });
  if (!res.ok) throw new Error('Failed to perform insight action');
  return res.json();
}

export async function dismissInsight(
  insightId: string,
  reason?: string,
  token?: string
): Promise<InsightActionResponse> {
  const res = await fetch(`${API_BASE_URL}/proactive-intelligence/dismiss`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ insight_id: insightId, reason })
  });
  if (!res.ok) throw new Error('Failed to dismiss insight');
  return res.json();
}

export async function fetchProactiveDigest(
  token?: string
): Promise<ProactiveDigestResponse> {
  const res = await fetch(`${API_BASE_URL}/proactive-intelligence/digest`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch proactive digest');
  return res.json();
}
