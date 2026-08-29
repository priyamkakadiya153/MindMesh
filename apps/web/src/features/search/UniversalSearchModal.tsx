import React, { useState } from 'react';
import {
  Search,
  X,
  Clock,
  Sparkles,
  ArrowRight,
  Trash2,
  ChevronLeft,
  ChevronRight,
  Loader2,
  AlertCircle,
  SearchX,
  FilterX,
  Sliders
} from 'lucide-react';
import { useUniversalSearch } from './useUniversalSearch';
import { SearchResultCard } from './SearchResultCard';
import { SearchFilterPanel } from './SearchFilterPanel';
import { UniversalSearchResultItem } from './types';
import { EmptyState } from '../../shared/components/EmptyState';

interface UniversalSearchModalProps {
  isOpen?: boolean;
  onClose?: () => void;
  onSelectResult?: (item: UniversalSearchResultItem) => void;
}

export function UniversalSearchModal({ isOpen: propsIsOpen, onClose: propsOnClose, onSelectResult }: UniversalSearchModalProps) {
  const {
    isOpen: hookIsOpen,
    setIsOpen,
    query,
    setQuery,
    filters,
    updateFilters,
    searchResponse,
    suggestions,
    history,
    loading,
    suggestionsLoading,
    error,
    clearHistory,
  } = useUniversalSearch();

  const [activeSuggestionIndex, setActiveSuggestionIndex] = useState(-1);

  const isModalVisible = propsIsOpen !== undefined ? propsIsOpen : hookIsOpen;

  const handleClose = () => {
    setIsOpen(false);
    if (propsOnClose) propsOnClose();
  };

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isModalVisible) {
        handleClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isModalVisible]);

  if (!isModalVisible) return null;

  const handleSelectSuggestion = (title: string) => {
    setQuery(title);
    setActiveSuggestionIndex(-1);
  };

  const handleSelectCard = (item: UniversalSearchResultItem) => {
    if (onSelectResult) {
      onSelectResult(item);
    }
    handleClose();
  };

  const totalPages = searchResponse?.total_pages || 0;
  const currentPage = searchResponse?.page || 1;
  const results = searchResponse?.results || [];

  return (
    <div 
      role="dialog"
      aria-modal="true"
      aria-label="Universal Search"
      className="fixed inset-0 z-50 flex items-start justify-center pt-12 sm:pt-20 px-4 bg-bgOverlay backdrop-blur-md transition-all animate-fadeIn"
    >
      {/* Backdrop click to close */}
      <div className="fixed inset-0" onClick={handleClose} aria-hidden="true" />

      {/* Main Search Modal Box */}
      <div className="relative w-full max-w-3xl bg-bgDialog border border-borderColor rounded-2xl shadow-2xl overflow-hidden z-10 flex flex-col max-h-[85vh]">
        {/* Top Header & Search Input */}
        <div className="relative flex items-center px-4 py-3.5 border-b border-borderColor bg-bgHeader gap-3">
          <Search className="w-5 h-5 text-accentText shrink-0" aria-hidden="true" />
          <label htmlFor="universal-search-input" className="sr-only">Search query</label>
          <input
            id="universal-search-input"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search across documents, projects, tasks, chat, users, knowledge..."
            aria-label="Search query"
            className="w-full bg-transparent text-sm text-textPrimary placeholder-textMuted focus:outline-none focus-visible:ring-1 focus-visible:ring-accent"
            autoFocus
          />

          {loading || suggestionsLoading ? (
            <Loader2 className="w-4 h-4 text-accentText animate-spin shrink-0" aria-hidden="true" />
          ) : query ? (
            <button
              type="button"
              onClick={() => setQuery('')}
              aria-label="Clear search query"
              title="Clear search query"
              className="p-1 rounded-md text-textMuted hover:text-textPrimary hover:bg-bgHover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent transition-colors"
            >
              <X className="w-4 h-4" aria-hidden="true" />
            </button>
          ) : null}

          <div className="hidden sm:flex items-center gap-1 text-[10px] text-textMuted bg-bgTertiary px-2 py-1 rounded-md border border-borderMuted" aria-hidden="true">
            <span>ESC</span>
            <span className="text-textMuted">to exit</span>
          </div>
        </div>

        {/* Live Autocomplete Suggestions Box (if typing) */}
        {suggestions.length > 0 && query.trim().length >= 2 && (
          <div className="px-4 py-2 bg-bgTertiary border-b border-borderMuted flex flex-col gap-1">
            <span className="text-[10px] uppercase tracking-wider text-accentText font-medium px-1">
              Suggestions & Recommendations
            </span>
            <div className="flex flex-wrap gap-2 pt-1">
              {suggestions.map((sug) => (
                <button
                  key={sug.id + sug.title}
                  onClick={() => handleSelectSuggestion(sug.title)}
                  className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-bgCard hover:bg-accentSubtle text-xs text-textPrimary border border-borderMuted hover:border-accent/30 transition-all"
                >
                  <Sparkles className="w-3 h-3 text-accentText" />
                  <span>{sug.title}</span>
                  <span className="text-[10px] text-textMuted uppercase">({sug.type})</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Filters Panel */}
        <div className="px-4 py-2.5 border-b border-borderMuted bg-bgTertiary/50">
          <SearchFilterPanel
            filters={filters}
            onFilterChange={updateFilters}
            facets={searchResponse?.facets}
          />
        </div>

        {/* Scrollable Body Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-borderColor">
          {/* Recent Searches Section (shown when query is empty) */}
          {!query.trim() && history.length > 0 && (
            <div className="mb-4 p-3 bg-bgTertiary border border-borderMuted rounded-xl">
              <div className="flex items-center justify-between mb-2 px-1">
                <div className="flex items-center gap-1.5 text-xs text-textMuted font-medium">
                  <Clock className="w-3.5 h-3.5 text-accentText" />
                  <span>Recent Searches</span>
                </div>
                <button
                  onClick={clearHistory}
                  className="text-[11px] text-textMuted hover:text-dangerText flex items-center gap-1 transition-colors"
                >
                  <Trash2 className="w-3 h-3" />
                  <span>Clear History</span>
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {history.map((h) => (
                  <button
                    key={h.id}
                    onClick={() => setQuery(h.query)}
                    className="px-2.5 py-1 rounded-lg bg-bgCard hover:bg-bgHover text-xs text-textSecondary border border-borderMuted hover:border-borderHover transition-all flex items-center gap-1.5"
                  >
                    <span>{h.query}</span>
                    <ArrowRight className="w-3 h-3 text-textMuted opacity-60" />
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Error Message Alert */}
          {error && (
            <div className="p-3 rounded-xl bg-dangerBg border border-dangerBorder text-dangerText text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-dangerText" />
              <span>{error}</span>
            </div>
          )}

          {/* Search Results List */}
          {results.length > 0 ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs text-textMuted px-1">
                <span>
                  Found <strong className="text-textPrimary">{searchResponse?.total_hits}</strong> results ({searchResponse?.query_time_ms} ms)
                </span>
                <span>Page {currentPage} of {totalPages}</span>
              </div>

              <div className="space-y-2.5">
                {results.map((item) => (
                  <SearchResultCard key={item.id} item={item} query={query} onSelect={handleSelectCard} />
                ))}
              </div>
            </div>
          ) : !loading && query.trim() ? (
            /* Empty State */
            <EmptyState
              title="No results found"
              description="Try another keyword or adjust your filters."
              icon={SearchX}
              variant="card"
              primaryAction={{
                label: "Clear Filters",
                onClick: () => {
                  updateFilters({ type: 'all' });
                  setQuery('');
                },
                icon: FilterX
              }}
              secondaryAction={{
                label: "Search Documents",
                onClick: () => updateFilters({ type: 'document' }),
                icon: Sliders
              }}
            />
          ) : !loading ? (
            /* Default Prompt State */
            <div className="py-8 flex flex-col items-center justify-center text-center p-6 text-textMuted">
              <Sparkles className="w-8 h-8 text-accentText/60 mb-2 animate-pulse" />
              <p className="text-xs text-textPrimary font-medium">Type a search query above or select a filter pill to explore.</p>
              <p className="text-[11px] text-textMuted mt-1">Search is automatically permission-aware across your active tenant organization and workspaces.</p>
            </div>
          ) : null}
        </div>

        {/* Modal Footer with Pagination */}
        {totalPages > 1 && (
          <div className="px-4 py-3 border-t border-borderMuted bg-bgHeader flex items-center justify-between text-xs text-textMuted">
            <span>
              Showing {((currentPage - 1) * (searchResponse?.limit || 20)) + 1} - {Math.min(currentPage * (searchResponse?.limit || 20), searchResponse?.total_hits || 0)} of {searchResponse?.total_hits}
            </span>
            <div className="flex items-center gap-2">
              <button
                disabled={currentPage <= 1}
                onClick={() => updateFilters({ page: currentPage - 1 })}
                className="px-2.5 py-1 rounded-lg bg-bgCard border border-borderMuted hover:bg-bgHover text-textPrimary disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1 transition-all"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
                <span>Prev</span>
              </button>
              <span className="font-semibold text-textPrimary">{currentPage} / {totalPages}</span>
              <button
                disabled={currentPage >= totalPages}
                onClick={() => updateFilters({ page: currentPage + 1 })}
                className="px-2.5 py-1 rounded-lg bg-bgCard border border-borderMuted hover:bg-bgHover text-textPrimary disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1 transition-all"
              >
                <span>Next</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
