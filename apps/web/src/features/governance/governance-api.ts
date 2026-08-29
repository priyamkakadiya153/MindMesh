const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface ReviewQueueItem {
  id: string;
  entity_type: string;
  entity_id: string;
  title: string;
  summary: string;
  reason: string;
  priority: 'LOW' | 'NORMAL' | 'HIGH';
  verification_state: string;
  lifecycle_state: string;
}

export interface AuditLogItem {
  id: string;
  action: string;
  entity_type: string;
  entity_id: string;
  previous_state?: string;
  new_state: string;
  user_id: string;
  details?: string;
  created_at: string;
}

export async function fetchReviewQueue(
  workspaceId?: string,
  token?: string
): Promise<ReviewQueueItem[]> {
  const params = new URLSearchParams();
  if (workspaceId) params.append('workspace_id', workspaceId);

  const res = await fetch(`${API_BASE_URL}/governance/review-queue?${params.toString()}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch review queue');
  return res.json();
}

export async function verifyKnowledge(
  entityType: string,
  entityId: string,
  token?: string
): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/governance/verify`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ entity_type: entityType, entity_id: entityId })
  });
  if (!res.ok) throw new Error('Failed to verify knowledge item');
}

export async function supersedeKnowledge(
  oldEntityType: string,
  oldEntityId: string,
  newEntityId: string,
  token?: string
): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/governance/supersede`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ old_entity_type: oldEntityType, old_entity_id: oldEntityId, new_entity_id: newEntityId })
  });
  if (!res.ok) throw new Error('Failed to mark knowledge superseded');
}

export async function archiveKnowledge(
  entityType: string,
  entityId: string,
  token?: string
): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/governance/archive`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ entity_type: entityType, entity_id: entityId })
  });
  if (!res.ok) throw new Error('Failed to archive knowledge item');
}

export async function restoreKnowledge(
  entityType: string,
  entityId: string,
  token?: string
): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/governance/restore`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ entity_type: entityType, entity_id: entityId })
  });
  if (!res.ok) throw new Error('Failed to restore knowledge item');
}

export async function fetchGovernanceAuditTrail(
  token?: string
): Promise<AuditLogItem[]> {
  const res = await fetch(`${API_BASE_URL}/governance/audit-trail`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch governance audit trail');
  return res.json();
}
