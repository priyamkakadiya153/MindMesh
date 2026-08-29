const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface TaskItem {
  id: string;
  title: string;
  description: string;
  status: string;
  task_type: string;
  priority: string;
  assignee_id?: string;
  due_date?: string;
  organization_id: string;
  workspace_id?: string;
  project_id?: string;
  source_type?: string;
  source_id?: string;
  decision_id?: string;
  is_ai_extracted: boolean;
  created_at: string;
}

export interface TaskProvenance {
  task_id: string;
  title: string;
  provenance_summary: string;
  source_type: string;
  is_ai_extracted: boolean;
  citations: Array<{ type: string; id: string; title: string }>;
}

export async function fetchTasks(
  filters?: {
    workspaceId?: string;
    projectId?: string;
    status?: string;
    assignee?: string;
  },
  token?: string
): Promise<TaskItem[]> {
  const params = new URLSearchParams();
  if (filters?.workspaceId) params.append('workspace_id', filters.workspaceId);
  if (filters?.projectId) params.append('project_id', filters.projectId);
  if (filters?.status) params.append('status', filters.status);
  if (filters?.assignee) params.append('assignee', filters.assignee);

  const res = await fetch(`${API_BASE_URL}/tasks?${params.toString()}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch tasks');
  return res.json();
}

export async function createManualTask(
  payload: {
    title: string;
    description: string;
    workspaceId?: string;
    projectId?: string;
    assigneeId?: string;
    dueDate?: string;
    priority?: string;
  },
  token?: string
): Promise<TaskItem> {
  const res = await fetch(`${API_BASE_URL}/tasks`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({
      title: payload.title,
      description: payload.description,
      workspace_id: payload.workspaceId,
      project_id: payload.projectId,
      assignee_id: payload.assigneeId,
      due_date: payload.dueDate,
      priority: payload.priority || 'MEDIUM'
    })
  });
  if (!res.ok) throw new Error('Failed to create task');
  return res.json();
}

export async function completeTask(
  taskId: string,
  completionNote?: string,
  token?: string
): Promise<TaskItem> {
  const res = await fetch(`${API_BASE_URL}/tasks/${taskId}/complete`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ completion_note: completionNote })
  });
  if (!res.ok) throw new Error('Failed to complete task');
  return res.json();
}

export async function fetchTaskWhyProvenance(
  taskId: string,
  token?: string
): Promise<TaskProvenance> {
  const res = await fetch(`${API_BASE_URL}/tasks/${taskId}/why`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch task provenance');
  return res.json();
}
