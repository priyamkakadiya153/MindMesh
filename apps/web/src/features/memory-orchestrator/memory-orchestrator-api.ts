const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface ImpactItem {
  entity_id: string;
  entity_type: string;
  title: string;
  impact_level: 'DIRECT' | 'RELATED' | 'POTENTIAL';
  explanation: string;
}

export interface ImpactAnalysisResponse {
  event_type: string;
  source_entity_id: string;
  direct_impact: ImpactItem[];
  related_impact: ImpactItem[];
  potential_impact: ImpactItem[];
  impact_summary: string;
}

export interface DependencyMapResponse {
  entity_id: string;
  upstream_dependencies: Array<{ id: string; type: string; title: string; relation: string }>;
  downstream_impacts: Array<{ id: string; type: string; title: string; relation: string }>;
  has_circular_dependency: boolean;
  dependency_health: string;
}

export interface KnowledgeClusterItem {
  cluster_id: string;
  concept_name: string;
  health: string;
  source_count: number;
  sources: Array<{ type: string; title: string }>;
}

export interface PatternItem {
  pattern_id: string;
  title: string;
  confidence: string;
  reason: string;
  evidence_count: number;
  evidence_items: string[];
  status: string;
}

export interface ImpactSimulationResponse {
  simulation_id: string;
  hypothetical_change: string;
  source_entity_id: string;
  simulation_only: boolean;
  database_modified: boolean;
  directly_affected_count: number;
  potentially_affected_count: number;
  simulated_cascade: string[];
}

export async function fetchEventImpactAnalysis(
  eventType: string,
  sourceEntityId: string,
  token?: string
): Promise<ImpactAnalysisResponse> {
  const res = await fetch(`${API_BASE_URL}/memory-orchestration/impact-analysis`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ event_type: eventType, source_entity_id: sourceEntityId })
  });
  if (!res.ok) throw new Error('Failed to fetch impact analysis');
  return res.json();
}

export async function fetchDependencyMap(
  entityId: string,
  token?: string
): Promise<DependencyMapResponse> {
  const res = await fetch(`${API_BASE_URL}/memory-orchestration/dependencies?entity_id=${entityId}`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch dependency map');
  return res.json();
}

export async function fetchKnowledgeClusters(
  token?: string
): Promise<KnowledgeClusterItem[]> {
  const res = await fetch(`${API_BASE_URL}/memory-orchestration/clusters`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch knowledge clusters');
  return res.json();
}

export async function fetchOrganizationalPatterns(
  token?: string
): Promise<PatternItem[]> {
  const res = await fetch(`${API_BASE_URL}/memory-orchestration/patterns`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch organizational patterns');
  return res.json();
}

export async function simulateImpact(
  hypotheticalChange: string,
  sourceEntityId: str,
  token?: string
): Promise<ImpactSimulationResponse> {
  const res = await fetch(`${API_BASE_URL}/memory-orchestration/simulate-impact`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ hypothetical_change: hypotheticalChange, source_entity_id: sourceEntityId })
  });
  if (!res.ok) throw new Error('Failed to simulate impact');
  return res.json();
}
