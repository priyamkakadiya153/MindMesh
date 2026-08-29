const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface ProvenanceResponse {
  entity_id: string;
  origin: {
    source_type: string;
    source_name: string;
    creator: string;
    version: number;
    created_at: string;
  };
  authority: {
    level: string;
    owner: string;
    steward: string;
  };
  verification: {
    status: string;
    verified_by: string;
    verified_at: string;
    reason?: string;
  };
  ai_provenance: {
    tag: string;
    model_provider: string;
    human_confirmation: boolean;
  };
  lineage: Array<{ step: number; type: string; label: string }>;
  provenance_label: string;
}

export interface ConflictItem {
  conflict_id: string;
  claim_a: string;
  source_a: string;
  claim_b: string;
  source_b: string;
  scope: string;
  status: string;
  detected_at: string;
  resolution?: string;
  resolved_by?: string;
}

export interface ReviewQueueResponse {
  total_review_items: number;
  needs_verification: Array<{ id: string; title: string; source: string; priority: string }>;
  potentially_outdated: Array<{ id: string; title: string; reason: string; priority: string }>;
  conflicting: Array<{ id: string; title: string; priority: string }>;
  ai_generated: Array<{ id: string; title: string; priority: string }>;
}

export interface AuditLogEntry {
  audit_id: string;
  action: string;
  actor: string;
  target: string;
  timestamp: string;
  rationale: string;
}

export async function fetchProvenanceDetail(
  entityId: string,
  token?: string
): Promise<ProvenanceResponse> {
  const res = await fetch(`${API_BASE_URL}/trust-quality/provenance/${entityId}`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch provenance detail');
  return res.json();
}

export async function updateVerificationState(
  entityId: string,
  verificationStatus: string,
  reason: string,
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/trust-quality/verify`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ entity_id: entityId, verification_status: verificationStatus, reason })
  });
  if (!res.ok) throw new Error('Failed to update verification state');
  return res.json();
}

export async function fetchConflicts(
  token?: string
): Promise<ConflictItem[]> {
  const res = await fetch(`${API_BASE_URL}/trust-quality/conflicts`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch conflicts');
  return res.json();
}

export async function resolveConflict(
  conflictId: string,
  resolutionStrategy: string,
  reason: string,
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/trust-quality/resolve-conflict`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ conflict_id: conflictId, resolution_strategy: resolutionStrategy, reason })
  });
  if (!res.ok) throw new Error('Failed to resolve conflict');
  return res.json();
}

export async function confirmAISuggestion(
  entityId: string,
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/trust-quality/confirm-ai`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ entity_id: entityId })
  });
  if (!res.ok) throw new Error('Failed to confirm AI suggestion');
  return res.json();
}

export async function fetchReviewQueue(
  token?: string
): Promise<ReviewQueueResponse> {
  const res = await fetch(`${API_BASE_URL}/trust-quality/review-queue`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch review queue');
  return res.json();
}

export async function revalidateAIResult(
  entityId: string,
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/trust-quality/revalidate`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ entity_id: entityId })
  });
  if (!res.ok) throw new Error('Failed to revalidate AI result');
  return res.json();
}

export async function fetchQualityAuditLog(
  token?: string
): Promise<AuditLogEntry[]> {
  const res = await fetch(`${API_BASE_URL}/trust-quality/audit-log`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch quality audit log');
  return res.json();
}
