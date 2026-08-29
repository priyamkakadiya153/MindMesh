import { useState, useEffect, useCallback, useRef } from 'react';
import { searchService } from './searchService';
import {
  UniversalSearchResponse,
  AutocompleteSuggestion,
  SearchHistoryItem,
  SearchFilters,
} from './types';

export function useUniversalSearch() {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [filters, setFilters] = useState<SearchFilters>({
    type: 'all',
    page: 1,
    limit: 20,
    sort: 'most_relevant',
  });

  const [searchResponse, setSearchResponse] = useState<UniversalSearchResponse | null>(null);
  const [suggestions, setSuggestions] = useState<AutocompleteSuggestion[]>([]);
  const [history, setHistory] = useState<SearchHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Debounce query input (~300ms)
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query);
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  // Global Ctrl+K / Cmd+K keyboard shortcut and custom event listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen((prev) => !prev);
      } else if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    };

    const handleCustomOpen = () => {
      setIsOpen(true);
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('open-universal-search', handleCustomOpen);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('open-universal-search', handleCustomOpen);
    };
  }, [isOpen]);


  // Load history when modal opens or on mount
  const loadHistory = useCallback(async () => {
    try {
      const data = await searchService.getHistory();
      setHistory(data);
    } catch (err) {
      console.warn('Failed to load search history', err);
    }
  }, []);

  useEffect(() => {
    if (isOpen) {
      loadHistory();
    }
  }, [isOpen, loadHistory]);

  // Execute universal search whenever debouncedQuery or filters change
  const executeSearch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await searchService.search({
        ...filters,
        query: debouncedQuery,
      });
      setSearchResponse(res);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Search failed. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [debouncedQuery, filters]);

  useEffect(() => {
    executeSearch();
  }, [executeSearch]);

  // Execute autocomplete whenever raw query changes
  useEffect(() => {
    let active = true;
    if (!query.trim()) {
      setSuggestions([]);
      return;
    }
    setSuggestionsLoading(true);
    searchService
      .getSuggestions(query)
      .then((res) => {
        if (active) setSuggestions(res);
      })
      .catch(() => {
        if (active) setSuggestions([]);
      })
      .finally(() => {
        if (active) setSuggestionsLoading(false);
      });

    return () => {
      active = false;
    };
  }, [query]);

  const clearHistory = async () => {
    try {
      await searchService.clearHistory();
      setHistory([]);
    } catch (err) {
      console.error('Failed to clear search history', err);
    }
  };

  const updateFilters = (newFilters: Partial<SearchFilters>) => {
    setFilters((prev) => ({
      ...prev,
      ...newFilters,
      page: newFilters.page !== undefined ? newFilters.page : 1, // reset page unless explicit
    }));
  };

  return {
    isOpen,
    setIsOpen,
    query,
    setQuery,
    debouncedQuery,
    filters,
    updateFilters,
    searchResponse,
    suggestions,
    history,
    loading,
    suggestionsLoading,
    error,
    clearHistory,
    refreshSearch: executeSearch,
  };
}
