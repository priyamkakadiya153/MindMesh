const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface DeepHealthResponse {
  overall_status: string;
  services: {
    api: { status: string; latency_ms: number };
    postgresql: { status: string; latency_ms: number; pool_usage: string };
    redis: { status: string; latency_ms: number; memory_usage: string };
    chromadb: { status: string; latency_ms: number; vector_count: number };
    workers: { status: string; active_jobs: number; queue_depth: number };
    websockets: { status: string; active_connections: number };
    storage: { status: string; available_capacity: string };
    ai_providers: { status: string; circuit_breaker: string };
  };
  timestamp: string;
}

export interface OperationsDashboardResponse {
  system_health: string;
  circuit_breaker: {
    status: string;
    failure_count: number;
    last_failure_time?: string;
    cooldown_seconds: number;
  };
  dead_letter_queue_count: number;
  dead_letter_jobs: Array<{
    job_id: string;
    job_type: string;
    owner: string;
    attempts: number;
    max_attempts: number;
    last_error: string;
    idempotency_key: string;
    status: string;
    failed_at: string;
  }>;
  active_incidents: Array<{
    incident_id: string;
    service: string;
    severity: string;
    status: string;
    started_at: string;
    details: string;
  }>;
  queue_depth: number;
  timestamp: string;
}

export async function fetchLiveness(): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/production-operations/health`);
  if (!res.ok) throw new Error('Liveness check failed');
  return res.json();
}

export async function fetchReadiness(): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/production-operations/readiness`);
  if (!res.ok) throw new Error('Readiness check failed');
  return res.json();
}

export async function fetchDeepHealth(token?: string): Promise<DeepHealthResponse> {
  const res = await fetch(`${API_BASE_URL}/production-operations/deep-health`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch deep health');
  return res.json();
}

export async function executeCircuitBreakerTest(
  operationName: string,
  simulateFailure: boolean,
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/production-operations/execute-cb`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ operation_name: operationName, simulate_failure: simulateFailure })
  });
  if (!res.ok) throw new Error('Circuit breaker test failed');
  return res.json();
}

export async function manageBackgroundJob(
  jobType: string,
  idempotencyKey: string,
  simulatePermanentFailure: boolean,
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/production-operations/manage-job`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ job_type: jobType, idempotency_key: idempotencyKey, simulate_permanent_failure: simulatePermanentFailure })
  });
  if (!res.ok) throw new Error('Failed to manage background job');
  return res.json();
}

export async function replayDeadLetterJob(
  jobId: string,
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/production-operations/replay-dead-letter`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ job_id: jobId })
  });
  if (!res.ok) throw new Error('Failed to replay dead letter job');
  return res.json();
}

export async function rebuildIndexes(token?: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/production-operations/rebuild-indexes`, {
    method: 'POST',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to rebuild search/vector indexes');
  return res.json();
}

export async function fetchOperationsDashboard(token?: string): Promise<OperationsDashboardResponse> {
  const res = await fetch(`${API_BASE_URL}/production-operations/dashboard`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch operations dashboard');
  return res.json();
}
