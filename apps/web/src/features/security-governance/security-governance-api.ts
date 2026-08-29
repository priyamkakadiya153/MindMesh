const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface AuthorizeResponse {
  authorized: boolean;
  reason: string;
  status_code: number;
}

export interface AIPolicyCheckResponse {
  provider: string;
  policy_status: string;
  original_items_count: number;
  sanitized_items_count: number;
  sanitized_context: any[];
  dm_privacy_enforced: boolean;
  provenance_label: string;
}

export interface RevokeMemberResponse {
  target_user_id: string;
  revocation_status: string;
  surfaces_invalidated: string[];
  timestamp: string;
}

export interface SecurityAuditItem {
  event_id: string;
  event_type: string;
  actor: string;
  scope: string;
  timestamp: string;
  details: string;
}

export interface SecurityStatusResponse {
  organization_isolation: string;
  workspace_isolation: string;
  dm_privacy: string;
  ai_data_boundary: string;
  secret_scanning: string;
  revoked_users_count: number;
  audit_events_count: number;
}

export async function checkAuthorization(
  targetOrgId: string,
  targetWorkspaceId: string,
  requiredPermission: string,
  resourceId?: string,
  token?: string
): Promise<AuthorizeResponse> {
  const res = await fetch(`${API_BASE_URL}/security-governance/authorize`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({
      target_org_id: targetOrgId,
      target_workspace_id: targetWorkspaceId,
      required_permission: requiredPermission,
      resource_id: resourceId
    })
  });
  if (!res.ok) {
    const err = await res.json();
    return { authorized: false, reason: err.detail || 'Authorization failed', status_code: res.status };
  }
  return res.json();
}

export async function checkAIPolicy(
  providerName: string,
  contextItems: any[],
  token?: string
): Promise<AIPolicyCheckResponse> {
  const res = await fetch(`${API_BASE_URL}/security-governance/ai-policy-check`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ provider_name: providerName, context_items: contextItems })
  });
  if (!res.ok) throw new Error('Failed to evaluate AI policy');
  return res.json();
}

export async function revokeMemberAccess(
  targetUserId: string,
  workspaceId: string,
  token?: string
): Promise<RevokeMemberResponse> {
  const res = await fetch(`${API_BASE_URL}/security-governance/revoke-member`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ target_user_id: targetUserId, workspace_id: workspaceId })
  });
  if (!res.ok) throw new Error('Failed to revoke member access');
  return res.json();
}

export async function scanSecrets(
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/security-governance/scan-secrets`, {
    method: 'POST',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to scan secrets');
  return res.json();
}

export async function fetchSecurityAuditTimeline(
  token?: string
): Promise<SecurityAuditItem[]> {
  const res = await fetch(`${API_BASE_URL}/security-governance/security-audit`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch security audit timeline');
  return res.json();
}

export async function fetchSecurityStatus(
  token?: string
): Promise<SecurityStatusResponse> {
  const res = await fetch(`${API_BASE_URL}/security-governance/security-status`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch security status');
  return res.json();
}
