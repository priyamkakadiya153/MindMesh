const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface OperationsHealthResponse {
  freshness_monitor: string;
  conflict_detector: string;
  risk_synthesizer: string;
  automation_engine: string;
  reprocessing_queue: string;
  overall_status: string;
  message: string;
}

export interface IssueItem {
  id: string;
  issue_type: string;
  severity: 'CRITICAL' | 'IMPORTANT' | 'ATTENTION' | 'INFORMATIONAL' | string;
  title: string;
  description: string;
  affected_entity: string;
  suggested_action: string;
}

export interface ProjectRiskItem {
  risk_id: string;
  project_name: string;
  severity: string;
  title: string;
  signals: string[];
  recommendation: string;
}

export interface DetectedIssuesResponse {
  total_issues: number;
  total_risks: number;
  issues: IssueItem[];
  project_risks: ProjectRiskItem[];
}

export interface KnowledgeDigestResponse {
  digest_date: string;
  important_changes: Array<{
    title: string;
    summary: string;
    timestamp: string;
  }>;
  your_work: Array<{
    title: string;
    status: string;
    action_required: string;
  }>;
  attention_items: string[];
}

export interface AutomationRule {
  rule_id: string;
  rule_name: string;
  trigger_event: string;
  scope: string;
  action_name: string;
  is_enabled: boolean;
  created_by: string;
  created_at: string;
}

export async function fetchOperationsHealth(
  token?: string
): Promise<OperationsHealthResponse> {
  const res = await fetch(`${API_BASE_URL}/operations/autonomous/health`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch operations health');
  return res.json();
}

export async function fetchDetectedIssues(
  projectId?: string,
  token?: string
): Promise<DetectedIssuesResponse> {
  const params = new URLSearchParams();
  if (projectId) params.append('project_id', projectId);
  const res = await fetch(`${API_BASE_URL}/operations/autonomous/issues?${params.toString()}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch detected issues');
  return res.json();
}

export async function fetchKnowledgeDigest(
  token?: string
): Promise<KnowledgeDigestResponse> {
  const res = await fetch(`${API_BASE_URL}/operations/autonomous/digest`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch knowledge digest');
  return res.json();
}

export async function fetchAutomationRules(
  token?: string
): Promise<AutomationRule[]> {
  const res = await fetch(`${API_BASE_URL}/operations/autonomous/rules`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch automation rules');
  return res.json();
}

export async function createAutomationRule(
  ruleName: string,
  triggerEvent: string,
  scope: string,
  actionName: string,
  token?: string
): Promise<AutomationRule> {
  const res = await fetch(`${API_BASE_URL}/operations/autonomous/rules`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({
      rule_name: ruleName,
      trigger_event: triggerEvent,
      scope: scope,
      action_name: actionName
    })
  });
  if (!res.ok) throw new Error('Failed to create automation rule');
  return res.json();
}

export async function toggleAutomationRule(
  ruleId: string,
  enable: boolean,
  token?: string
): Promise<any> {
  const params = new URLSearchParams({ enable: enable.toString() });
  const res = await fetch(`${API_BASE_URL}/operations/autonomous/rules/${ruleId}/toggle?${params.toString()}`, {
    method: 'POST',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to toggle automation rule');
  return res.json();
}

export async function triggerReprocessEntity(
  entityType: string,
  entityId: string,
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/operations/autonomous/reprocess`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ entity_type: entityType, entity_id: entityId })
  });
  if (!res.ok) throw new Error('Failed to reprocess entity');
  return res.json();
}

export async function triggerMaintenanceReindex(
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/operations/autonomous/reindex`, {
    method: 'POST',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to reindex operations');
  return res.json();
}
