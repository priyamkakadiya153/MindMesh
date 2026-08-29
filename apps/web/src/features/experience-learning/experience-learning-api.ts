const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface ExperienceRecordResponse {
  record_id: string;
  title: string;
  situation: string;
  action: string;
  outcome: str;
  organization_id: string;
  project_id: string | null;
  confidence: string;
  validation_status: string;
  captured_by: string;
  created_at: string;
  lessons_extracted: string[];
}

export interface OutcomeAttributionResponse {
  project_id: string | null;
  expected_outcome: string;
  actual_outcome: string;
  outcome_classification: string;
  contributing_factors: Array<{
    factor: string;
    impact: string;
    evidence: string;
  }>;
  attribution_explanation: string;
}

export interface LessonsPatternsResponse {
  organization_id: string;
  extracted_lessons: Array<{
    lesson_id: string;
    claim: string;
    lesson_type: string;
    evidence: string[];
    generalization_level: string;
    confidence: string;
  }>;
  detected_patterns: Array<{
    pattern_id: string;
    pattern_type: string;
    title: string;
    observed_instances: number;
    confidence: string;
    transferability: string;
  }>;
}

export interface PlaybookRetroResponse {
  retrospective_draft: {
    project_id: string | null;
    observed_events: string[];
    interpretations: string[];
    opinions: string[];
    extracted_actions: string[];
  };
  playbook_candidate: {
    playbook_id: string;
    title: string;
    status: string;
    applicability_conditions: string[];
    non_conditions: string[];
    recommended_steps: string[];
    drift_status: string;
  };
}

export interface ImprovementResponse {
  opportunity_id: string;
  problem_description: string;
  proposal: string;
  classification: string;
  status: string;
  owner: string;
  metrics: {
    baseline: string;
    target: string;
    actual: string;
  };
  phase_621_execution_plan_prepared: boolean;
}

export async function captureExperience(
  title: string,
  situation: string,
  action: string,
  outcome: string,
  projectId?: string,
  token?: string
): Promise<ExperienceRecordResponse> {
  const res = await fetch(`${API_BASE_URL}/experience-learning/capture`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ title, situation, action, outcome, project_id: projectId })
  });
  if (!res.ok) throw new Error('Experience capture failed');
  return res.json();
}

export async function analyzeOutcomeAttribution(
  expectedOutcome: string,
  actualOutcome: string,
  projectId?: string,
  token?: string
): Promise<OutcomeAttributionResponse> {
  const res = await fetch(`${API_BASE_URL}/experience-learning/outcomes`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ expected_outcome: expectedOutcome, actual_outcome: actualOutcome, project_id: projectId })
  });
  if (!res.ok) throw new Error('Outcome attribution failed');
  return res.json();
}

export async function fetchLessonsAndPatterns(
  token?: string
): Promise<LessonsPatternsResponse> {
  const res = await fetch(`${API_BASE_URL}/experience-learning/lessons-patterns`, {
    method: 'POST',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Lessons & patterns fetch failed');
  return res.json();
}

export async function generatePlaybookAndRetro(
  projectId?: string,
  token?: string
): Promise<PlaybookRetroResponse> {
  const res = await fetch(`${API_BASE_URL}/experience-learning/playbooks${projectId ? `?project_id=${projectId}` : ''}`, {
    method: 'POST',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Playbook & Retrospective generation failed');
  return res.json();
}

export async function manageContinuousImprovement(
  problemDescription: string,
  proposal: string,
  token?: string
): Promise<ImprovementResponse> {
  const res = await fetch(`${API_BASE_URL}/experience-learning/improvements`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ problem_description: problemDescription, proposal })
  });
  if (!res.ok) throw new Error('Improvement management failed');
  return res.json();
}
