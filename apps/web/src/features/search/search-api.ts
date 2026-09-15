import { apiClient } from '../../lib/api-client';

export interface SearchResultItem {
  id: string;
  source_type: 'document' | 'file' | 'message' | 'conversation' | 'project' | 'task' | 'decision' | 'insight';
  source_id?: string;
  type?: string;
  title: string;
  snippet: string;
  location?: string;
  author_name?: string;
  workspace_name?: string;
  organization_name?: string;
  created_at: string;
  updated_at?: string;
  deep_link?: string;
  score?: number;
  metadata?: Record<string, any>;
}

export interface SearchResponse {
  query: string;
  total_hits: number;
  total_results?: number;
  page: number;
  limit: number;
  total_pages: number;
  query_time_ms: number;
  facets: Record<string, number>;
  results: SearchResultItem[];
  items?: SearchResultItem[];
}

export interface AutocompleteSuggestion {
  id: string;
  title: string;
  type: string;
  workspace_id?: string;
}

export async function globalSearch(
  query: string,
  organizationId?: string,
  workspaceId?: string,
  entityType: string = 'all',
  token?: string
): Promise<SearchResponse> {
  if (!query || query.trim().length < 1) {
    return {
      query: '',
      total_hits: 0,
      total_results: 0,
      page: 1,
      limit: 20,
      total_pages: 0,
      query_time_ms: 0,
      facets: {},
      results: [],
      items: []
    };
  }

  const params: Record<string, any> = { q: query.trim(), type: entityType };
  if (organizationId) params.organization_id = organizationId;
  if (workspaceId && workspaceId !== 'all') params.workspace_id = workspaceId;

  const headers: Record<string, string> = {};
  if (organizationId) headers['X-Organization-ID'] = organizationId;
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await apiClient.get('/search', { params, headers });
  const data = res.data;
  const rawItems = data.items || data.results || [];
  
  // Normalize fields for UI compatibility
  const normalizedResults: SearchResultItem[] = rawItems.map((r: any) => ({
    id: String(r.id),
    source_type: r.source_type || r.type || r.entity_type || 'document',
    source_id: r.source_id || r.entity_id || String(r.id),
    type: r.source_type || r.type || r.entity_type || 'document',
    title: r.title || 'Untitled',
    snippet: r.snippet || r.excerpt || '',
    location: r.location || r.workspace_name || r.organization_name || 'Workspace',
    author_name: r.author_name,
    created_at: r.created_at || new Date().toISOString(),
    updated_at: r.updated_at,
    deep_link: r.deep_link,
    score: r.score || 1.0,
    metadata: r.metadata || {}
  }));

  const totalHits = data.total_results ?? data.total_hits ?? normalizedResults.length;

  return {
    query: query,
    total_hits: totalHits,
    total_results: totalHits,
    page: data.page || 1,
    limit: data.limit || 20,
    total_pages: data.total_pages || 1,
    query_time_ms: data.query_time_ms || 10,
    facets: data.facets || {},
    results: normalizedResults,
    items: normalizedResults
  };
}

export async function getAutocompleteSuggestions(
  query: string,
  organizationId?: string,
  token?: string
): Promise<AutocompleteSuggestion[]> {
  if (!query || query.trim().length < 1) return [];
  const params: Record<string, any> = { q: query.trim() };
  if (organizationId) params.organization_id = organizationId;

  const headers: Record<string, string> = {};
  if (organizationId) headers['X-Organization-ID'] = organizationId;
  if (token) headers['Authorization'] = `Bearer ${token}`;

  try {
    const res = await apiClient.get('/search/suggestions', { params, headers });
    const data = res.data;
    return (data || []).map((s: any, idx: number) => ({
      id: String(s.id || idx),
      title: s.title || query,
      type: (s.entity_type || s.type || 'DOCUMENT').toUpperCase()
    }));
  } catch {
    return [];
  }
}

export async function getRecentSearches(organizationId?: string, token?: string): Promise<string[]> {
  const params: Record<string, any> = {};
  if (organizationId) params.organization_id = organizationId;

  const headers: Record<string, string> = {};
  if (organizationId) headers['X-Organization-ID'] = organizationId;
  if (token) headers['Authorization'] = `Bearer ${token}`;

  try {
    const res = await apiClient.get('/search/recent', { params, headers });
    const data = res.data;
    return (data || []).map((item: any) => typeof item === 'string' ? item : item.query);
  } catch {
    return [];
  }
}

export async function clearSearchHistory(token?: string): Promise<boolean> {
  return true;
}
