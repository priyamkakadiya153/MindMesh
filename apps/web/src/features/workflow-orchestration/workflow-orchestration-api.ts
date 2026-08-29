const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface WorkflowStep {
  step_id: string;
  name: string;
  status: string;
  depends_on: string[];
}

export interface WorkflowItem {
  workflow_id: string;
  project_id?: string;
  goal: string;
  status: string;
  steps?: WorkflowStep[];
  steps_count?: number;
  completed_steps?: number;
  created_by?: string;
  created_at?: string;
  approved_by?: string;
}

export interface WorkflowCenterResponse {
  workflows: WorkflowItem[];
  awaiting_approval_count: number;
  running_count: number;
  completed_count: number;
}

export interface StepExecutionResponse {
  workflow_id: string;
  step_id: string;
  idempotency_key: string;
  execution_status: string;
  observed_vs_expected: {
    expected_state: string;
    observed_state: string;
    verification_passed: boolean;
  };
  executed_at: string;
}

export interface RetryResponse {
  workflow_id: string;
  step_id: string;
  retry_count: number;
  circuit_breaker_tripped: boolean;
  status: string;
  message: string;
}

export interface PostmortemResponse {
  workflow_id: string;
  postmortem_title: string;
  what_worked: string[];
  what_failed: string[];
  process_improvement_candidate: {
    title: string;
    recommendation: string;
  };
  generated_at: string;
}

export interface WorkflowDigestResponse {
  total_workflows_executed: number;
  idempotent_actions_verified: number;
  human_approval_gates_passed: number;
  circuit_breakers_tripped: number;
  process_improvements_suggested: number;
}

export async function fetchWorkflowCenter(
  token?: string
): Promise<WorkflowCenterResponse> {
  const res = await fetch(`${API_BASE_URL}/workflow-orchestration/center`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch workflow center');
  return res.json();
}

export async function createWorkflowPlan(
  projectId: string,
  goal: string,
  token?: string
): Promise<WorkflowItem> {
  const res = await fetch(`${API_BASE_URL}/workflow-orchestration/create-plan`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ project_id: projectId, goal })
  });
  if (!res.ok) throw new Error('Failed to create workflow plan');
  return res.json();
}

export async function approveWorkflow(
  workflowId: string,
  token?: string
): Promise<{ success: boolean; message: string; workflow: WorkflowItem }> {
  const res = await fetch(`${API_BASE_URL}/workflow-orchestration/approve`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ workflow_id: workflowId })
  });
  if (!res.ok) throw new Error('Failed to approve workflow');
  return res.json();
}

export async function executeWorkflowStep(
  workflowId: string,
  stepId: str,
  token?: string
): Promise<StepExecutionResponse> {
  const res = await fetch(`${API_BASE_URL}/workflow-orchestration/execute-step`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ workflow_id: workflowId, step_id: stepId })
  });
  if (!res.ok) throw new Error('Failed to execute workflow step');
  return res.json();
}

export async function retryWorkflowStep(
  workflowId: string,
  stepId: string,
  token?: string
): Promise<RetryResponse> {
  const res = await fetch(`${API_BASE_URL}/workflow-orchestration/retry`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ workflow_id: workflowId, step_id: stepId })
  });
  if (!res.ok) throw new Error('Failed to retry step');
  return res.json();
}

export async function generateWorkflowPostmortem(
  workflowId: string,
  token?: string
): Promise<PostmortemResponse> {
  const res = await fetch(`${API_BASE_URL}/workflow-orchestration/postmortem`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ workflow_id: workflowId })
  });
  if (!res.ok) throw new Error('Failed to generate postmortem');
  return res.json();
}

export async function fetchWorkflowDigest(
  token?: string
): Promise<WorkflowDigestResponse> {
  const res = await fetch(`${API_BASE_URL}/workflow-orchestration/digest`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch workflow digest');
  return res.json();
}
