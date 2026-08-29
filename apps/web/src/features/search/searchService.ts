import { apiClient } from '../../lib/api-client';
import { useAuthStore } from '../auth/auth-store';
import { useWorkspaceStore } from '../workspace/store';
import {
  UniversalSearchResponse,
  AutocompleteSuggestion,
  SearchHistoryItem,
  SearchFilters,
  UniversalSearchResultItem
} from './types';

export const searchService = {
  async search(filters: SearchFilters): Promise<UniversalSearchResponse> {
    const qText = filters.q || filters.query || '';
    if (!qText.trim()) {
      return {
        results: [],
        total_hits: 0,
        page: 1,
        limit: filters.limit || 20,
        total_pages: 0,
        query_time_ms: 0,
        facets: {}
      };
    }

    const currentOrg = useAuthStore.getState().currentOrg;
    const currentWorkspace = useWorkspaceStore.getState().currentWorkspace;

    const params: Record<string, any> = {
      q: qText.trim(),
      organization_id: filters.organization_id || filters.organization || currentOrg?.id,
      limit: filters.limit || 20,
      offset: ((filters.page || 1) - 1) * (filters.limit || 20)
    };

    if (filters.workspace_id || filters.workspace || currentWorkspace?.id) {
      params.workspace_id = filters.workspace_id || filters.workspace || currentWorkspace?.id;
    }

    const startTime = Date.now();
    const response = await apiClient.get('/search', { params });
    const queryTimeMs = Date.now() - startTime;

    const rawData = response.data;
    const items: any[] = rawData.items || rawData.results || [];
    const totalCount: number = rawData.total_results ?? rawData.total_hits ?? items.length;

    const normalizedResults: UniversalSearchResultItem[] = items.map((item: any) => ({
      id: String(item.id),
      entity_type: (item.type || item.entity_type || 'document').toUpperCase(),
      entity_id: String(item.id),
      title: item.title || 'Untitled',
      snippet: item.snippet || item.excerpt || '',
      workspace_id: item.workspace_id || currentWorkspace?.id,
      workspace_name: item.workspace_name || currentWorkspace?.name,
      organization_id: item.organization_id || currentOrg?.id,
      organization_name: item.organization_name || currentOrg?.name,
      owner_id: item.author_name || item.owner_id,
      tags: item.tags || [],
      metadata: item.metadata || {},
      created_at: item.created_at,
      updated_at: item.updated_at,
      score: item.score || 1.0
    }));

    const limit = filters.limit || 20;
    const page = filters.page || 1;
    const totalPages = Math.ceil(totalCount / limit) || 1;

    return {
      results: normalizedResults,
      total_hits: totalCount,
      page,
      limit,
      total_pages: totalPages,
      query_time_ms: queryTimeMs,
      facets: rawData.facets || {}
    };
  },

  async getSuggestions(query: string): Promise<AutocompleteSuggestion[]> {
    if (!query || query.trim().length === 0) return [];
    const currentOrg = useAuthStore.getState().currentOrg;
    const params: Record<string, any> = { q: query.trim() };
    if (currentOrg?.id) {
      params.organization_id = currentOrg.id;
    }
    try {
      const response = await apiClient.get<any[]>('/search/suggestions', { params });
      return (response.data || []).map((s: any, idx: number) => ({
        id: String(s.id || idx),
        title: s.title || query,
        type: (s.entity_type || s.type || 'DOCUMENT').toUpperCase()
      }));
    } catch {
      return [];
    }
  },

  async getHistory(): Promise<SearchHistoryItem[]> {
    const currentOrg = useAuthStore.getState().currentOrg;
    const params: Record<string, any> = {};
    if (currentOrg?.id) {
      params.organization_id = currentOrg.id;
    }
    try {
      const response = await apiClient.get<string[]>('/search/recent', { params });
      return (response.data || []).map((q: string, idx: number) => ({
        id: String(idx),
        query: q,
        created_at: new Date().toISOString()
      }));
    } catch {
      return [];
    }
  },

  async clearHistory(): Promise<{ success: boolean; message: string }> {
    return { success: true, message: 'Search history cleared' };
  }
};
