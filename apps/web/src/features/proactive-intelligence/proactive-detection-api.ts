import axios from 'axios';

const API_BASE = '/api/v1/proactive/action-detection';

export interface ProactiveSuggestionItem {
  id: string;
  organization_id?: string;
  workspace_id?: string;
  source_type: string;
  conversation_id: string;
  message_id?: string;
  detected_action_type: string;
  title: string;
  description?: string;
  deadline?: string;
  normalized_deadline?: string;
  assignee_name?: string;
  confidence: number;
  confidence_level: string;
  status: string;
  source_label?: string;
  source_content?: string;
  pending_proposal?: any;
  agent_id?: string;
  agent_execution_id?: string;
  agent_output_id?: string;
  created_at: string;
}

export interface DetectSignalPayload {
  text: string;
  source_type: string;
  conversation_id: string;
  message_id?: string;
  sender_name?: string;
  history?: Array<{ sender?: string; content: string }>;
  workspace_id?: string;
}

export async function detectActionableSignal(
  token: string,
  payload: DetectSignalPayload
): Promise<{ detected: boolean; duplicate?: boolean; suggestion?: ProactiveSuggestionItem }> {
  try {
    const res = await axios.post(`${API_BASE}/detect`, payload, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return res.data;
  } catch (err) {
    console.error('Failed to run proactive signal detection:', err);
    return { detected: false };
  }
}

export async function fetchProactiveSuggestions(
  token: string,
  conversationId?: string,
  sourceType?: string,
  statusFilter?: string
): Promise<ProactiveSuggestionItem[]> {
  try {
    const res = await axios.get(`${API_BASE}/suggestions`, {
      headers: { Authorization: `Bearer ${token}` },
      params: {
        conversation_id: conversationId,
        source_type: sourceType,
        status_filter: statusFilter || 'DETECTED'
      }
    });
    return res.data;
  } catch (err) {
    console.error('Failed to fetch proactive suggestions:', err);
    return [];
  }
}

export async function fetchPendingSuggestionsCount(token: string): Promise<number> {
  try {
    const res = await axios.get(`${API_BASE}/count`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return res.data.pending_count || 0;
  } catch (err) {
    console.error('Failed to fetch pending suggestions count:', err);
    return 0;
  }
}

export async function dismissProactiveSuggestion(
  token: string,
  suggestionId: string
): Promise<boolean> {
  try {
    await axios.post(`${API_BASE}/suggestions/${suggestionId}/dismiss`, {}, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return true;
  } catch (err) {
    console.error('Failed to dismiss proactive suggestion:', err);
    return false;
  }
}

export async function promoteProactiveSuggestion(
  token: string,
  suggestionId: string,
  targetActionType: 'TASK' | 'REMINDER' = 'TASK'
): Promise<{ status: string; proposal: any }> {
  try {
    const res = await axios.post(`${API_BASE}/suggestions/${suggestionId}/promote`, {
      target_action_type: targetActionType
    }, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return res.data;
  } catch (err) {
    console.error('Failed to promote proactive suggestion:', err);
    throw err;
  }
}

export async function cancelProactiveProposal(
  token: string,
  suggestionId: string
): Promise<boolean> {
  try {
    await axios.post(`${API_BASE}/suggestions/${suggestionId}/cancel_proposal`, {}, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return true;
  } catch (err) {
    console.error('Failed to cancel proactive proposal:', err);
    return false;
  }
}
