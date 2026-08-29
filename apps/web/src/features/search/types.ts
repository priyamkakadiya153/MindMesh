export interface UniversalSearchResultItem {
  id: string;
  entity_type: string;
  entity_id: string;
  title: string;
  snippet: string;
  workspace_id?: string;
  workspace_name?: string;
  organization_id?: string;
  organization_name?: string;
  owner_id?: string;
  tags: string[];
  metadata: Record<string, any>;
  created_at?: string;
  updated_at?: string;
  score: number;
}

export interface UniversalSearchResponse {
  results: UniversalSearchResultItem[];
  total_hits: number;
  page: number;
  limit: number;
  total_pages: number;
  query_time_ms: number;
  facets: Record<string, number>;
}

export interface AutocompleteSuggestion {
  id: string;
  title: string;
  type: string;
  workspace_id?: string;
}

export interface SearchHistoryItem {
  id: string;
  query: string;
  created_at: string;
}

export interface SearchFilters {
  query?: string;
  q?: string;
  type?: string;
  workspace?: string;
  workspace_id?: string;
  organization?: string;
  organization_id?: string;
  owner?: string;
  page?: number;
  limit?: number;
  sort?: 'most_relevant' | 'newest' | 'oldest' | 'alphabetical';
  status?: string;
  file_type?: string;
  tags?: string;
  date_from?: string;
  date_to?: string;
}
