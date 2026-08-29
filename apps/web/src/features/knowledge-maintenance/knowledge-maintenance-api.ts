const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface ReviewQueueItem {
  queue_item_id: string;
  entity_id: string;
  title: string;
  issue_type: string;
  priority: string;
  reason: string;
  active_dependencies_count: number;
  status: string;
  created_at: string;
}

export interface CanonicalCandidateItem {
  candidate_id: string;
  project_id: string;
  concept: string;
  recommended_canonical_doc: string;
  overlapping_docs: string[];
  recommendation_reason: string;
  status: string;
}

export interface MergePreviewResponse {
  source_a_title: string;
  source_b_title: string;
  overlapping_content: string;
  differences: string[];
  proposed_result: string;
  governance_requirement: string;
}

export interface ContextSearchResponse {
  query: string;
  resolved_scope: string;
  answer: string;
  context_ambiguity: boolean;
  confidence: string;
}

export interface MaintenanceDigestResponse {
  total_review_items: number;
  high_impact_stale_count: number;
  canonical_candidates_count: number;
  self_healed_indices_count: number;
}

export async function fetchKnowledgeReviewQueue(
  token?: string
): Promise<ReviewQueueItem[]> {
  const res = await fetch(`${API_BASE_URL}/knowledge-maintenance/review-queue`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch review queue');
  return res.json();
}

export async function scanCanonicalCandidates(
  projectId: string,
  token?: string
): Promise<CanonicalCandidateItem[]> {
  const res = await fetch(`${API_BASE_URL}/knowledge-maintenance/canonical-candidates?project_id=${encodeURIComponent(projectId)}`, {
    method: 'POST',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to scan canonical candidates');
  return res.json();
}

export async function generateMergePreview(
  sourceAId: string,
  sourceBId: string,
  token?: string
): Promise<MergePreviewResponse> {
  const res = await fetch(`${API_BASE_URL}/knowledge-maintenance/merge-preview`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ source_a_id: sourceAId, source_b_id: sourceBId })
  });
  if (!res.ok) throw new Error('Failed to generate merge preview');
  return res.json();
}

export async function revalidateKnowledge(
  entityId: string,
  revalidationState: string = 'STILL_VALID',
  token?: string
): Promise<{ success: boolean; message: string; entity_id: string }> {
  const res = await fetch(`${API_BASE_URL}/knowledge-maintenance/revalidate`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ entity_id: entityId, revalidation_state: revalidationState })
  });
  if (!res.ok) throw new Error('Failed to revalidate knowledge');
  return res.json();
}

export async function triggerSelfHealIndex(
  token?: string
): Promise<{ success: boolean; message: string; repaired_chunks: number; repaired_embeddings: number }> {
  const res = await fetch(`${API_BASE_URL}/knowledge-maintenance/self-heal-index`, {
    method: 'POST',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to self heal index');
  return res.json();
}

export async function performContextSearch(
  query: string,
  scopeContext: string = 'PROJECT_A',
  token?: string
): Promise<ContextSearchResponse> {
  const res = await fetch(`${API_BASE_URL}/knowledge-maintenance/context-search`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ query, scope_context: scopeContext })
  });
  if (!res.ok) throw new Error('Failed context search');
  return res.json();
}

export async function fetchMaintenanceDigest(
  token?: string
): Promise<MaintenanceDigestResponse> {
  const res = await fetch(`${API_BASE_URL}/knowledge-maintenance/digest`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch maintenance digest');
  return res.json();
}
