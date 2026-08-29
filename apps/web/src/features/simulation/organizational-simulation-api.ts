const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface DigitalTwinResponse {
  snapshot_id: string;
  timestamp: string;
  data_freshness: string;
  scope: string;
  modeled_entities: {
    projects_count: number;
    tasks_count: number;
    dependencies_count: number;
    active_risks_count: number;
    operating_controls_count: number;
    active_workflows_count: number;
  };
  system_state_hash: string;
}

export interface CreateScenarioResponse {
  scenario_id: string;
  name: string;
  description: string;
  status: string;
  base_snapshot_id: string;
  created_by: string;
  created_at: string;
  changes: Array<{
    target: string;
    attribute: string;
    original_value: any;
    new_value: any;
    reason: string;
  }>;
  assumptions: Array<{
    statement: string;
    type: string;
    confidence: string;
  }>;
}

export interface RunSimulationResponse {
  simulation_run_id: string;
  scenario_id: string;
  status: string;
  modeled_delta: {
    duration_delta: string;
    cost_delta: string;
    risk_delta: string;
    compliance_impact: string;
  };
  impact_propagation: {
    direct_impacts: string[];
    indirect_downstream_1hop: string[];
    indirect_downstream_2hop: string[];
  };
  sensitivity_analysis: Array<{
    variable: string;
    impact_ranking: number;
    comment: string;
  }>;
  uncertainty_range: {
    best_case: string;
    expected_case: string;
    worst_case: string;
  };
  simulation_confidence: string;
}

export interface CompareScenariosResponse {
  comparison_id: string;
  baseline: string;
  scenarios_evaluated: Array<{
    scenario_id: string;
    name: string;
    duration_estimate: string;
    cost_estimate: string;
    risk_level: string;
    recommendation_rank: number;
  }>;
  tradeoff_summary: string;
}

export interface HandoffScenarioResponse {
  handoff_status: string;
  scenario_id: string;
  error_reason: string | null;
  created_workflow_id?: string;
  workflow_name?: string;
  status?: string;
  handoff_timestamp?: string;
}

export async function fetchDigitalTwinSnapshot(
  token?: string
): Promise<DigitalTwinResponse> {
  const res = await fetch(`${API_BASE_URL}/simulation/digital-twin`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch digital twin snapshot');
  return res.json();
}

export async function createScenario(
  name: string,
  naturalLanguageRequest?: string,
  changes: any[] = [],
  token?: string
): Promise<CreateScenarioResponse> {
  const res = await fetch(`${API_BASE_URL}/simulation/scenarios/create`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ name, natural_language_request: naturalLanguageRequest, changes })
  });
  if (!res.ok) throw new Error('Failed to create scenario');
  return res.json();
}

export async function runSimulation(
  scenarioId: string,
  token?: string
): Promise<RunSimulationResponse> {
  const res = await fetch(`${API_BASE_URL}/simulation/scenarios/run`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ scenario_id: scenarioId })
  });
  if (!res.ok) throw new Error('Failed to run simulation');
  return res.json();
}

export async function compareScenarios(
  scenarioIds: string[],
  token?: string
): Promise<CompareScenariosResponse> {
  const res = await fetch(`${API_BASE_URL}/simulation/scenarios/compare`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ scenario_ids: scenarioIds })
  });
  if (!res.ok) throw new Error('Failed to compare scenarios');
  return res.json();
}

export async function handoffScenarioToWorkflow(
  scenarioId: string,
  isStale: boolean = false,
  token?: string
): Promise<HandoffScenarioResponse> {
  const res = await fetch(`${API_BASE_URL}/simulation/scenarios/handoff`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ scenario_id: scenarioId, is_stale: isStale })
  });
  if (!res.ok) throw new Error('Failed to handoff scenario to workflow');
  return res.json();
}
