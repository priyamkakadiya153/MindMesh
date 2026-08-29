import axios from 'axios';

const API_BASE = '/api/v1';

export interface CitationData {
  id?: string;
  document?: string;
  document_id: string;
  chunk_id?: string;
  page?: number;
  page_number?: number;
  section?: string;
  confidence?: number;
  score?: number;
}

export interface ActionProposalData {
  proposal_id: string;
  intent_type: string;
  title: string;
  description?: string;
  parameters: Record<string, any>;
  workspace_id?: string;
  user_id?: string;
  confirmation_required: boolean;
  status: string;
  clarification_prompt?: string;
}

export interface ActionResultData {
  status: string;
  action_type: string;
  entity_type?: string;
  entity_id?: string;
  entity_name?: string;
  message: string;
  error_code?: string;
  metadata?: Record<string, any>;
}

export interface ChatMessage {
  id: string;
  conversation_id?: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  status?: 'DRAFT' | 'SENDING' | 'SENT' | 'GENERATING' | 'STREAMING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  content_type?: string;
  model?: string;
  token_count?: number;
  latency_ms?: number;
  metadata?: Record<string, any>;
  created_at?: string;
  citations?: CitationData[];
  action_proposal?: ActionProposalData;
  action_result?: ActionResultData;
}

export interface ConversationItem {
  id: string;
  organization_id: string;
  workspace_id?: string;
  user_id?: string;
  title: string;
  description?: string;
  is_pinned: boolean;
  status: string;
  last_message_at?: string;
  created_at: string;
  updated_at: string;
}

export interface PaginatedConversations {
  conversations: ConversationItem[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface SendChatPayload {
  query: string;
  chat_id?: string;
  conversation_id?: string;
  workspace_id?: string;
  organization_id?: string;
  org_id?: string;
  project_id?: string;
  idempotency_key?: string;
  client_message_id?: string;
  provider?: string;
  model?: string;
  temperature?: number;
  max_tokens?: number;
  system_prompt?: string;
  stream?: boolean;
}

export interface AIGatewayResponse {
  response_id: string;
  request_id: string;
  conversation_id?: string;
  user_message_id?: string;
  content: string;
  status: 'PENDING' | 'GENERATING' | 'STREAMING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  model: string;
  provider: string;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
    estimated_cost_usd: number;
  };
  sources?: any[];
  timing?: {
    total_latency_ms: number;
    provider_latency_ms: number;
  };
  error?: {
    code: string;
    message: string;
    details?: any;
  };
}

export interface AIGatewayHealth {
  status: 'AVAILABLE' | 'DEGRADED' | 'UNAVAILABLE';
  provider: string;
  model: string;
  timeout_seconds: number;
  prompt_version: string;
}

// ---------------- CONVERSATION MANAGEMENT APIs ----------------

export async function createConversation(
  token: string,
  payload: { title?: string; description?: string; workspace_id?: string }
): Promise<ConversationItem> {
  const res = await axios.post(`${API_BASE}/chat/conversations`, payload, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return res.data;
}

export async function fetchConversations(
  token: string,
  params?: { workspace_id?: string; is_pinned?: boolean; q?: string; page?: number; limit?: number }
): Promise<PaginatedConversations> {
  const res = await axios.get(`${API_BASE}/chat/conversations`, {
    headers: { Authorization: `Bearer ${token}` },
    params
  });
  return res.data;
}

export async function fetchRecentConversations(
  token: string,
  workspace_id?: string
): Promise<ConversationItem[]> {
  const res = await axios.get(`${API_BASE}/chat/conversations/recent`, {
    headers: { Authorization: `Bearer ${token}` },
    params: { workspace_id }
  });
  return res.data;
}

export async function searchConversations(
  token: string,
  query: string,
  workspace_id?: string
): Promise<ConversationItem[]> {
  const res = await axios.get(`${API_BASE}/chat/conversations/search`, {
    headers: { Authorization: `Bearer ${token}` },
    params: { q: query, workspace_id }
  });
  return res.data;
}

export async function fetchConversationDetails(
  token: string,
  conversationId: string
): Promise<any> {
  const res = await axios.get(`${API_BASE}/chat/${conversationId}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return res.data;
}

export async function updateConversation(
  token: string,
  conversationId: string,
  payload: { title?: string; description?: string; is_pinned?: boolean; workspace_id?: string; settings?: Record<string, any> }
): Promise<any> {
  const res = await axios.patch(`${API_BASE}/chat/conversations/${conversationId}`, payload, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return res.data;
}

export async function pinConversation(
  token: string,
  conversationId: string,
  is_pinned: boolean
): Promise<ConversationItem> {
  const res = await axios.post(
    `${API_BASE}/chat/conversations/${conversationId}/pin`,
    { is_pinned },
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return res.data;
}

export async function deleteConversation(
  token: string,
  conversationId: string
): Promise<any> {
  const res = await axios.delete(`${API_BASE}/chat/conversations/${conversationId}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return res.data;
}

// ---------------- MESSAGE APIs ----------------

export async function fetchMessages(
  token: string,
  conversationId: string
): Promise<ChatMessage[]> {
  const res = await axios.get(`${API_BASE}/chat/conversations/${conversationId}/messages`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return res.data;
}

export async function createMessage(
  token: string,
  conversationId: string,
  payload: { content: string; role?: string; content_type?: string; model?: string; token_count?: number; latency_ms?: number; metadata?: Record<string, any> }
): Promise<ChatMessage> {
  const res = await axios.post(`${API_BASE}/chat/conversations/${conversationId}/messages`, payload, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return res.data;
}

export async function executeChat(
  token: string,
  payload: SendChatPayload
): Promise<any> {
  const res = await axios.post(`${API_BASE}/chat`, payload, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return res.data;
}

export async function deleteMessage(
  token: string,
  messageId: string
): Promise<any> {
  const res = await axios.delete(`${API_BASE}/chat/messages/${messageId}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return res.data;
}

export async function exportConversation(
  token: string,
  conversationId: string,
  format: 'markdown' | 'json' = 'markdown'
): Promise<Blob | any> {
  const res = await axios.post(
    `${API_BASE}/chat/export?conversation_id=${conversationId}`,
    { format },
    {
      headers: { Authorization: `Bearer ${token}` },
      responseType: format === 'markdown' ? 'blob' : 'json'
    }
  );
  return res.data;
}

export async function retryChatMessage(
  token: string,
  messageId: string
): Promise<AIGatewayResponse> {
  const res = await axios.post(`${API_BASE}/ai/gateway/messages/${messageId}/retry`, {}, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return res.data;
}

export async function regenerateChatMessage(
  token: string,
  messageId: string
): Promise<AIGatewayResponse> {
  const res = await axios.post(`${API_BASE}/ai/gateway/messages/${messageId}/regenerate`, {}, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return res.data;
}

export async function stopGeneration(
  token: string,
  conversationId: string
): Promise<any> {
  return cancelChatGeneration(token, conversationId);
}

export async function regenerateResponse(
  token: string,
  conversationId: string
): Promise<any> {
  const res = await axios.post(`${API_BASE}/ai/gateway/messages/${conversationId}/regenerate`, {}, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return res.data;
}

export async function cancelChatGeneration(
  token: string,
  conversationId: string
): Promise<any> {
  const res = await axios.post(`${API_BASE}/ai/gateway/conversations/${conversationId}/cancel`, {}, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return res.data;
}

export async function streamChatMessage(
  token: string,
  payload: SendChatPayload,
  handlers: {
    onToken?: (tokenText: string) => void;
    onSession?: (chatId: string) => void;
    onActionProposal?: (proposal: ActionProposalData) => void;
    onFinal?: (metadata: any) => void;
    onError?: (err: Error) => void;
    signal?: AbortSignal;
  }
): Promise<void> {
  const idempKey = payload.idempotency_key || payload.client_message_id || '';
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
    'X-Idempotency-Key': idempKey
  };
  if (payload.organization_id || payload.org_id) {
    headers['X-Organization-ID'] = (payload.organization_id || payload.org_id)!;
  }
  try {
    const response = await fetch(`${API_BASE}/ai/gateway/chat/stream`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        message: payload.query,
        conversation_id: payload.conversation_id || payload.chat_id,
        workspace_id: payload.workspace_id,
        idempotency_key: idempKey,
        provider: payload.provider,
        model: payload.model,
        temperature: payload.temperature,
        max_tokens: payload.max_tokens,
        system_prompt: payload.system_prompt,
        stream: true
      }),
      signal: handlers.signal
    });

    if (!response.ok) {
      throw new Error(`HTTP error ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error('ReadableStream not supported.');

    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    let finalPayload: any = null;
    let terminalSeen = false;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || !trimmed.startsWith('data: ')) continue;
        const jsonStr = trimmed.substring(6).trim();
        if (!jsonStr) continue;

        try {
          const evt = JSON.parse(jsonStr);
          if ((evt.type === 'START' || evt.type === 'session') && (evt.chat_id || evt.conversation_id)) {
            handlers.onSession?.(evt.chat_id || evt.conversation_id);
          } else if (evt.type === 'action_proposal' && evt.action_proposal) {
            finalPayload = { ...finalPayload, action_proposal: evt.action_proposal };
            handlers.onActionProposal?.(evt.action_proposal);
          } else if ((evt.type === 'DELTA' || evt.type === 'TOKEN' || evt.type === 'token') && evt.content) {
            handlers.onToken?.(evt.content);
          } else if (evt.type === 'COMPLETE' || evt.type === 'final') {
            const proposal = evt.action_proposal || (evt.metadata && evt.metadata.action_proposal) || finalPayload?.action_proposal;
            finalPayload = { ...finalPayload, ...evt, action_proposal: proposal };
          } else if (evt.type === 'done') {
            terminalSeen = true;
          }
        } catch (e) {
          // ignore chunk parse errors
        }
      }
    }

    handlers.onFinal?.(finalPayload || { type: 'final' });
  } catch (err: any) {
    if (err.name !== 'AbortError') {
      handlers.onError?.(err);
    }
  }
}

// ---------------- AI GATEWAY CLIENT APIs ----------------

export async function fetchGatewayHealth(): Promise<AIGatewayHealth> {
  const res = await axios.get(`${API_BASE}/ai/gateway/health`);
  return res.data;
}

export async function fetchGatewayModels(provider?: string): Promise<string[]> {
  const res = await axios.get(`${API_BASE}/ai/gateway/models`, { params: { provider } });
  return res.data;
}

export async function sendGatewayChat(
  token: string,
  payload: {
    message: string;
    conversation_id?: string;
    workspace_id?: string;
    idempotency_key?: string;
    provider?: string;
    model?: string;
    temperature?: number;
    max_tokens?: number;
    system_prompt?: string;
  }
): Promise<AIGatewayResponse> {
  const res = await axios.post(`${API_BASE}/ai/gateway/chat`, payload, {
    headers: {
      Authorization: `Bearer ${token}`,
      'X-Idempotency-Key': payload.idempotency_key || ''
    }
  });
  return res.data;
}

export async function confirmActionProposal(
  token: string,
  payload: { proposal_id: string; intent_type: string; parameters: Record<string, any>; confirm: boolean }
): Promise<ActionResultData> {
  const res = await axios.post(`${API_BASE}/actions/confirm`, payload, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return res.data;
}
