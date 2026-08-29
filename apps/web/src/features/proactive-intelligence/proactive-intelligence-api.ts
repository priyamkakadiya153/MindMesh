const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface ProactiveSignalExplanation {
  what: string;
  why: string;
  evidence: string[];
  time_horizon: string;
  impact: string;
  what_can_be_done: string;
}

export interface ProactiveSignal {
  signal_id: string;
  signal_type: string;
  severity: string;
  confidence: string;
  title: string;
  explanation: ProactiveSignalExplanation;
  status: string;
  detected_at: string;
}

export interface ProactiveSignalsResponse {
  organization_id: string;
  project_id: string | null;
  detected_signals: ProactiveSignal[];
  total_active_signals: number;
}

export interface WhatIfResponse {
  scenario_name: string;
  mode: string;
  assumptions: string[];
  simulated_outcomes: Record<string, any>;
  side_effect_guarantee: string;
}

export interface BriefingResponse {
  briefing_type: string;
  user: string;
  generated_at: string;
  summary_bullet_points: string[];
  recommended_next_actions: Array<Record<string, any>>;
}

export async function fetchProactiveSignals(
  projectId?: string,
  token?: string
): Promise<ProactiveSignalsResponse> {
  const url = projectId 
    ? `${API_BASE_URL}/proactive-intelligence/signals?project_id=${projectId}`
    : `${API_BASE_URL}/proactive-intelligence/signals`;
  const res = await fetch(url, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch proactive signals');
  return res.json();
}

export async function manageSignalStatus(
  signalId: string,
  action: string,
  reason?: string,
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/proactive-intelligence/manage-signal`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ signal_id: signalId, action, reason })
  });
  if (!res.ok) throw new Error('Failed to manage signal status');
  return res.json();
}

export async function runWhatIfScenario(
  scenarioName: string,
  parameters: Record<string, any>,
  token?: string
): Promise<WhatIfResponse> {
  const res = await fetch(`${API_BASE_URL}/proactive-intelligence/what-if`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ scenario_name: scenarioName, parameters })
  });
  if (!res.ok) throw new Error('What-If scenario failed');
  return res.json();
}

export async function fetchProactiveBriefing(
  type: string = 'MORNING',
  token?: string
): Promise<BriefingResponse> {
  const res = await fetch(`${API_BASE_URL}/proactive-intelligence/briefing?type=${type}`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch briefing');
  return res.json();
}
