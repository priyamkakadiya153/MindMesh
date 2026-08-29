const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface KnowledgeHealthResponse {
  total_documents: number;
  potentially_stale_documents: number;
  verified_knowledge: number;
  conflicting_knowledge: number;
  needs_review: number;
  total_tasks: number;
}

export interface ProjectCoverageProfile {
  project_id: string;
  project_name: string;
  document_count: number;
  decision_count: number;
  task_count: number;
  coverage_status: 'STRONG' | 'ATTENTION_REQUIRED' | string;
}

export interface KnowledgeGapItem {
  id: string;
  gap_type: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH';
  title: string;
  summary: string;
  recommendation: string;
}

export interface ProjectHandoffBrief {
  project_id: string;
  project_name: string;
  description?: string;
  generated_at: string;
  generated_by: string;
  overview: string;
  key_decisions: Array<{ id: string; content: string }>;
  active_tasks: Array<{ id: string; title: string; status: string }>;
  reference_documents: Array<{ id: string; title: string; filename: string }>;
}

export async function fetchKnowledgeHealth(
  workspaceId?: string,
  token?: string
): Promise<KnowledgeHealthResponse> {
  const params = new URLSearchParams();
  if (workspaceId) params.append('workspace_id', workspaceId);

  const res = await fetch(`${API_BASE_URL}/operations/health?${params.toString()}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch knowledge health metrics');
  return res.json();
}

export async function fetchProjectCoverage(
  workspaceId?: string,
  token?: string
): Promise<ProjectCoverageProfile[]> {
  const params = new URLSearchParams();
  if (workspaceId) params.append('workspace_id', workspaceId);

  const res = await fetch(`${API_BASE_URL}/operations/coverage?${params.toString()}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch project coverage');
  return res.json();
}

export async function fetchKnowledgeGaps(
  workspaceId?: string,
  token?: string
): Promise<KnowledgeGapItem[]> {
  const params = new URLSearchParams();
  if (workspaceId) params.append('workspace_id', workspaceId);

  const res = await fetch(`${API_BASE_URL}/operations/gaps?${params.toString()}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch knowledge gaps');
  return res.json();
}

export async function generateProjectHandoff(
  projectId: string,
  token?: string
): Promise<ProjectHandoffBrief> {
  const res = await fetch(`${API_BASE_URL}/operations/projects/${projectId}/handoff`, {
    method: 'POST',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to generate project handoff brief');
  return res.json();
}
