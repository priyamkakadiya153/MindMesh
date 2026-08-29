const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface PlanStep {
  step_number: number;
  action: string;
  description: string;
  risk: string;
  requires_approval: boolean;
  dependencies: number[];
}

export interface PlanResponse {
  plan_id: string;
  goal: string;
  project_id: string | null;
  autonomy_level: number;
  overall_risk: string;
  steps: PlanStep[];
  approval_required: boolean;
  status: string;
  message?: string;
}

export interface DryRunResponse {
  plan_id: string;
  mode: string;
  simulated_steps: number;
  state_changes: Array<Record<string, any>>;
  predicted_side_effects: string;
  status: string;
}

export interface ExecutionJournalResponse {
  organization_id: string;
  entries: Array<{
    execution_id: string;
    plan_id: string;
    intent: string;
    action: string;
    tool: string;
    actor: string;
    approved_by: string;
    status: string;
    timestamp: string;
  }>;
}

export async function parseIntentAndCreatePlan(
  rawUserPrompt: string,
  projectId?: string,
  token?: string
): Promise<PlanResponse> {
  const res = await fetch(`${API_BASE_URL}/autonomous-work/plans`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ raw_user_prompt: rawUserPrompt, project_id: projectId })
  });
  if (!res.ok) throw new Error('Plan generation failed');
  return res.json();
}

export async function executeDryRun(planId: string, token?: string): Promise<DryRunResponse> {
  const res = await fetch(`${API_BASE_URL}/autonomous-work/dry-run`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ plan_id: planId })
  });
  if (!res.ok) throw new Error('Dry run execution failed');
  return res.json();
}

export async function manageApprovalRequest(
  planId: string,
  action: string,
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/autonomous-work/approval-action`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ plan_id: planId, action })
  });
  if (!res.ok) throw new Error('Approval action failed');
  return res.json();
}

export async function executePlanStep(
  planId: string,
  stepNumber: number,
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/autonomous-work/execute-step`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ plan_id: planId, step_number: stepNumber })
  });
  if (!res.ok) throw new Error('Step execution failed');
  return res.json();
}

export async function emergencyStopAutonomy(scope: string, token?: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/autonomous-work/emergency-stop`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ scope })
  });
  if (!res.ok) throw new Error('Emergency stop failed');
  return res.json();
}

export async function fetchExecutionJournal(token?: string): Promise<ExecutionJournalResponse> {
  const res = await fetch(`${API_BASE_URL}/autonomous-work/execution-journal`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch execution journal');
  return res.json();
}
