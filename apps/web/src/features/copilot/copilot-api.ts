const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface CopilotCitation {
  id: string;
  entity_type: string;
  title: string;
  excerpt: string;
  project_name?: string;
  governance_status: string;
}

export interface CopilotAnswerResponse {
  question: string;
  intent: string;
  direct_answer: string;
  confidence_state: 'Well supported' | 'Supported' | 'Limited evidence' | 'Conflicting evidence' | 'Insufficient evidence' | string;
  key_points: string[];
  citations: CopilotCitation[];
  evidence_path: string[];
  conflict_warning?: string | null;
  suggested_action?: {
    action_type: string;
    title: string;
    reason: string;
  } | null;
  follow_ups: string[];
}

export interface ProjectBriefResponse {
  project_id: string;
  project_name: string;
  overview: string;
  current_state: string;
  key_decisions: string[];
  open_tasks: string[];
  blockers: string[];
  key_documents: string[];
  recent_changes: string[];
}

export async function askKnowledgeCopilot(
  question: string,
  workspaceId?: string,
  projectId?: string,
  token?: string
): Promise<CopilotAnswerResponse> {
  const res = await fetch(`${API_BASE_URL}/copilot/ask`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ question, workspace_id: workspaceId, project_id: projectId })
  });
  if (!res.ok) throw new Error('Failed to ask Knowledge Copilot');
  return res.json();
}

export async function fetchProjectBrief(
  projectId: string,
  token?: string
): Promise<ProjectBriefResponse> {
  const res = await fetch(`${API_BASE_URL}/copilot/project-brief`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ project_id: projectId })
  });
  if (!res.ok) throw new Error('Failed to generate project brief');
  return res.json();
}
