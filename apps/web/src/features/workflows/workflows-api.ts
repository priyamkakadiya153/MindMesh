const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface WorkflowStepItem {
  id: string;
  step_index: number;
  action_type: string;
  title: string;
  description?: string;
  expected_result?: string;
  status: 'PENDING' | 'READY' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'SKIPPED' | 'BLOCKED' | string;
  result_summary?: Record<string, any>;
}

export interface WorkflowDetailsResponse {
  id: string;
  goal: string;
  workflow_type: string;
  status: 'DRAFT' | 'WAITING_FOR_APPROVAL' | 'RUNNING' | 'PAUSED' | 'COMPLETED' | 'FAILED' | 'CANCELLED' | string;
  completed_steps: number;
  total_steps: number;
  progress_pct: number;
  steps: WorkflowStepItem[];
}

export async function createWorkflowPlan(
  goal: string,
  projectId?: string,
  workspaceId?: string,
  token?: string
): Promise<WorkflowDetailsResponse> {
  const res = await fetch(`${API_BASE_URL}/workflows/plan`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ goal, project_id: projectId, workspace_id: workspaceId })
  });
  if (!res.ok) throw new Error('Failed to create workflow plan');
  return res.json();
}

export async function fetchWorkflowDetails(
  workflowId: string,
  token?: string
): Promise<WorkflowDetailsResponse> {
  const res = await fetch(`${API_BASE_URL}/workflows/${workflowId}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch workflow details');
  return res.json();
}

export async function approveWorkflow(
  workflowId: string,
  approvedStepIds?: string[],
  token?: string
): Promise<WorkflowDetailsResponse> {
  const res = await fetch(`${API_BASE_URL}/workflows/${workflowId}/approve`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ approved_step_ids: approvedStepIds })
  });
  if (!res.ok) throw new Error('Failed to approve workflow');
  return res.json();
}

export async function pauseWorkflow(
  workflowId: string,
  token?: string
): Promise<WorkflowDetailsResponse> {
  const res = await fetch(`${API_BASE_URL}/workflows/${workflowId}/pause`, {
    method: 'POST',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to pause workflow');
  return res.json();
}

export async function resumeWorkflow(
  workflowId: string,
  token?: string
): Promise<WorkflowDetailsResponse> {
  const res = await fetch(`${API_BASE_URL}/workflows/${workflowId}/resume`, {
    method: 'POST',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to resume workflow');
  return res.json();
}
