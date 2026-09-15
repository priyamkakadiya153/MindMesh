import { apiClient } from '../../lib/api-client';

const API_PATH = '/proactive/action-detection';

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
  token?: string,
  payload?: DetectSignalPayload
): Promise<{ detected: boolean; duplicate?: boolean; suggestion?: ProactiveSuggestionItem }> {
  try {
    const res = await apiClient.post(`${API_PATH}/detect`, payload);
    return res.data;
  } catch (err) {
    console.error('Failed to run proactive signal detection:', err);
    return { detected: false };
  }
}

export async function fetchProactiveSuggestions(
  token?: string,
  conversationId?: string,
  sourceType?: string,
  statusFilter?: string
): Promise<ProactiveSuggestionItem[]> {
  try {
    const res = await apiClient.get(`${API_PATH}/suggestions`, {
      params: {
        conversation_id: conversationId,
        source_type: sourceType,
        status_filter: statusFilter || 'DETECTED'
      }
    });
    const data = res.data;
    if (Array.isArray(data)) {
      return data;
    }
    if (data && Array.isArray(data.items)) {
      return data.items;
    }
    if (data && Array.isArray(data.suggestions)) {
      return data.suggestions;
    }
    return [];
  } catch (err) {
    console.error('Failed to fetch proactive suggestions:', err);
    return [];
  }
}

export async function fetchPendingSuggestionsCount(token?: string): Promise<number> {
  try {
    const res = await apiClient.get(`${API_PATH}/count`);
    return res.data?.pending_count || 0;
  } catch (err) {
    console.error('Failed to fetch pending suggestions count:', err);
    return 0;
  }
}

export async function dismissProactiveSuggestion(
  token?: string,
  suggestionId?: string
): Promise<boolean> {
  try {
    await apiClient.post(`${API_PATH}/suggestions/${suggestionId}/dismiss`, {});
    return true;
  } catch (err) {
    console.error('Failed to dismiss proactive suggestion:', err);
    return false;
  }
}

export async function promoteProactiveSuggestion(
  token: string | undefined,
  suggestionId: string,
  targetActionType: 'TASK' | 'REMINDER' = 'TASK'
): Promise<{ status: string; proposal: any }> {
  try {
    const res = await apiClient.post(`${API_PATH}/suggestions/${suggestionId}/promote`, {
      target_action_type: targetActionType
    });
    return res.data;
  } catch (err) {
    console.error('Failed to promote proactive suggestion:', err);
    throw err;
  }
}

export async function cancelProactiveProposal(
  token?: string,
  suggestionId?: string
): Promise<boolean> {
  try {
    await apiClient.post(`${API_PATH}/suggestions/${suggestionId}/cancel_proposal`, {});
    return true;
  } catch (err) {
    console.error('Failed to cancel proactive proposal:', err);
    return false;
  }
}
