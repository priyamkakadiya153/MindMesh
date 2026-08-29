const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface DecisionEvidenceItem {
  evidence_id: string;
  source_entity_id: string;
  source_entity_type: string;
  title: string;
  category: string;
  governance_status: string;
  content_snippet: string;
  attached_at: string;
}

export interface DecisionAlternativeItem {
  alternative_id: string;
  title: string;
  security_score: string;
  cost: string;
  complexity: string;
  timeline: string;
}

export interface GroundedRecommendationResponse {
  recommended_option_id: string;
  recommended_option_title: string;
  confidence: string;
  reasoning: string;
  supporting_evidence: string[];
  counter_evidence: string[];
  limitations: string[];
}

export interface FinalDecisionResponse {
  selected_option_id: string;
  selected_option_title: str;
  rationale: string;
  user_override_reason?: string;
  finalized_by: string;
  governance_status: string;
  published_version: string;
  finalized_at: string;
}

export interface DecisionWorkspaceResponse {
  workspace_id: string;
  question: string;
  project_id: string;
  scope: string;
  constraints: string[];
  readiness_state: string;
  evidence_list: DecisionEvidenceItem[];
  evidence_conflicts: Array<{ conflict_id: string; title: string; description: string }>;
  alternatives: DecisionAlternativeItem[];
  recommendation?: GroundedRecommendationResponse;
  final_decision?: FinalDecisionResponse;
  created_by: string;
  created_at: string;
}

export async function createDecisionWorkspace(
  question: string,
  projectId: string,
  scope?: string,
  constraints?: string[],
  token?: string
): Promise<DecisionWorkspaceResponse> {
  const res = await fetch(`${API_BASE_URL}/decision-intelligence/workspaces`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ question, project_id: projectId, scope, constraints })
  });
  if (!res.ok) throw new Error('Failed to create decision workspace');
  return res.json();
}

export async function fetchDecisionWorkspace(
  workspaceId: string,
  token?: string
): Promise<DecisionWorkspaceResponse> {
  const res = await fetch(`${API_BASE_URL}/decision-intelligence/workspaces/${workspaceId}`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch decision workspace');
  return res.json();
}

export async function addDecisionEvidence(
  workspaceId: string,
  sourceEntityId: string,
  sourceEntityType: string,
  title: string,
  category: string = 'CURRENT',
  governanceStatus: string = 'APPROVED',
  contentSnippet: string = '',
  token?: string
): Promise<{ success: boolean; message: string; workspace: DecisionWorkspaceResponse }> {
  const res = await fetch(`${API_BASE_URL}/decision-intelligence/workspaces/${workspaceId}/evidence`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({
      source_entity_id: sourceEntityId,
      source_entity_type: sourceEntityType,
      title,
      category,
      governance_status: governanceStatus,
      content_snippet: contentSnippet
    })
  });
  if (!res.ok) throw new Error('Failed to add evidence');
  return res.json();
}

export async function generateDecisionRecommendation(
  workspaceId: string,
  token?: string
): Promise<GroundedRecommendationResponse> {
  const res = await fetch(`${API_BASE_URL}/decision-intelligence/workspaces/${workspaceId}/recommendation`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to generate recommendation');
  return res.json();
}

export async function finalizeDecision(
  workspaceId: string,
  selectedOptionId: string,
  selectedOptionTitle: string,
  rationale: string,
  userOverrideReason?: string,
  token?: string
): Promise<{ success: boolean; message: string; workspace: DecisionWorkspaceResponse }> {
  const res = await fetch(`${API_BASE_URL}/decision-intelligence/workspaces/${workspaceId}/finalize`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({
      selected_option_id: selectedOptionId,
      selected_option_title: selectedOptionTitle,
      rationale,
      user_override_reason: userOverrideReason
    })
  });
  if (!res.ok) throw new Error('Failed to finalize decision');
  return res.json();
}

export async function createDecisionRetrospective(
  workspaceId: string,
  expectedOutcome: string,
  actualOutcome: string,
  outcomeStatus: string = 'SUCCESSFUL',
  lessonsLearned?: string[],
  token?: string
): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE_URL}/decision-intelligence/workspaces/${workspaceId}/retrospective`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({
      expected_outcome: expectedOutcome,
      actual_outcome: actualOutcome,
      outcome_status: outcomeStatus,
      lessons_learned: lessonsLearned
    })
  });
  if (!res.ok) throw new Error('Failed to create retrospective');
  return res.json();
}
