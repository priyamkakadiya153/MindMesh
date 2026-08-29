const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface FeedbackEvent {
  event_id: string;
  entity_id: string;
  entity_type: string;
  feedback_type: string;
  rating: string;
  reason: string;
  user_id: string;
  submitted_at: string;
}

export interface CorrectionProposal {
  correction_id: string;
  source_entity_id: str;
  proposed_content: string;
  reason: string;
  proposed_by: string;
  status: string;
  created_at: string;
}

export interface KnowledgeGapItem {
  gap_id: string;
  query: string;
  occurrences: number;
  project_context: string;
  priority: string;
  recommended_action: string;
}

export interface QuestionClusterItem {
  cluster_id: string;
  topic: string;
  question_count: number;
  sample_questions: string[];
  matched_decision: string;
}

export interface PlaybookItem {
  playbook_id: string;
  title: string;
  version: string;
  owner: string;
  steps: string[];
  governance_status: string;
  created_at: string;
}

export interface LearningAnalyticsResponse {
  total_feedback_events: number;
  helpful_rate: string;
  correction_proposals_count: number;
  approved_corrections_count: number;
  active_knowledge_gaps: number;
  governed_playbooks_count: number;
}

export async function submitFeedback(
  entityId: string,
  entityType: string,
  feedbackType: string,
  rating: string,
  reason?: string,
  token?: string
): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE_URL}/learning-feedback/feedback`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({
      entity_id: entityId,
      entity_type: entityType,
      feedback_type: feedbackType,
      rating,
      reason
    })
  });
  if (!res.ok) throw new Error('Failed to submit feedback');
  return res.json();
}

export async function proposeCorrection(
  sourceEntityId: string,
  proposedContent: string,
  reason: string,
  token?: string
): Promise<{ success: boolean; message: string; correction: CorrectionProposal }> {
  const res = await fetch(`${API_BASE_URL}/learning-feedback/corrections`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({
      source_entity_id: sourceEntityId,
      proposed_content: proposedContent,
      reason
    })
  });
  if (!res.ok) throw new Error('Failed to propose correction');
  return res.json();
}

export async function approveCorrection(
  correctionId: string,
  token?: string
): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE_URL}/learning-feedback/corrections/${correctionId}/approve`, {
    method: 'POST',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to approve correction');
  return res.json();
}

export async function fetchKnowledgeGaps(
  token?: string
): Promise<KnowledgeGapItem[]> {
  const res = await fetch(`${API_BASE_URL}/learning-feedback/knowledge-gaps`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch knowledge gaps');
  return res.json();
}

export async function fetchQuestionClusters(
  token?: string
): Promise<QuestionClusterItem[]> {
  const res = await fetch(`${API_BASE_URL}/learning-feedback/question-clusters`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch question clusters');
  return res.json();
}

export async function fetchPlaybooks(
  token?: string
): Promise<PlaybookItem[]> {
  const res = await fetch(`${API_BASE_URL}/learning-feedback/playbooks`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch playbooks');
  return res.json();
}

export async function createPlaybook(
  title: string,
  steps: string[],
  token?: string
): Promise<{ success: boolean; message: string; playbook: PlaybookItem }> {
  const res = await fetch(`${API_BASE_URL}/learning-feedback/create-playbook`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ title, steps })
  });
  if (!res.ok) throw new Error('Failed to create playbook');
  return res.json();
}

export async function fetchLearningAnalytics(
  token?: string
): Promise<LearningAnalyticsResponse> {
  const res = await fetch(`${API_BASE_URL}/learning-feedback/analytics`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch analytics');
  return res.json();
}
