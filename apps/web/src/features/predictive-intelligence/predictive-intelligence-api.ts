const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface EarlyWarningItem {
  prediction_id: string;
  type: string;
  severity: 'CRITICAL' | 'IMPORTANT' | 'ATTENTION' | 'INFORMATIONAL' | string;
  title: string;
  reason: string;
  evidence: string[];
  affected_entities: string[];
  suggested_next_step: string;
  status: string;
  created_at: string;
}

export interface DecisionImpactResponse {
  decision_id: string;
  decision_title: string;
  direct_impact: Array<{ type: string; name: string; impact_summary: string }>;
  indirect_impact: Array<{ type: string; name: string; impact_summary: string }>;
  graph_depth_evaluated: number;
}

export interface WhatIfResponse {
  scenario: string;
  known_impacts: string[];
  potential_risks: string[];
  unknowns: string[];
  historical_references: string[];
}

export interface ReadinessCategoryItem {
  title: string;
  status: string;
}

export interface ProjectReadinessResponse {
  project_name: string;
  overall_readiness: string;
  categories: {
    blockers: ReadinessCategoryItem[];
    dependencies: ReadinessCategoryItem[];
    knowledge: ReadinessCategoryItem[];
    decisions: ReadinessCategoryItem[];
    documentation: ReadinessCategoryItem[];
    open_questions: ReadinessCategoryItem[];
  };
  readiness_summary: string;
}

export interface DecisionBriefResponse {
  brief_id: string;
  topic: string;
  context: string;
  option_matrix: Array<{
    option: string;
    benefits: string[];
    risks: string[];
    evidence: string;
  }>;
  questions_to_resolve: string[];
  recommended_review: string;
}

export async function fetchEarlyWarnings(
  projectId?: string,
  token?: string
): Promise<EarlyWarningItem[]> {
  const params = new URLSearchParams();
  if (projectId) params.append('project_id', projectId);
  const res = await fetch(`${API_BASE_URL}/predictive/early-warnings?${params.toString()}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch early warnings');
  return res.json();
}

export async function fetchDecisionImpact(
  decisionId: string,
  token?: string
): Promise<DecisionImpactResponse> {
  const res = await fetch(`${API_BASE_URL}/predictive/decision-impact/${decisionId}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch decision impact');
  return res.json();
}

export async function performWhatIfAnalysis(
  scenario: string,
  projectId?: string,
  token?: string
): Promise<WhatIfResponse> {
  const res = await fetch(`${API_BASE_URL}/predictive/what-if`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ scenario, project_id: projectId })
  });
  if (!res.ok) throw new Error('Failed to perform what-if analysis');
  return res.json();
}

export async function fetchProjectReadiness(
  projectId: string,
  token?: string
): Promise<ProjectReadinessResponse> {
  const res = await fetch(`${API_BASE_URL}/predictive/project-readiness/${projectId}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch project readiness');
  return res.json();
}

export async function generateDecisionBrief(
  topic: string,
  token?: string
): Promise<DecisionBriefResponse> {
  const res = await fetch(`${API_BASE_URL}/predictive/decision-brief`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ topic })
  });
  if (!res.ok) throw new Error('Failed to generate decision brief');
  return res.json();
}

export async function rebuildPredictions(
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/predictive/rebuild-predictions`, {
    method: 'POST',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to rebuild predictions');
  return res.json();
}
