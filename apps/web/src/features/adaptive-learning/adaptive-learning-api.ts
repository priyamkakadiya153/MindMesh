const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface LearningReviewItem {
  id: string;
  event_type: string;
  scope: str;
  title: string;
  description: string;
  submitted_by: string;
  submitted_at: string;
  status: string;
}

export interface ReviewQueueResponse {
  organization_id: string;
  pending_items: LearningReviewItem[];
}

export interface DownstreamImpactResponse {
  knowledge_id: string;
  impact_graph: {
    nodes: Array<{ id: string; label: string; type: string }>;
    edges: Array<{ from: string; to: string; relation: string }>;
  };
  preview_summary: string;
}

export interface ShadowAutomationResponse {
  rule_name: string;
  mode: string;
  total_predictions: number;
  human_alignment_rate: string;
  predicted_actions_matched: number;
  predicted_actions_mismatched: number;
  status: string;
}

export interface AdaptiveDashboardResponse {
  organization_id: string;
  signal_quality_metrics: {
    total_learning_signals: number;
    validated_signals: number;
    rejected_signals: number;
    signal_accuracy: string;
  };
  drift_detection: {
    concept_drift_status: string;
    vocabulary_drift_status: string;
    detected_drift: string;
  };
  shadow_automations_count: number;
  active_experiments_count: number;
  learning_audit: Array<{
    timestamp: string;
    action: string;
    actor: string;
    details: string;
  }>;
}

export async function recordLearningEvent(
  eventType: string,
  scope: string,
  payload: Record<string, any>,
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/adaptive-learning/events`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ event_type: eventType, scope, payload })
  });
  if (!res.ok) throw new Error('Failed to record learning event');
  return res.json();
}

export async function fetchReviewQueue(token?: string): Promise<ReviewQueueResponse> {
  const res = await fetch(`${API_BASE_URL}/adaptive-learning/review-queue`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch review queue');
  return res.json();
}

export async function submitReviewAction(
  itemId: string,
  action: string,
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/adaptive-learning/review-action`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ item_id: itemId, action })
  });
  if (!res.ok) throw new Error('Review action failed');
  return res.json();
}

export async function revalidateDocument(documentId: string, token?: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/adaptive-learning/revalidate`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ document_id: documentId })
  });
  if (!res.ok) throw new Error('Revalidation failed');
  return res.json();
}

export async function fetchDownstreamImpact(knowledgeId: string, token?: string): Promise<DownstreamImpactResponse> {
  const res = await fetch(`${API_BASE_URL}/adaptive-learning/impact-preview?knowledge_id=${knowledgeId}`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch downstream impact');
  return res.json();
}

export async function fetchShadowAutomation(ruleName: string, token?: string): Promise<ShadowAutomationResponse> {
  const res = await fetch(`${API_BASE_URL}/adaptive-learning/shadow-automation?rule_name=${ruleName}`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch shadow automation');
  return res.json();
}

export async function promoteAutomationRule(ruleName: string, token?: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/adaptive-learning/promote-automation`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ rule_name: ruleName })
  });
  if (!res.ok) throw new Error('Automation promotion failed');
  return res.json();
}

export async function fetchAdaptiveDashboard(token?: string): Promise<AdaptiveDashboardResponse> {
  const res = await fetch(`${API_BASE_URL}/adaptive-learning/dashboard`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch adaptive dashboard');
  return res.json();
}
