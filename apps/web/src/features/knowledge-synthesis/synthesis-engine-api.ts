const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface SynthesisSource {
  id: string;
  title: string;
  type: string;
  status: string;
  citation: string;
}

export interface SynthesisStructuredAnswer {
  current_state: string;
  why: string;
  open_work: string;
  conflicts: string;
}

export interface SynthesisResponse {
  query: string;
  mode: string;
  project_id: string;
  structured_answer: SynthesisStructuredAnswer;
  confidence: string;
  sources: SynthesisSource[];
  suggested_actions: string[];
}

export interface SynthesisModeItem {
  mode: string;
  description: string;
}

export async function executeSynthesis(
  query: str,
  mode: str = 'OVERVIEW',
  projectId?: string,
  token?: string
): Promise<SynthesisResponse> {
  const res = await fetch(`${API_BASE_URL}/knowledge/synthesis/synthesize`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ query, mode, project_id: projectId })
  });
  if (!res.ok) throw new Error('Failed to execute synthesis');
  return res.json();
}

export async function fetchSynthesisModes(
  token?: string
): Promise<SynthesisModeItem[]> {
  const res = await fetch(`${API_BASE_URL}/knowledge/synthesis/modes`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch synthesis modes');
  return res.json();
}
