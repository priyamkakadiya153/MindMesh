const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface ProjectMemoryResponse {
  project_id: string;
  project_name: string;
  purpose: string;
  current_state: string;
  decisions: Array<{ id: string; title: string; status: string }>;
  milestones: Array<{ id: string; name: string; status: string }>;
  outcomes: Array<{ id: string; title: string; details: string }>;
  lessons: Array<{ id: string; situation: string; lesson: string }>;
  retrieved_at: string;
}

export interface ContextPackResponse {
  scope_type: string;
  scope_id: string;
  title: string;
  current_state: string;
  relevant_knowledge: string[];
  recent_decisions: string[];
  dependencies: string[];
  known_risks: string[];
  open_questions: string[];
  generated_at: string;
}

export interface KnowledgeBriefResponse {
  project_id: string;
  brief_title: string;
  overview: string;
  sections: Array<{
    heading: string;
    content: string;
    sources: string[];
  }>;
  evidence_links_count: number;
  provenance_label: string;
  generated_at: string;
}

export interface KnowledgeHandoffResponse {
  handoff_id: string;
  project_id: string;
  created_by: string;
  recipient_id: string;
  current_state: string;
  key_decisions: string[];
  outstanding_work: string[];
  known_risks: string[];
  open_questions: string[];
  status: string;
  created_at: string;
}

export interface DecisionMemoryResponse {
  decision_id: string;
  problem_statement: string;
  chosen_option: string;
  alternatives_evaluated: string[];
  reasoning: string;
  evidence: string[];
  outcome: string;
  status: string;
}

export interface MemoryHealthResponse {
  memory_coverage: string;
  stale_memory_items: number;
  conflicting_memory_items: number;
  memory_gaps: Array<{
    gap_id: string;
    title: string;
    description: string;
  }>;
  reconstructed_items: number;
}

export interface MemoryDigestResponse {
  total_memory_objects: number;
  active_context_packs: number;
  synthesized_knowledge_briefs: number;
  knowledge_handoffs_completed: number;
  lessons_reused: number;
}

export async function fetchProjectMemory(
  projectId: string,
  token?: string
): Promise<ProjectMemoryResponse> {
  const res = await fetch(`${API_BASE_URL}/memory-fabric/project-memory?project_id=${encodeURIComponent(projectId)}`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch project memory');
  return res.json();
}

export async function generateContextPack(
  scopeType: string = 'TASK',
  scopeId: string = 'task-deploy-101',
  token?: string
): Promise<ContextPackResponse> {
  const res = await fetch(`${API_BASE_URL}/memory-fabric/context-pack`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ scope_type: scopeType, scope_id: scopeId })
  });
  if (!res.ok) throw new Error('Failed to generate context pack');
  return res.json();
}

export async function synthesizeKnowledgeBrief(
  projectId: string,
  token?: string
): Promise<KnowledgeBriefResponse> {
  const res = await fetch(`${API_BASE_URL}/memory-fabric/knowledge-brief`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ project_id: projectId })
  });
  if (!res.ok) throw new Error('Failed to synthesize knowledge brief');
  return res.json();
}

export async function createKnowledgeHandoff(
  projectId: string,
  recipientId: string,
  token?: string
): Promise<KnowledgeHandoffResponse> {
  const res = await fetch(`${API_BASE_URL}/memory-fabric/create-handoff`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ project_id: projectId, recipient_id: recipientId })
  });
  if (!res.ok) throw new Error('Failed to create knowledge handoff');
  return res.json();
}

export async function fetchDecisionMemory(
  decisionId: string,
  token?: string
): Promise<DecisionMemoryResponse> {
  const res = await fetch(`${API_BASE_URL}/memory-fabric/decision-memory?decision_id=${encodeURIComponent(decisionId)}`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch decision memory');
  return res.json();
}

export async function fetchMemoryHealth(
  token?: string
): Promise<MemoryHealthResponse> {
  const res = await fetch(`${API_BASE_URL}/memory-fabric/health`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch memory health');
  return res.json();
}

export async function fetchMemoryDigest(
  token?: string
): Promise<MemoryDigestResponse> {
  const res = await fetch(`${API_BASE_URL}/memory-fabric/digest`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch memory digest');
  return res.json();
}
