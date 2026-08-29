const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface SearchResultItem {
  id: string;
  title: string;
  entity_type: string;
  snippet: string;
  project_name: string;
  authority_status: 'CURRENT_GOVERNED' | 'SUPERSEDED' | 'ACTIVE' | 'COMPLETED' | string;
  relevance_score: number;
  explanation: string;
  has_conflict?: boolean;
  conflict_summary?: string;
  created_at: string;
}

export interface SearchQueryResponse {
  query: str;
  mode: string;
  total_results: number;
  grouped_results: Record<string, SearchResultItem[]>;
  results: SearchResultItem[];
  has_contradictions: boolean;
  contradiction_summary?: string;
}

export interface AutocompleteItem {
  label: string;
  type: string;
  id: string;
}

export interface CompareResultsResponse {
  item_a: { id: string; title: string; value: string; status: string };
  item_b: { id: string; title: string; value: string; status: string };
  comparison_summary: string;
}

export async function executeSearch(
  query: string,
  mode: string = 'HYBRID',
  projectId?: string,
  entityTypes?: string[],
  token?: string
): Promise<SearchQueryResponse> {
  const res = await fetch(`${API_BASE_URL}/search/query`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({
      query,
      mode,
      project_id: projectId,
      entity_types: entityTypes
    })
  });
  if (!res.ok) throw new Error('Failed to execute search query');
  return res.json();
}

export async function fetchAutocompleteSuggestions(
  prefix: string = 'auth',
  token?: string
): Promise<AutocompleteItem[]> {
  const params = new URLSearchParams({ prefix });
  const res = await fetch(`${API_BASE_URL}/search/autocomplete?${params.toString()}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch autocomplete suggestions');
  return res.json();
}

export async function compareResultItems(
  itemIdA: string,
  itemIdB: string,
  token?: string
): Promise<CompareResultsResponse> {
  const res = await fetch(`${API_BASE_URL}/search/compare`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ item_id_a: itemIdA, item_id_b: itemIdB })
  });
  if (!res.ok) throw new Error('Failed to compare result items');
  return res.json();
}

export async function fetchSearchFacets(
  token?: string
): Promise<Record<string, number>> {
  const res = await fetch(`${API_BASE_URL}/search/facets`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch search facets');
  return res.json();
}

export async function rebuildSearchIndex(
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/search/rebuild-index`, {
    method: 'POST',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to rebuild search index');
  return res.json();
}
