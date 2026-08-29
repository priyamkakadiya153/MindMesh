const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface EvidenceItem {
  source_type: string;
  title: string;
  snippet: string;
  authority_score: number;
  freshness: string;
  url_link: string;
}

export interface RecommendedAction {
  action_type: string;
  label: string;
  payload: Record<string, any>;
}

export interface UniversalAnswerResponse {
  intent_type: string;
  scope: string;
  answer_text: string;
  confidence: string;
  evidence: EvidenceItem[];
  recommended_actions: RecommendedAction[];
  freshness_timestamp: string;
}

export interface FileIntelligenceResponse {
  file_name: string;
  file_type: string;
  native_visual_preview_supported: boolean;
  preview_explanation?: string;
  extracted_intelligence: Record<string, any>;
  related_knowledge?: Array<Record<string, any>>;
}

export interface ContextSourcesResponse {
  organization_id: string;
  available_scopes: Array<{
    scope: string;
    count: number;
    label: string;
  }>;
}

export async function queryUniversalInterface(
  rawPrompt: string,
  activeResourceId?: string,
  token?: string
): Promise<UniversalAnswerResponse> {
  const res = await fetch(`${API_BASE_URL}/universal-interface/query`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ raw_prompt: rawPrompt, active_resource_id: activeResourceId })
  });
  if (!res.ok) throw new Error('Universal query failed');
  return res.json();
}

export async function fetchFileIntelligence(
  fileName: string,
  fileMime: string,
  token?: string
): Promise<FileIntelligenceResponse> {
  const res = await fetch(`${API_BASE_URL}/universal-interface/file-intelligence`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ file_name: fileName, file_mime: fileMime })
  });
  if (!res.ok) throw new Error('File intelligence fetch failed');
  return res.json();
}

export async function convertAnswerToAction(
  actionType: string,
  payload: Record<string, any>,
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/universal-interface/convert-action`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ action_type: actionType, payload })
  });
  if (!res.ok) throw new Error('Action conversion failed');
  return res.json();
}

export async function fetchAvailableContextSources(token?: string): Promise<ContextSourcesResponse> {
  const res = await fetch(`${API_BASE_URL}/universal-interface/context-sources`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch context sources');
  return res.json();
}
