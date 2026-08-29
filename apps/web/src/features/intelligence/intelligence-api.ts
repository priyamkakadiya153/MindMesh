const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface IntelligenceSignalItem {
  id: string;
  signal_type: 'NEW_DECISION' | 'BLOCKED_TASK' | 'OVERDUE_TASK' | 'OPEN_QUESTION' | 'KNOWLEDGE_CONFLICT' | 'STALE_KNOWLEDGE' | 'DECISION_AFFECTS_TASK' | 'PROJECT_ATTENTION' | string;
  priority: 'LOW' | 'NORMAL' | 'HIGH';
  title: string;
  summary: string;
  status: 'ACTIVE' | 'READ' | 'DISMISSED' | 'RESOLVED';
  source_type?: string;
  source_id?: string;
  created_at: string;
  metadata?: Record<string, any>;
}

export async function fetchImportantSignals(
  workspaceId?: string,
  token?: string
): Promise<IntelligenceSignalItem[]> {
  const params = new URLSearchParams();
  if (workspaceId) params.append('workspace_id', workspaceId);

  const res = await fetch(`${API_BASE_URL}/intelligence/important?${params.toString()}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch proactive intelligence signals');
  return res.json();
}

export async function dismissSignal(
  signalId: string,
  token?: string
): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/intelligence/signals/${signalId}/dismiss`, {
    method: 'POST',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to dismiss signal');
}
