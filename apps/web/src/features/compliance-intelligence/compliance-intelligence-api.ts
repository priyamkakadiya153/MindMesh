const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface FrameworksAndControlsResponse {
  frameworks: Array<{
    framework_id: string;
    name: string;
    version: string;
    status: string;
    requirements: Array<{
      requirement_id: string;
      title: string;
      category: string;
      applicability: string;
      controls_mapped: string[];
    }>;
  }>;
  controls: Array<{
    control_id: string;
    name: string;
    description: string;
    type: string;
    status: string;
    design_effectiveness: string;
    operating_effectiveness: string;
    mapped_policy_id: string;
    owner: string;
  }>;
}

export interface TestControlResponse {
  test_id: string;
  control_id: string;
  result: string;
  design_effectiveness: string;
  operating_effectiveness: string;
  gap_detected: {
    gap_id: string;
    classification: string;
    description: string;
  } | null;
  tested_at: string;
  tested_by: string;
}

export interface EvidenceCollectResponse {
  evidence_id: string;
  control_id: string;
  type: string;
  source: string;
  collected_at: string;
  freshness: string;
  sha256_checksum: string;
  provenance: {
    collector: string;
    scope: string;
    verified: boolean;
  };
}

export interface RemediateFindingResponse {
  finding_id: string;
  title: string;
  severity: string;
  status: string;
  reopened_reason?: string;
  remediation_plan?: {
    plan_id: string;
    status: string;
    remediated_by: string;
    verified_at: string;
  };
  linked_risk_id: string;
  updated_at: string;
}

export interface AcceptRiskResponse {
  risk_id: string;
  title: string;
  category: string;
  inherent_score: number;
  residual_score: number;
  status: string;
  acceptance_record: {
    accepted_by: string;
    granted_at: string;
    expires_at: string;
    is_expired: boolean;
  };
}

export interface AuditReadinessResponse {
  overall_status: string;
  readiness_score: string;
  missing_evidence_count: number;
  readiness_warning: string | null;
  audit_package: {
    package_id: string;
    framework: string;
    generated_at: string;
    generated_by: string;
    evidence_items_included: number;
    control_coverage: string;
    package_sha256: string;
  } | null;
}

export async function fetchFrameworksAndControls(
  token?: string
): Promise<FrameworksAndControlsResponse> {
  const res = await fetch(`${API_BASE_URL}/compliance/frameworks`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch frameworks and controls');
  return res.json();
}

export async function testComplianceControl(
  controlId: string,
  testType: string = 'AUTOMATED',
  simulateFailure: boolean = false,
  token?: string
): Promise<TestControlResponse> {
  const res = await fetch(`${API_BASE_URL}/compliance/controls/test`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ control_id: controlId, test_type: testType, simulate_failure: simulateFailure })
  });
  if (!res.ok) throw new Error('Failed to test compliance control');
  return res.json();
}

export async function collectComplianceEvidence(
  controlId: string,
  evidenceType: string = 'LOG',
  contentPayload: string = 'Audit event log content for SOC2 verification',
  token?: string
): Promise<EvidenceCollectResponse> {
  const res = await fetch(`${API_BASE_URL}/compliance/evidence/collect`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ control_id: controlId, evidence_type: evidenceType, content_payload: contentPayload })
  });
  if (!res.ok) throw new Error('Failed to collect evidence');
  return res.json();
}

export async function remediateFinding(
  findingId: string | null,
  title: string,
  severity: string = 'HIGH',
  verificationPassed: boolean = true,
  token?: string
): Promise<RemediateFindingResponse> {
  const res = await fetch(`${API_BASE_URL}/compliance/findings/remediate`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ finding_id: findingId, title, severity, verification_passed: verificationPassed })
  });
  if (!res.ok) throw new Error('Failed to remediate finding');
  return res.json();
}

export async function acceptResidualRisk(
  riskTitle: string,
  category: string = 'Security',
  inherentScore: number = 80,
  durationHours: number = 24,
  token?: string
): Promise<AcceptRiskResponse> {
  const res = await fetch(`${API_BASE_URL}/compliance/risks/accept`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ risk_title: riskTitle, category, inherent_score: inherentScore, duration_hours: durationHours })
  });
  if (!res.ok) throw new Error('Failed to accept residual risk');
  return res.json();
}

export async function fetchAuditReadiness(
  missingEvidence: boolean = false,
  token?: string
): Promise<AuditReadinessResponse> {
  const res = await fetch(`${API_BASE_URL}/compliance/audit-readiness?missing_evidence=${missingEvidence}`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch audit readiness');
  return res.json();
}
