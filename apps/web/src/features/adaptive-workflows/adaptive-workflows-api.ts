const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface WorkObjectiveResponse {
  objective_id: string;
  goal: string;
  scope: string;
  priority: string;
  constraints: string[];
  deadline: string;
  owner: string;
  participants: string[];
  expected_outcome: string;
  risk_assessment: string;
  organization_id: string;
  project_id: string | null;
  created_at: string;
}

export interface WorkPlanStep {
  step_id: string;
  name: string;
  step_type: string;
  side_effect: string;
  owner: string;
  state: string;
  dependencies: string[];
  requires_approval: boolean;
}

export interface WorkPlanResponse {
  plan_id: string;
  objective_id: string;
  user_intent: string;
  version: number;
  status: string;
  confidence_score: number;
  plan_sources: Array<{
    source_type: string;
    name: string;
  }>;
  steps: WorkPlanStep[];
  critical_path: string[];
  autonomy_level: string;
}

export interface PlanPreviewResponse {
  plan_id: string;
  is_valid: boolean;
  validation_checks: Array<{
    check: string;
    passed: boolean;
  }>;
  preview_summary: {
    total_steps: number;
    human_steps: number;
    tool_steps: number;
    approval_gates: number;
    estimated_duration_minutes: number;
    potential_risks: string[];
  };
}

export interface StepExecutionResponse {
  plan_id: string;
  step_id: string;
  action_performed: string;
  step_state: string;
  plan_status: string;
  executed_by: string;
  timestamp: string;
  execution_trace: {
    actor_type: string;
    inputs_used: string[];
    outputs_generated: string[];
    confidence: number;
  };
}

export interface ExceptionResponse {
  exception_id: string;
  plan_id: string;
  step_id: string;
  severity: string;
  error_message: string;
  evidence: string[];
  suggested_recovery: string;
  compensating_action_required: boolean;
  recovery_options: Array<{
    action: string;
    description: string;
  }>;
}

export interface DryRunResponse {
  plan_id: string;
  mode: string;
  simulated_actions: Array<{
    step_id: string;
    action: string;
    effect: string;
  }>;
  resources_affected: string[];
  potential_errors: string[];
  production_mutation_occurred: boolean;
}

export interface PlanEvaluationResponse {
  plan_id: string;
  planned_duration_minutes: number;
  actual_duration_minutes: number;
  deviations_detected: Array<{
    type: string;
    step_id: string;
    reason: string;
  }>;
  objective_achieved: string;
  outcome_evidence: string;
  candidate_lesson: string;
}

export async function createWorkObjective(
  goal: string,
  scope: string,
  priority: string = 'HIGH',
  deadline?: string,
  projectId?: string,
  token?: string
): Promise<WorkObjectiveResponse> {
  const res = await fetch(`${API_BASE_URL}/adaptive-workflows/objectives`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ goal, scope, priority, deadline, project_id: projectId })
  });
  if (!res.ok) throw new Error('Failed to create work objective');
  return res.json();
}

export async function generateWorkPlan(
  objectiveId: string,
  userIntent: string,
  projectId?: string,
  token?: string
): Promise<WorkPlanResponse> {
  const res = await fetch(`${API_BASE_URL}/adaptive-workflows/plans/generate`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ objective_id: objectiveId, user_intent: userIntent, project_id: projectId })
  });
  if (!res.ok) throw new Error('Failed to generate work plan');
  return res.json();
}

export async function previewPlan(
  planId: string,
  token?: string
): Promise<PlanPreviewResponse> {
  const res = await fetch(`${API_BASE_URL}/adaptive-workflows/plans/preview`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ plan_id: planId })
  });
  if (!res.ok) throw new Error('Failed to preview plan');
  return res.json();
}

export async function executeWorkflowStep(
  planId: string,
  stepId: str,
  action: string = 'START',
  token?: string
): Promise<StepExecutionResponse> {
  const res = await fetch(`${API_BASE_URL}/adaptive-workflows/execute-step`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ plan_id: planId, step_id: stepId, action })
  });
  if (!res.ok) throw new Error('Failed to execute workflow step');
  return res.json();
}

export async function handleWorkflowException(
  planId: string,
  stepId: string,
  errorMessage: string,
  token?: string
): Promise<ExceptionResponse> {
  const res = await fetch(`${API_BASE_URL}/adaptive-workflows/exceptions/handle`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ plan_id: planId, step_id: stepId, error_message: errorMessage })
  });
  if (!res.ok) throw new Error('Failed to handle workflow exception');
  return res.json();
}

export async function dryRunWorkflow(
  planId: string,
  token?: string
): Promise<DryRunResponse> {
  const res = await fetch(`${API_BASE_URL}/adaptive-workflows/dry-run`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ plan_id: planId })
  });
  if (!res.ok) throw new Error('Failed to run dry-run simulation');
  return res.json();
}

export async function evaluatePlanVsActual(
  planId: string,
  token?: string
): Promise<PlanEvaluationResponse> {
  const res = await fetch(`${API_BASE_URL}/adaptive-workflows/evaluate`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ plan_id: planId })
  });
  if (!res.ok) throw new Error('Failed to evaluate plan vs actual');
  return res.json();
}
