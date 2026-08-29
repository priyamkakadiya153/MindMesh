const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface ConversationSummaryResponse {
  id: string;
  chat_id: string;
  summary_type: string;
  summary_text: string;
  topics: string[];
  timeline: Array<{ time: string; topic: string; summary: string }>;
  open_questions?: string[];
  blockers?: Array<{ blocker: string }>;
}

export interface ExtractedKnowledgeItem {
  id: string;
  chat_id: string;
  message_id?: string;
  item_type: 'DECISION' | 'TASK' | 'QUESTION' | 'BLOCKER' | 'COMMITMENT' | string;
  title: string;
  description?: string;
  assignee_name?: string;
  due_date_str?: string;
  confidence: number;
  status: 'AI_DETECTED' | 'CONFIRMED' | 'REJECTED' | string;
  promoted_entity_type?: string;
  promoted_entity_id?: string;
}

export interface MeetingNotesResponse {
  chat_id: string;
  title: string;
  notes_markdown: string;
}

export async function fetchConversationSummary(
  chatId: string,
  summaryType: string = 'QUICK',
  token?: string
): Promise<ConversationSummaryResponse> {
  const res = await fetch(`${API_BASE_URL}/conversations/${chatId}/summary?summary_type=${summaryType}`, {
    method: 'POST',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch conversation summary');
  return res.json();
}

export async function fetchConversationKnowledge(
  chatId: string,
  token?: string
): Promise<ExtractedKnowledgeItem[]> {
  const res = await fetch(`${API_BASE_URL}/conversations/${chatId}/knowledge`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch conversation knowledge');
  return res.json();
}

export async function promoteItemToProject(
  chatId: string,
  itemId: string,
  projectId: string,
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/conversations/${chatId}/promote`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ item_id: itemId, project_id: projectId })
  });
  if (!res.ok) throw new Error('Failed to promote item to project');
  return res.json();
}

export async function generateMeetingNotes(
  chatId: string,
  title?: string,
  token?: string
): Promise<MeetingNotesResponse> {
  const res = await fetch(`${API_BASE_URL}/conversations/${chatId}/meeting-notes`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ title })
  });
  if (!res.ok) throw new Error('Failed to generate meeting notes');
  return res.json();
}
