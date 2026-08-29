const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface ClaimItem {
  claim_id: string;
  claim_text: string;
  claim_type: string;
  supporting_sources: string[];
  contradicting_sources: string[];
  confidence: string;
  conflict_detected?: boolean;
  conflict_explanation?: string;
  timestamp: string;
}

export interface SynthesisResponse {
  organization_id: string;
  project_id: string | null;
  evidence_bundle: ClaimItem[];
  total_claims: number;
  conflicts_surfaced: number;
  synthesis_status: string;
}

export interface CandidateResponse {
  candidate_id: string;
  decision_question: string;
  readiness_status: string;
  objectives: string[];
  constraints: {
    hard_constraints: string[];
    soft_constraints: string[];
  };
  evidence_gaps: Array<{
    gap_id: string;
    missing_information: string;
    why_it_matters: string;
    action_to_obtain: string;
  }>;
  readiness_explanation: string;
}

export interface CompareOptionsResponse {
  candidate_id: string;
  evaluated_options: Array<{
    option_id: string;
    option_name: string;
    source_type: string;
    feasibility: string;
    feasibility_reason?: string;
    weighted_score: number;
    criteria_breakdown: Record<string, string>;
    tradeoff_summary: string;
  }>;
  recommended_option: string;
  recommendation_reasoning: string;
  sensitivity_analysis: {
    test_case: string;
    stability: string;
    explanation: string;
  };
}

export interface RecordDecisionResponse {
  decision_id: string;
  decision_question: string;
  chosen_option_id: string;
  rationale: string;
  version: number;
  supersedes_decision_id: string | null;
  decision_maker: string;
  recorded_at: string;
  status: string;
  decision_brief_drafts: {
    executive_brief: string;
    technical_brief: string;
  };
}

export async function synthesizeKnowledge(
  projectId?: string,
  token?: string
): Promise<SynthesisResponse> {
  const res = await fetch(`${API_BASE_URL}/decision-intelligence/synthesize`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ project_id: projectId })
  });
  if (!res.ok) throw new Error('Knowledge synthesis failed');
  return res.json();
}

export async function evaluateDecisionCandidate(
  topicDescription: string,
  projectId?: string,
  token?: string
): Promise<CandidateResponse> {
  const res = await fetch(`${API_BASE_URL}/decision-intelligence/candidates`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ topic_description: topicDescription, project_id: projectId })
  });
  if (!res.ok) throw new Error('Candidate evaluation failed');
  return res.json();
}

export async function compareDecisionOptions(
  candidateId: string,
  options: Array<Record<string, any>>,
  token?: string
): Promise<CompareOptionsResponse> {
  const res = await fetch(`${API_BASE_URL}/decision-intelligence/compare-options`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ candidate_id: candidateId, options })
  });
  if (!res.ok) throw new Error('Option comparison failed');
  return res.json();
}

export async function recordDecision(
  decisionQuestion: string,
  chosenOptionId: string,
  rationale: string,
  supersedesId?: string,
  token?: string
): Promise<RecordDecisionResponse> {
  const res = await fetch(`${API_BASE_URL}/decision-intelligence/record`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({
      decision_question: decisionQuestion,
      chosen_option_id: chosenOptionId,
      rationale,
      supersedes_decision_id: supersedesId
    })
  });
  if (!res.ok) throw new Error('Recording decision failed');
  return res.json();
}
