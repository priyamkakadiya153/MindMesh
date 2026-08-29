const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface ActionPlanResponse {
  plan_id: string;
  decision_id: string;
  project_id: string;
  objective: string;
  expected_outcome: string;
  success_criteria: string[];
  status: string;
  owner_id: string;
  created_at: string;
}

export interface SuggestedTaskItem {
  task_id: string;
  plan_id: string;
  title: string;
  description: string;
  status: string;
  source: string;
  suggested_at: string;
}

export interface DetectedBlockerItem {
  blocker_id: string;
  title: string;
  blocked_task_id: string;
  blocked_task_title: string;
  classification: string;
  explanation: string;
  resolution_recommendation: string;
}

export interface CriticalPathResponse {
  project_id: string;
  execution_health: string;
  health_explanation: string;
  critical_path_tasks: Array<{ step: number; title: string; status: string; is_blocker: boolean }>;
}

export interface ClosedLoopOutcomeResponse {
  outcome_id: string;
  plan_id: string;
  expected_outcome: string;
  actual_outcome: string;
  discrepancy_status: string;
  lesson_candidate: string;
  recorded_by: string;
  recorded_at: string;
}

export interface PendingActionItem {
  action_id: string;
  action_type: string;
  title: string;
  source_decision: string;
  status: string;
  confirmation_level: string;
  reason: string;
}

export async function createActionPlan(
  decisionId: string,
  projectId: string,
  objective: str,
  expectedOutcome: string,
  successCriteria?: string[],
  token?: string
): Promise<ActionPlanResponse> {
  const res = await fetch(`${API_BASE_URL}/execution-intelligence/action-plans`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({
      decision_id: decisionId,
      project_id: projectId,
      objective,
      expected_outcome: expectedOutcome,
      success_criteria: successCriteria
    })
  });
  if (!res.ok) throw new Error('Failed to create action plan');
  return res.json();
}

export async function fetchActionPlan(
  planId: string,
  token?: string
): Promise<ActionPlanResponse> {
  const res = await fetch(`${API_BASE_URL}/execution-intelligence/action-plans/${planId}`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch action plan');
  return res.json();
}

export async function suggestActionPlanTasks(
  planId: string,
  token?: string
): Promise<SuggestedTaskItem[]> {
  const res = await fetch(`${API_BASE_URL}/execution-intelligence/action-plans/${planId}/tasks/suggest`, {
    method: 'POST',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to suggest tasks');
  return res.json();
}

export async function confirmSuggestedTask(
  planId: string,
  suggestedTaskId: string,
  token?: string
): Promise<{ success: boolean; message: string; task: SuggestedTaskItem }> {
  const res = await fetch(`${API_BASE_URL}/execution-intelligence/action-plans/${planId}/tasks/confirm?suggested_task_id=${encodeURIComponent(suggestedTaskId)}`, {
    method: 'POST',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to confirm task');
  return res.json();
}

export async function fetchDetectedBlockers(
  projectId: string,
  token?: string
): Promise<DetectedBlockerItem[]> {
  const res = await fetch(`${API_BASE_URL}/execution-intelligence/blockers?project_id=${encodeURIComponent(projectId)}`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch blockers');
  return res.json();
}

export async function fetchCriticalPath(
  projectId: string,
  token?: string
): Promise<CriticalPathResponse> {
  const res = await fetch(`${API_BASE_URL}/execution-intelligence/critical-path?project_id=${encodeURIComponent(projectId)}`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch critical path');
  return res.json();
}

export async function recordClosedLoopOutcome(
  planId: string,
  expectedOutcome: string,
  actualOutcome: string,
  token?: string
): Promise<{ success: boolean; message: string; outcome_record: ClosedLoopOutcomeResponse }> {
  const res = await fetch(`${API_BASE_URL}/execution-intelligence/closed-loop/outcomes?plan_id=${encodeURIComponent(planId)}`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({
      expected_outcome: expectedOutcome,
      actual_outcome: actualOutcome
    })
  });
  if (!res.ok) throw new Error('Failed to record closed-loop outcome');
  return res.json();
}

export async function fetchPendingActions(
  projectId: string,
  token?: string
): Promise<PendingActionItem[]> {
  const res = await fetch(`${API_BASE_URL}/execution-intelligence/pending-actions?project_id=${encodeURIComponent(projectId)}`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch pending actions');
  return res.json();
}
