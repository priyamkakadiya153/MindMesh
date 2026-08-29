const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface AgentDefinition {
  agent_id: string;
  name: string;
  role: string;
  capabilities: string[];
  allowed_tools: string[];
  data_scope: string;
  risk_level: string;
  autonomy_level: string;
  budget_max_tokens: number;
  status: string;
}

export interface TaskDecompositionResponse {
  decomposition_id: string;
  user_intent: string;
  subtasks: Array<{
    subtask_id: string;
    goal: string;
    required_capability: string;
    dependencies: string[];
    assigned_agent_id: string;
  }>;
  circular_delegation_detected: boolean;
  max_delegation_depth: number;
}

export interface RouteResponse {
  decomposition_id: string;
  routes: Array<{
    subtask_id: string;
    selected_agent: string;
    reason: string;
    confidence: number;
    fallback_agent: string;
  }>;
  budget_allocated: {
    max_tokens: number;
    max_execution_sec: number;
  };
}

export interface SubtaskExecutionResponse {
  trace_id: string;
  subtask_id: string;
  agent_id: string;
  status: string;
  execution_time_ms: number;
  tokens_consumed: number;
  output: {
    summary: string;
    findings: string[];
    side_effect: string;
  };
  evidence_sources: string[];
  confidence: number;
}

export interface SynthesisResponse {
  synthesis_id: string;
  verification_status: string;
  conflicts_detected: Array<{
    conflict_id: string;
    agent_a: string;
    agent_b: string;
    claim_a: string;
    claim_b: string;
    resolution: string;
    status: string;
  }>;
  synthesized_brief: {
    title: string;
    recommended_choice: string;
    evidence_provenance: string[];
    uncertainty_level: string;
    requires_human_approval: boolean;
  };
}

export async function fetchSpecialistAgents(
  token?: string
): Promise<AgentDefinition[]> {
  const res = await fetch(`${API_BASE_URL}/multi-agent-orchestration/agents`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch specialist agents');
  return res.json();
}

export async function decomposeTask(
  userIntent: string,
  projectId?: string,
  token?: string
): Promise<TaskDecompositionResponse> {
  const res = await fetch(`${API_BASE_URL}/multi-agent-orchestration/decompose`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ user_intent: userIntent, project_id: projectId })
  });
  if (!res.ok) throw new Error('Failed to decompose task');
  return res.json();
}

export async function routeTask(
  decompositionId: string,
  token?: string
): Promise<RouteResponse> {
  const res = await fetch(`${API_BASE_URL}/multi-agent-orchestration/route`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ decomposition_id: decompositionId })
  });
  if (!res.ok) throw new Error('Failed to route task');
  return res.json();
}

export async function executeAgentSubtask(
  subtaskId: string,
  agentId: string,
  inputPayload: Record<string, any> = {},
  token?: string
): Promise<SubtaskExecutionResponse> {
  const res = await fetch(`${API_BASE_URL}/multi-agent-orchestration/execute-subtask`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ subtask_id: subtaskId, agent_id: agentId, input_payload: inputPayload })
  });
  if (!res.ok) throw new Error('Failed to execute agent subtask');
  return res.json();
}

export async function verifyAndSynthesize(
  subtaskOutputs: Record<string, any>[],
  token?: string
): Promise<SynthesisResponse> {
  const res = await fetch(`${API_BASE_URL}/multi-agent-orchestration/verify-synthesize`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ subtask_outputs: subtaskOutputs })
  });
  if (!res.ok) throw new Error('Failed to verify and synthesize outputs');
  return res.json();
}
