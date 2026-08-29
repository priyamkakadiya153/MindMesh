const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface ActionStep {
  action_id: string;
  step_index: number;
  tool_name: string;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | string;
  status: 'PROPOSED' | 'AWAITING_APPROVAL' | 'APPROVED' | 'RUNNING' | 'COMPLETED' | 'REJECTED' | 'FAILED' | string;
  description: string;
  target: string;
  reason: string;
  source_citation: string;
  completed_at?: string;
}

export interface ActionPlan {
  plan_id: string;
  goal: string;
  project_id: string;
  created_at: string;
  status: string;
  steps: ActionStep[];
}

export interface PendingApprovalItem {
  plan_id: string;
  goal: string;
  step: ActionStep;
}

export interface ActionLogItem {
  action_id: string;
  plan_id: string;
  tool_name: string;
  executor: string;
  status: string;
  timestamp: string;
}

export async function proposeActionPlan(
  goal: string,
  projectId?: string,
  token?: string
): Promise<ActionPlan> {
  const res = await fetch(`${API_BASE_URL}/agentic/propose-plan`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ goal, project_id: projectId })
  });
  if (!res.ok) throw new Error('Failed to propose action plan');
  return res.json();
}

export async function fetchPendingApprovals(
  token?: string
): Promise<PendingApprovalItem[]> {
  const res = await fetch(`${API_BASE_URL}/agentic/pending-approvals`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch pending approvals');
  return res.json();
}

export async function approveAction(
  planId: string,
  actionId: string,
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/agentic/approve-action`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ plan_id: planId, action_id: actionId })
  });
  if (!res.ok) throw new Error('Failed to approve action');
  return res.json();
}

export async function rejectAction(
  planId: string,
  actionId: string,
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/agentic/reject-action`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ plan_id: planId, action_id: actionId })
  });
  if (!res.ok) throw new Error('Failed to reject action');
  return res.json();
}

export async function fetchActionLog(
  token?: string
): Promise<ActionLogItem[]> {
  const res = await fetch(`${API_BASE_URL}/agentic/action-log`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch action log');
  return res.json();
}
