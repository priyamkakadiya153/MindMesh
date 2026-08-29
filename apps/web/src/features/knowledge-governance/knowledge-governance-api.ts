const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface GovernanceQueueItem {
  entity_id: string;
  entity_type: string;
  title: string;
  version: string;
  status: string;
  classification: string;
  trust_label: string;
  owner: string;
  reviewer: string;
  created_at: string;
}

export interface GovernanceAuditItem {
  audit_id: string;
  actor_id: string;
  action: string;
  entity_id: string;
  previous_state: string;
  new_state: string;
  details: string;
  timestamp: string;
}

export async function fetchGovernanceQueue(
  statusFilter: string = 'ALL',
  token?: string
): Promise<GovernanceQueueItem[]> {
  const res = await fetch(`${API_BASE_URL}/governance/queue?status_filter=${statusFilter}`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch governance queue');
  return res.json();
}

export async function submitForReview(
  entityId: string,
  entityType: string,
  reviewerId?: string,
  token?: string
): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE_URL}/governance/submit-review`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ entity_id: entityId, entity_type: entityType, reviewer_id: reviewerId })
  });
  if (!res.ok) throw new Error('Failed to submit for review');
  return res.json();
}

export async function approveVersion(
  entityId: string,
  version: str,
  token?: string
): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE_URL}/governance/approve`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ entity_id: entityId, version })
  });
  if (!res.ok) throw new Error('Failed to approve version');
  return res.json();
}

export async function rejectVersion(
  entityId: string,
  reason: string,
  token?: string
): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE_URL}/governance/reject`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ entity_id: entityId, reason })
  });
  if (!res.ok) throw new Error('Failed to reject version');
  return res.json();
}

export async function resolveConflict(
  conflictId: string,
  resolutionStrategy: string,
  currentEntityId: string,
  supersededEntityId: string,
  token?: string
): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE_URL}/governance/resolve-conflict`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({
      conflict_id: conflictId,
      resolution_strategy: resolutionStrategy,
      current_entity_id: currentEntityId,
      superseded_entity_id: supersededEntityId
    })
  });
  if (!res.ok) throw new Error('Failed to resolve conflict');
  return res.json();
}

export async function fetchGovernanceAuditLog(
  entityId?: string,
  token?: string
): Promise<GovernanceAuditItem[]> {
  const url = entityId ? `${API_BASE_URL}/governance/audit-log?entity_id=${entityId}` : `${API_BASE_URL}/governance/audit-log`;
  const res = await fetch(url, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch audit log');
  return res.json();
}
