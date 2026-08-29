import {
  CognitiveAgent,
  CognitiveAgentCreate,
  CognitiveAgentUpdate,
  CognitiveAgentExecution
} from '../../../types/cognitive-agent';

const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string, orgId?: string) {
  const authToken = token || localStorage.getItem('token') || localStorage.getItem('mindmesh_token') || '';
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
  if (orgId) {
    headers['X-Organization-ID'] = orgId;
  }
  return headers;
}

export async function fetchCognitiveAgents(
  token: string,
  orgId: string,
  workspaceId?: string,
  includeArchived: boolean = false
): Promise<CognitiveAgent[]> {
  const params = new URLSearchParams();
  if (workspaceId) params.append('workspace_id', workspaceId);
  if (includeArchived) params.append('include_archived', 'true');

  const queryString = params.toString() ? `?${params.toString()}` : '';
  const res = await fetch(`${API_BASE_URL}/cognitive-agents${queryString}`, {
    method: 'GET',
    headers: getAuthHeaders(token, orgId)
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to fetch Cognitive Agents');
  }

  return res.json();
}

export async function fetchCognitiveAgent(
  token: string,
  orgId: string,
  agentId: string
): Promise<CognitiveAgent> {
  const res = await fetch(`${API_BASE_URL}/cognitive-agents/${agentId}`, {
    method: 'GET',
    headers: getAuthHeaders(token, orgId)
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to fetch Cognitive Agent');
  }

  return res.json();
}

export async function createCognitiveAgent(
  token: string,
  orgId: string,
  data: CognitiveAgentCreate
): Promise<CognitiveAgent> {
  const res = await fetch(`${API_BASE_URL}/cognitive-agents`, {
    method: 'POST',
    headers: getAuthHeaders(token, orgId),
    body: JSON.stringify(data)
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to create Cognitive Agent');
  }

  return res.json();
}

export async function updateCognitiveAgent(
  token: string,
  orgId: string,
  agentId: string,
  data: CognitiveAgentUpdate
): Promise<CognitiveAgent> {
  const res = await fetch(`${API_BASE_URL}/cognitive-agents/${agentId}`, {
    method: 'PATCH',
    headers: getAuthHeaders(token, orgId),
    body: JSON.stringify(data)
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to update Cognitive Agent');
  }

  return res.json();
}

export async function archiveCognitiveAgent(
  token: string,
  orgId: string,
  agentId: string
): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/cognitive-agents/${agentId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(token, orgId)
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to archive Cognitive Agent');
  }
}

export async function fetchKnowledgeOptions(
  token: string,
  orgId: string,
  workspaceId: string
): Promise<{
  projects: { id: string; name: string; description?: string; status?: string }[];
  documents: { id: string; title: string; filename: string; mime_type: string; size: number; project_id?: string }[];
  conversations: { id: string; title: string; conversation_type: string; created_at?: string }[];
}> {
  const res = await fetch(`${API_BASE_URL}/cognitive-agents/knowledge-options?workspace_id=${workspaceId}`, {
    method: 'GET',
    headers: getAuthHeaders(token, orgId)
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to fetch knowledge options');
  }

  return res.json();
}

export async function updateAgentKnowledgeScope(
  token: string,
  orgId: string,
  agentId: string,
  scopeData: any
): Promise<CognitiveAgent> {
  const res = await fetch(`${API_BASE_URL}/cognitive-agents/${agentId}/knowledge-scope`, {
    method: 'PUT',
    headers: getAuthHeaders(token, orgId),
    body: JSON.stringify(scopeData)
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to update knowledge scope');
  }

  return res.json();
}

export async function fetchAgentKnowledgePreview(
  token: string,
  orgId: string,
  agentId: string
): Promise<{
  scope_type: string;
  accessible_projects: any[];
  accessible_documents: any[];
  accessible_conversations: any[];
  message: string;
}> {
  const res = await fetch(`${API_BASE_URL}/cognitive-agents/${agentId}/knowledge-preview`, {
    method: 'POST',
    headers: getAuthHeaders(token, orgId)
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to fetch knowledge preview');
  }

  return res.json();
}

export async function executeCognitiveAgent(
  token: string,
  orgId: string,
  agentId: string
): Promise<{ execution: CognitiveAgentExecution; output: CognitiveAgentOutput | null }> {
  const res = await fetch(`${API_BASE_URL}/cognitive-agents/${agentId}/execute`, {
    method: 'POST',
    headers: getAuthHeaders(token, orgId)
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to execute Cognitive Agent');
  }

  return res.json();
}

export async function fetchCognitiveAgentExecutions(
  token: string,
  orgId: string,
  agentId: string
): Promise<CognitiveAgentExecution[]> {
  const res = await fetch(`${API_BASE_URL}/cognitive-agents/${agentId}/executions`, {
    method: 'GET',
    headers: getAuthHeaders(token, orgId)
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to fetch agent execution history');
  }

  return res.json();
}

export async function fetchAgentTriggers(
  token: string,
  orgId: string,
  agentId: string
): Promise<CognitiveAgentTriggerRecord[]> {
  const res = await fetch(`${API_BASE_URL}/cognitive-agents/${agentId}/triggers`, {
    method: 'GET',
    headers: getAuthHeaders(token, orgId)
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to fetch agent triggers');
  }

  return res.json();
}

export async function createAgentTrigger(
  token: string,
  orgId: string,
  agentId: string,
  payload: any
): Promise<CognitiveAgentTriggerRecord> {
  const res = await fetch(`${API_BASE_URL}/cognitive-agents/${agentId}/triggers`, {
    method: 'POST',
    headers: getAuthHeaders(token, orgId),
    body: JSON.stringify(payload)
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to create agent trigger');
  }

  return res.json();
}

export async function pauseAgentTrigger(
  token: string,
  orgId: string,
  agentId: string,
  triggerId: string
): Promise<CognitiveAgentTriggerRecord> {
  const res = await fetch(`${API_BASE_URL}/cognitive-agents/${agentId}/triggers/${triggerId}/pause`, {
    method: 'POST',
    headers: getAuthHeaders(token, orgId)
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to pause trigger');
  }

  return res.json();
}

export async function resumeAgentTrigger(
  token: string,
  orgId: string,
  agentId: string,
  triggerId: string
): Promise<CognitiveAgentTriggerRecord> {
  const res = await fetch(`${API_BASE_URL}/cognitive-agents/${agentId}/triggers/${triggerId}/resume`, {
    method: 'POST',
    headers: getAuthHeaders(token, orgId)
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to resume trigger');
  }

  return res.json();
}

export async function deleteAgentTrigger(
  token: string,
  orgId: string,
  agentId: string,
  triggerId: string
): Promise<boolean> {
  const res = await fetch(`${API_BASE_URL}/cognitive-agents/${agentId}/triggers/${triggerId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(token, orgId)
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to delete trigger');
  }

  return true;
}

export async function fetchAgentOutputs(
  token: string,
  orgId: string,
  agentId: string
): Promise<CognitiveAgentOutputRecord[]> {
  const res = await fetch(`${API_BASE_URL}/cognitive-agents/${agentId}/outputs`, {
    method: 'GET',
    headers: getAuthHeaders(token, orgId)
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to fetch agent outputs');
  }

  return res.json();
}

export async function fetchAgentOutputDetail(
  token: string,
  orgId: string,
  agentId: string,
  outputId: string
): Promise<CognitiveAgentOutputRecord> {
  const res = await fetch(`${API_BASE_URL}/cognitive-agents/${agentId}/outputs/${outputId}`, {
    method: 'GET',
    headers: getAuthHeaders(token, orgId)
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to fetch agent output detail');
  }

  return res.json();
}

export async function fetchExecutionOutput(
  token: string,
  orgId: string,
  agentId: string,
  executionId: string
): Promise<CognitiveAgentOutputRecord | null> {
  const res = await fetch(`${API_BASE_URL}/cognitive-agents/${agentId}/executions/${executionId}/output`, {
    method: 'GET',
    headers: getAuthHeaders(token, orgId)
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to fetch execution output');
  }

  return res.json();
}

export async function fetchAgentMemories(
  token: string,
  orgId: string,
  agentId: string
): Promise<any[]> {
  const res = await fetch(`${API_BASE_URL}/cognitive-agents/${agentId}/memories`, {
    method: 'GET',
    headers: getAuthHeaders(token, orgId)
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to fetch agent memories');
  }

  return res.json();
}

export async function deleteAgentMemory(
  token: string,
  orgId: string,
  agentId: string,
  memoryId: string
): Promise<boolean> {
  const res = await fetch(`${API_BASE_URL}/cognitive-agents/${agentId}/memories/${memoryId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(token, orgId)
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to delete agent memory');
  }

  const data = await res.json();
  return data.success;
}




