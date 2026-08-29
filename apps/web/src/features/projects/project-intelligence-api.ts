const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface ProjectHealth {
  status: 'HEALTHY' | 'ATTENTION' | 'AT_RISK' | 'UNKNOWN';
  explanation: string;
  overdue_count: number;
  blocked_count: number;
}

export interface TaskSummary {
  total: number;
  open: number;
  in_progress: number;
  blocked: number;
  overdue: number;
  completed: number;
}

export interface DecisionItem {
  id: string;
  content: string;
  created_at: string;
}

export interface ChangeItem {
  id: string;
  event_type: string;
  title: string;
  description: string;
  occurred_at: string;
}

export interface ProjectIntelligenceResponse {
  project_id: string;
  name: string;
  description?: string;
  status: string;
  health: ProjectHealth;
  current_state: str;
  task_summary: TaskSummary;
  key_decisions: DecisionItem[];
  recent_changes: ChangeItem[];
  open_questions: Array<Record<string, any>>;
  conflicts: Array<Record<string, any>>;
}

export async function fetchProjectIntelligence(
  projectId: string,
  token?: string
): Promise<ProjectIntelligenceResponse> {
  const res = await fetch(`${API_BASE_URL}/projects/${projectId}/intelligence`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch project intelligence');
  return res.json();
}
