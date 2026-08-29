const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface PerformanceBaselinesResponse {
  p50_ms: Record<string, number>;
  p95_ms: Record<string, number>;
  p99_ms: Record<string, number>;
  throughput_rps: number;
  provenance_label: string;
}

export interface AIRouteResponse {
  task_complexity: string;
  selected_model: string;
  routing_path: string;
  context_deduplicated: boolean;
  tokens_saved: number;
  estimated_cost: string;
  first_token_latency_ms: number;
}

export interface CapacityMetricsResponse {
  capacity_limits: {
    max_supported_concurrent_users: number;
    max_concurrent_ai_jobs: number;
    max_daily_file_ingestions: number;
    storage_growth_headroom: string;
  };
  multi_instance_leader_election: {
    status: string;
    coordination_mechanism: string;
  };
  cost_telemetry: {
    current_month_ai_cost: string;
    budget_limit: string;
    cost_efficiency_score: string;
  };
}

export async function fetchPerformanceBaselines(token?: string): Promise<PerformanceBaselinesResponse> {
  const res = await fetch(`${API_BASE_URL}/performance-scale/baselines`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch performance baselines');
  return res.json();
}

export async function optimizeQueryExecution(
  queryType: string,
  cursor?: string,
  limit: number = 50,
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/performance-scale/optimize-query`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ query_type: queryType, cursor, limit })
  });
  if (!res.ok) throw new Error('Query optimization failed');
  return res.json();
}

export async function routeAIRequest(
  taskComplexity: string,
  rawPrompt: string,
  token?: string
): Promise<AIRouteResponse> {
  const res = await fetch(`${API_BASE_URL}/performance-scale/route-ai`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ task_complexity: taskComplexity, raw_prompt: rawPrompt })
  });
  if (!res.ok) throw new Error('AI routing failed');
  return res.json();
}

export async function batchEmbeddings(
  documentIds: string[],
  workspaceId: string,
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/performance-scale/batch-embeddings`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ document_ids: documentIds, workspace_id: workspaceId })
  });
  if (!res.ok) throw new Error('Embedding batching failed');
  return res.json();
}

export async function fetchCapacityMetrics(token?: string): Promise<CapacityMetricsResponse> {
  const res = await fetch(`${API_BASE_URL}/performance-scale/capacity-metrics`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch capacity metrics');
  return res.json();
}
