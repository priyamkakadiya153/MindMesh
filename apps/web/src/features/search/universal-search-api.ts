const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface UniversalSearchResultItem {
  id: string;
  entity_type: string;
  entity_id: string;
  title: string;
  excerpt: string;
  project_name?: string;
  source_type: string;
  governance_status: string;
  relevance_reason: string;
}

export interface UniversalSearchResponse {
  query: string;
  intent: string;
  target_entity?: string;
  total_results: number;
  results: UniversalSearchResultItem[];
}

export interface TypeaheadSuggestion {
  title: string;
  entity_type: string;
}

export async function executeUniversalSearch(
  query: string,
  entityFilter: string = 'ALL',
  workspaceId?: string,
  projectId?: string,
  token?: string
): Promise<UniversalSearchResponse> {
  const params = new URLSearchParams({ q: query, entity_filter: entityFilter });
  if (workspaceId) params.append('workspace_id', workspaceId);
  if (projectId) params.append('project_id', projectId);

  const res = await fetch(`${API_BASE_URL}/search/universal?${params.toString()}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to execute universal search');
  return res.json();
}

export async function fetchTypeaheadSuggestions(
  query: string,
  token?: string
): Promise<TypeaheadSuggestion[]> {
  const res = await fetch(`${API_BASE_URL}/search/suggestions?q=${encodeURIComponent(query)}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch typeahead suggestions');
  return res.json();
}
