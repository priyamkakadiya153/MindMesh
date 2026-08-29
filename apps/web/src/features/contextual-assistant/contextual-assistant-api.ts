const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface AssistantSourceItem {
  entity_type: string;
  entity_id: string;
  name: string;
  status: string;
}

export interface AskAssistantResponse {
  question: string;
  context_entity_id?: string;
  context_entity_type?: string;
  answer: string;
  sources: AssistantSourceItem[];
  confidence_label: string;
  has_conflict?: boolean;
  conflict_summary?: string;
  suggested_followups: string[];
}

export interface CandidateActionItem {
  action_type: string;
  title: string;
}

export interface ResearchWorkspaceResponse {
  research_id: string;
  topic: string;
  summary: string;
  findings: string[];
  sources: Array<{ type: string; id: string; name: string }>;
  conflicts: string[];
  open_questions: string[];
  candidate_actions: CandidateActionItem[];
}

export interface ActionPreviewResponse {
  action_id: string;
  action_type: string;
  title: str;
  project_name: string;
  risk_level: string;
  expected_change: string;
  requires_user_approval: boolean;
  approval_status: string;
}

export async function askAssistant(
  question: string,
  contextEntityId?: string,
  contextEntityType?: string,
  projectId?: string,
  selectedSources?: string[],
  token?: string
): Promise<AskAssistantResponse> {
  const res = await fetch(`${API_BASE_URL}/assistant/ask`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({
      question,
      context_entity_id: contextEntityId,
      context_entity_type: contextEntityType,
      project_id: projectId,
      selected_sources: selectedSources
    })
  });
  if (!res.ok) throw new Error('Failed to ask assistant');
  return res.json();
}

export async function conductTopicResearch(
  topic: string,
  projectId?: string,
  token?: string
): Promise<ResearchWorkspaceResponse> {
  const res = await fetch(`${API_BASE_URL}/assistant/research`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ topic, project_id: projectId })
  });
  if (!res.ok) throw new Error('Failed to conduct research');
  return res.json();
}

export async function generateActionPreview(
  actionType: string,
  title: string,
  projectId?: string,
  token?: string
): Promise<ActionPreviewResponse> {
  const res = await fetch(`${API_BASE_URL}/assistant/action-preview`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ action_type: actionType, title, project_id: projectId })
  });
  if (!res.ok) throw new Error('Failed to generate action preview');
  return res.json();
}
