const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface ProjectIntelligenceResponse {
  project_id: string;
  project_name: string;
  health_assessment: {
    overall_status: string;
    health_score: string;
    contributing_signals: Array<{
      signal: string;
      severity: string;
      description: string;
      evidence_ids: string[];
    }>;
  };
  trend: {
    direction: string;
    time_window: string;
    what_changed: string;
  };
  risk_signals: string[];
  provenance: {
    source_tables: string[];
    last_calculated_at: string;
  };
}

export interface KnowledgeHealthResponse {
  organization_id: string;
  health_summary: {
    freshness_score: string;
    verification_breakdown: {
      verified: number;
      unverified: number;
      under_review: number;
      superseded: number;
    };
    stale_documents_count: number;
    unresolved_conflicts_count: number;
  };
  zero_result_searches: Array<{
    query: string;
    search_count: number;
    zero_result_rate: string;
    potential_knowledge_gap: string;
    evidence: string;
  }>;
  knowledge_gaps: Array<{
    domain: string;
    gap_description: string;
    impact: string;
    recommended_action: string;
  }>;
}

export interface BottlenecksResponse {
  organization_id: string;
  bottlenecks: Array<{
    id: string;
    type: string;
    target: string;
    affected_tasks_count: number;
    affected_projects: string[];
    description: string;
    evidence_chain: string[];
  }>;
  shared_dependency_risks: Array<{
    dependency_name: string;
    impact_scope: string;
    risk_level: string;
    description: string;
  }>;
}

export interface TrendsAnomaliesResponse {
  trends: Array<{
    metric: string;
    direction: string;
    data_points: number[];
    time_range: string;
    minimum_evidence: string;
  }>;
  anomalies: Array<{
    id: string;
    event_type: string;
    observed_anomaly: string;
    possible_explanation: string;
    confidence: string;
    evidence: string;
  }>;
  recurring_patterns: Array<{
    id: string;
    pattern_name: string;
    occurrences: number;
    affected_scope: string;
    potential_explanation: string;
    confidence: string;
  }>;
}

export interface PortfolioAnalyticsResponse {
  organization_id: string;
  portfolio_summary: {
    total_active_projects: number;
    healthy_projects: number;
    at_risk_projects: number;
    overall_portfolio_health: string;
  };
  projects_matrix: Array<{
    id: string;
    name: string;
    status: string;
    progress_percentage: number;
    open_tasks: number;
    blocked_tasks: number;
    top_risk: string;
  }>;
  executive_signals: string[];
}

export interface DrilldownEvidenceResponse {
  insight_id: string;
  explanation: {
    what: string;
    why: string;
    impact: string;
    what_changed: string;
    recommended_action: string;
  };
  evidence_chain: Array<{
    entity_type: string;
    entity_id: string;
    title: string;
    status: string;
  }>;
  rbac_authorized: boolean;
}

export async function fetchProjectIntelligence(projectId: string, token?: string): Promise<ProjectIntelligenceResponse> {
  const res = await fetch(`${API_BASE_URL}/data-intelligence/project-health/${projectId}`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch project intelligence');
  return res.json();
}

export async function fetchKnowledgeHealthAnalytics(token?: string): Promise<KnowledgeHealthResponse> {
  const res = await fetch(`${API_BASE_URL}/data-intelligence/knowledge-health`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch knowledge health analytics');
  return res.json();
}

export async function fetchBottlenecksAndDependencies(token?: string): Promise<BottlenecksResponse> {
  const res = await fetch(`${API_BASE_URL}/data-intelligence/bottlenecks`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch bottlenecks and dependencies');
  return res.json();
}

export async function fetchTrendsAnomalies(token?: string): Promise<TrendsAnomaliesResponse> {
  const res = await fetch(`${API_BASE_URL}/data-intelligence/trends-anomalies`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch trends and anomalies');
  return res.json();
}

export async function fetchPortfolioAnalytics(token?: string): Promise<PortfolioAnalyticsResponse> {
  const res = await fetch(`${API_BASE_URL}/data-intelligence/portfolio`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch portfolio analytics');
  return res.json();
}

export async function fetchDrilldownEvidence(insightId: string, token?: string): Promise<DrilldownEvidenceResponse> {
  const res = await fetch(`${API_BASE_URL}/data-intelligence/drilldown/${insightId}`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch drilldown evidence');
  return res.json();
}
