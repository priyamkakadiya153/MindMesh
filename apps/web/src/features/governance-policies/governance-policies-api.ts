const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface PolicyDefinition {
  policy_id: string;
  name: string;
  description: string;
  category: string;
  scope: string;
  precedence: number;
  effect: string;
  status: string;
  version: string;
  owner: string;
  effective_date: string;
}

export interface PolicyEvaluationResponse {
  decision: string;
  result_code: string;
  matched_policies: string[];
  reason: string;
  required_controls: string[];
  timestamp: string;
}

export interface PolicyExceptionResponse {
  exception_id: string;
  policy_id: string;
  status: string;
  granted_to: string;
  justification: string;
  granted_at: string;
  expires_at: string;
  is_temporary: boolean;
  non_propagating: boolean;
}

export interface PolicySimulationResponse {
  simulation_id: string;
  proposed_rule: string;
  mode: string;
  affected_entities: {
    active_workflows_blocked: number;
    agents_affected: number;
    projects_affected: number;
  };
  impact_warning: string;
  estimated_compliance_shift: string;
}

export interface GovernanceAuditResponse {
  compliance_indicators: {
    active_policies_count: number;
    open_violations_count: number;
    active_exceptions_count: number;
    compliance_status: string;
  };
  violations: Array<{
    violation_id: string;
    policy_id: string;
    actor: string;
    action: string;
    resource: string;
    severity: string;
    response_action: string;
    timestamp: string;
  }>;
  audit_trail: Array<{
    event_id: string;
    type: string;
    decision: string;
    actor: string;
    timestamp: string;
  }>;
}

export async function fetchGovernancePolicies(
  query?: string,
  category?: string,
  token?: string
): Promise<PolicyDefinition[]> {
  const params = new URLSearchParams();
  if (query) params.append('query', query);
  if (category) params.append('category', category);

  const res = await fetch(`${API_BASE_URL}/governance-policies/list?${params.toString()}`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch governance policies');
  return res.json();
}

export async function evaluateGovernancePolicy(
  action: string,
  dataClassification: string = 'Confidential',
  targetResource: string = 'doc-spec-101',
  context: Record<string, any> = {},
  token?: string
): Promise<PolicyEvaluationResponse> {
  const res = await fetch(`${API_BASE_URL}/governance-policies/evaluate`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({
      action,
      data_classification: dataClassification,
      target_resource: targetResource,
      context
    })
  });
  if (!res.ok) throw new Error('Failed to evaluate policy');
  return res.json();
}

export async function requestPolicyException(
  policyId: string,
  justification: string,
  durationHours: number = 24,
  token?: string
): Promise<PolicyExceptionResponse> {
  const res = await fetch(`${API_BASE_URL}/governance-policies/exceptions/request`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({
      policy_id: policyId,
      justification,
      duration_hours: durationHours
    })
  });
  if (!res.ok) throw new Error('Failed to request policy exception');
  return res.json();
}

export async function simulatePolicyImpact(
  proposedPolicyRule: string,
  token?: string
): Promise<PolicySimulationResponse> {
  const res = await fetch(`${API_BASE_URL}/governance-policies/simulate`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ proposed_policy_rule: proposedPolicyRule })
  });
  if (!res.ok) throw new Error('Failed to simulate policy impact');
  return res.json();
}

export async function fetchGovernanceAudit(
  token?: string
): Promise<GovernanceAuditResponse> {
  const res = await fetch(`${API_BASE_URL}/governance-policies/audit`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch governance audit');
  return res.json();
}
