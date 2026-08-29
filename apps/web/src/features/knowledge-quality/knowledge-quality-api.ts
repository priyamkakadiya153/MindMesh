const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface QualityIssueItem {
  issue_id: string;
  type: string;
  severity: string;
  entity_id: string;
  entity_type: string;
  title: string;
  reason: string;
  evidence: string[];
  status: string;
  owner: string;
  created_at: string;
}

export interface KnowledgeHealthResponse {
  needs_attention_count: number;
  stale_count: number;
  duplicate_count: number;
  missing_owner_count: number;
  orphan_count: number;
  issues: QualityIssueItem[];
}

export async function fetchQualityIssues(
  typeFilter: string = 'ALL',
  token?: string
): Promise<QualityIssueItem[]> {
  const res = await fetch(`${API_BASE_URL}/quality/issues?type_filter=${typeFilter}`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch quality issues');
  return res.json();
}

export async function runQualityScan(
  projectId?: string,
  token?: string
): Promise<{ success: boolean; items_checked: number; issues_found: number }> {
  const res = await fetch(`${API_BASE_URL}/quality/scan`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ project_id: projectId })
  });
  if (!res.ok) throw new Error('Failed to run quality scan');
  return res.json();
}

export async function resolveQualityIssue(
  issueId: string,
  token?: string
): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE_URL}/quality/issues/${issueId}/resolve`, {
    method: 'POST',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to resolve issue');
  return res.json();
}

export async function assignOwner(
  entityId: string,
  ownerId: string,
  token?: string
): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE_URL}/quality/assign-owner`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ entity_id: entityId, owner_id: ownerId })
  });
  if (!res.ok) throw new Error('Failed to assign owner');
  return res.json();
}

export async function keepSeparate(
  issueId: string,
  token?: string
): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE_URL}/quality/keep-separate`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ issue_id: issueId })
  });
  if (!res.ok) throw new Error('Failed to keep separate');
  return res.json();
}

export async function fetchKnowledgeHealth(
  token?: string
): Promise<KnowledgeHealthResponse> {
  const res = await fetch(`${API_BASE_URL}/quality/health`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch knowledge health');
  return res.json();
}
