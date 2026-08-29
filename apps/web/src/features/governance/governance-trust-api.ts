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
  organization_id: string;
  workspace_id: string;
  project_id: string;
  entity_type: string;
  entity_id: string;
  title: string;
  description: string;
  source_type: string;
  source_id: string;
  status: string;
  reason: string;
  created_at: string;
}

export interface ConflictItem {
  id: string;
  organization_id: string;
  workspace_id: string;
  project_id: string;
  topic: string;
  severity: string;
  source_a: { id: string; title: string; content: string };
  source_b: { id: string; title: str; content: string };
  status: string;
  created_at: string;
}

export interface GovernanceReviewQueueResponse {
  total_review_items: number;
  total_conflicts: number;
  review_queue: ReviewQueueItem[];
  active_conflicts: ConflictItem[];
}

export interface AuditLogItem {
  id: string;
  organization_id: string;
  performed_by: string;
  user_id: string;
  action: string;
  entity_type: string;
  entity_id: string;
  old_state: string;
  new_state: string;
  reason: string;
  timestamp: string;
}

export async function fetchGovernanceReviewQueue(
  workspaceId?: string,
  projectId?: string,
  token?: string
): Promise<GovernanceReviewQueueResponse> {
  const params = new URLSearchParams();
  if (workspaceId) params.append('workspace_id', workspaceId);
  if (projectId) params.append('project_id', projectId);

  const res = await fetch(`${API_BASE_URL}/governance/trust/review-queue?${params.toString()}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch governance review queue');
  return res.json();
}

export async function confirmExtraction(
  reviewItemId: string,
  editedTitle?: string,
  editedDescription?: string,
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/governance/trust/confirm`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({
      review_item_id: reviewItemId,
      edited_title: editedTitle,
      edited_description: editedDescription
    })
  });
  if (!res.ok) throw new Error('Failed to confirm extraction');
  return res.json();
}

export async function rejectExtraction(
  reviewItemId: string,
  reason?: string,
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/governance/trust/reject`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({
      review_item_id: reviewItemId,
      reason
    })
  });
  if (!res.ok) throw new Error('Failed to reject extraction');
  return res.json();
}

export async function resolveConflict(
  conflictId: string,
  winningSourceId: string,
  resolutionNotes?: string,
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/governance/trust/resolve-conflict`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({
      conflict_id: conflictId,
      winning_source_id: winningSourceId,
      resolution_notes: resolutionNotes
    })
  });
  if (!res.ok) throw new Error('Failed to resolve conflict');
  return res.json();
}

export async function setSourceOfTruth(
  projectId: string,
  entityId: string,
  entityTitle: str,
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/governance/trust/set-source-of-truth`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({
      project_id: projectId,
      entity_id: entityId,
      entity_title: entityTitle
    })
  });
  if (!res.ok) throw new Error('Failed to set source of truth');
  return res.json();
}

export async function fetchGovernanceAuditLog(
  token?: string
): Promise<AuditLogItem[]> {
  const res = await fetch(`${API_BASE_URL}/governance/trust/audit-log`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch governance audit log');
  return res.json();
}
