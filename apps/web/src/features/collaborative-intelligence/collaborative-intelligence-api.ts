const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface ConversationContextResponse {
  conversation_id: string;
  project_name: string;
  participants: string[];
  related_files: string[];
  related_tasks: string[];
  related_decisions: string[];
  status: string;
}

export interface SuggestionItem {
  suggestion_id: string;
  type: 'SUGGESTED_DECISION' | 'SUGGESTED_TASK' | 'OPEN_QUESTION' | string;
  title: string;
  reason?: string;
  source_message?: string;
  author?: string;
  assignee?: string;
  status: string;
}

export interface DetectSuggestionsResponse {
  conversation_id: string;
  total_suggestions: number;
  suggestions: SuggestionItem[];
}

export interface TeamDigestResponse {
  project_name: string;
  team_members: number;
  recent_decisions: Array<{ title: string; source: string }>;
  open_work: Array<{ title: string; status: string }>;
  unresolved_questions: string[];
}

export interface ReviewRoomResponse {
  room_id: string;
  title: string;
  conflicting_sources: string[];
  status: string;
  created_at: string;
}

export async function fetchConversationContext(
  conversationId: string,
  token?: string
): Promise<ConversationContextResponse> {
  const res = await fetch(`${API_BASE_URL}/collaboration/conversation-context/${conversationId}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch conversation context');
  return res.json();
}

export async function detectSuggestions(
  conversationId: string,
  token?: string
): Promise<DetectSuggestionsResponse> {
  const res = await fetch(`${API_BASE_URL}/collaboration/detect-suggestions?conversation_id=${conversationId}`, {
    method: 'POST',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to detect suggestions');
  return res.json();
}

export async function confirmDecision(
  suggestionId: string,
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/collaboration/confirm-decision`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ suggestion_id: suggestionId })
  });
  if (!res.ok) throw new Error('Failed to confirm decision');
  return res.json();
}

export async function confirmTask(
  suggestionId: string,
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/collaboration/confirm-task`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ suggestion_id: suggestionId })
  });
  if (!res.ok) throw new Error('Failed to confirm task');
  return res.json();
}

export async function fetchTeamDigest(
  token?: string
): Promise<TeamDigestResponse> {
  const res = await fetch(`${API_BASE_URL}/collaboration/team-digest`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch team digest');
  return res.json();
}

export async function createReviewRoom(
  title: string,
  conflictingSources: string[],
  token?: string
): Promise<ReviewRoomResponse> {
  const res = await fetch(`${API_BASE_URL}/collaboration/review-room`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ title, conflicting_sources: conflictingSources })
  });
  if (!res.ok) throw new Error('Failed to create review room');
  return res.json();
}

export async function resolveReview(
  roomId: string,
  resolutionNotes: string,
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/collaboration/resolve-review`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ room_id: roomId, resolution_notes: resolutionNotes })
  });
  if (!res.ok) throw new Error('Failed to resolve review');
  return res.json();
}
