import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  globalSearch,
  getRecentSearches,
  getAutocompleteSuggestions,
  clearSearchHistory,
  SearchResultItem,
  AutocompleteSuggestion
} from '../search-api';
import {
  Search, X, MessageSquare, FileText, Briefcase, User as UserIcon,
  Clock, Sparkles, CheckCircle2, Loader2, ArrowRight, Trash2, Filter
} from 'lucide-react';

interface GlobalSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  organizationId?: string;
  workspaceId?: string;
  token?: string;
  onSelectItem?: (item: SearchResultItem) => void;
  onAskMindMesh?: (contextText: string, title?: string) => void;
}

export const GlobalSearchModal: React.FC<GlobalSearchModalProps> = ({
  isOpen,
  onClose,
  organizationId,
  workspaceId,
  token,
  onSelectItem,
  onAskMindMesh
}) => {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState<string>('all');
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [suggestions, setSuggestions] = useState<AutocompleteSuggestion[]>([]);
  const [recent, setRecent] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedResult, setSelectedResult] = useState<SearchResultItem | null>(null);

  // Keyboard shortcut listener (Cmd+K / Ctrl+K / '/' key)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        if (isOpen) onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Load recent history when modal opens
  useEffect(() => {
    if (!isOpen) return;
    getRecentSearches(organizationId, token).then(setRecent).catch(console.error);
  }, [isOpen, organizationId, token]);

  const handleSearch = useCallback(async (qText: string, category: string) => {
    if (!qText.trim()) {
      setResults([]);
      return;
    }
    setIsLoading(true);
    try {
      const data = await globalSearch(qText, organizationId, workspaceId, category, token);
      setResults(data.results || data.items || []);
    } catch (err) {
      console.error('Universal search error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [organizationId, workspaceId, token]);

  // Debounced search & autocomplete suggestions
  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setSuggestions([]);
      return;
    }

    const timer = setTimeout(() => {
      handleSearch(query, activeCategory);
      getAutocompleteSuggestions(query, organizationId, token)
        .then(setSuggestions)
        .catch(() => setSuggestions([]));
    }, 250);

    return () => clearTimeout(timer);
  }, [query, activeCategory, handleSearch, organizationId, token]);

  if (!isOpen) return null;

  const handleClearHistory = async () => {
    await clearSearchHistory(token);
    setRecent([]);
  };

  const handleDeepLinkClick = (item: SearchResultItem) => {
    if (onSelectItem) {
      onSelectItem(item);
    }

    if (item.deep_link) {
      if (item.deep_link.startsWith('/')) {
        navigate(item.deep_link);
      } else if (item.deep_link.startsWith('file_preview:')) {
        const fileId = item.deep_link.replace('file_preview:', '');
        navigate(`/files?preview=${fileId}`);
      }
    }
    onClose();
  };

  const handleAskHandoff = (item: SearchResultItem, e: React.MouseEvent) => {
    e.stopPropagation();
    const contextPrompt = `Context from ${item.source_type} "${item.title}":\n\n${item.snippet}`;
    if (onAskMindMesh) {
      onAskMindMesh(contextPrompt, item.title);
    } else {
      navigate('/ask', { state: { initialPrompt: `What does "${item.title}" say about ${query}?`, contextText: contextPrompt } });
    }
    onClose();
  };

  const getResultIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'message':
      case 'conversation':
        return <MessageSquare className="w-4 h-4 text-blue-400" />;
      case 'document':
      case 'file':
        return <FileText className="w-4 h-4 text-emerald-400" />;
      case 'project':
        return <Briefcase className="w-4 h-4 text-purple-400" />;
      case 'task':
        return <CheckCircle2 className="w-4 h-4 text-amber-400" />;
      case 'decision':
        return <CheckCircle2 className="w-4 h-4 text-indigo-400" />;
      default:
        return <Search className="w-4 h-4 text-slate-400" />;
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-950/70 backdrop-blur-md z-50 flex items-start justify-center pt-16 p-4 select-none animate-fadeIn">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-3xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh] text-slate-100">
        
        {/* Search Input Bar */}
        <div className="p-4 border-b border-slate-800/80 flex items-center space-x-3 bg-slate-950/60">
          <Search className="w-5 h-5 text-indigo-400 shrink-0" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search organization memory (documents, messages, decisions, tasks)..."
            autoFocus
            className="flex-1 bg-transparent text-white placeholder-slate-400 text-sm focus:outline-none font-medium"
          />
          {query && (
            <button
              type="button"
              onClick={() => setQuery('')}
              className="p-1 text-slate-400 hover:text-white rounded-lg transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          <button
            type="button"
            onClick={onClose}
            className="px-2 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 transition-colors"
          >
            ESC
          </button>
        </div>

        {/* Filter Categories */}
        <div className="px-4 py-2 border-b border-slate-800/60 bg-slate-950/40 flex items-center justify-between text-xs overflow-x-auto">
          <div className="flex items-center space-x-1.5 shrink-0">
            <Filter className="w-3.5 h-3.5 text-slate-400 mr-1" />
            {['all', 'document', 'message', 'project', 'task', 'decision'].map(cat => (
              <button
                key={cat}
                type="button"
                onClick={() => setActiveCategory(cat)}
                className={`px-3 py-1 rounded-lg capitalize transition-all font-medium text-xs ${
                  activeCategory === cat
                    ? 'bg-indigo-600 text-white font-semibold shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                {cat === 'all' ? 'All Sources' : `${cat}s`}
              </button>
            ))}
          </div>
        </div>

        {/* Results Body */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          
          {/* Autocomplete Suggestions Popup */}
          {query.trim() && suggestions.length > 0 && results.length > 0 && (
            <div className="p-2.5 rounded-xl bg-slate-950/40 border border-slate-800/60 space-y-1.5">
              <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-400 px-1">Quick Suggestions</span>
              <div className="flex flex-wrap gap-1.5">
                {suggestions.map(s => (
                  <button
                    key={s.id}
                    type="button"
                    onClick={() => setQuery(s.title)}
                    className="flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-indigo-600 hover:text-white text-xs text-slate-300 transition-colors"
                  >
                    <span>{s.title}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-16 text-slate-400 space-y-3">
              <Loader2 className="w-6 h-6 animate-spin text-indigo-400" />
              <span className="text-xs font-medium">Searching organization's memory...</span>
            </div>
          ) : query.trim() ? (
            results.length === 0 ? (
              <div className="py-16 text-center text-slate-400 space-y-2">
                <Search className="w-8 h-8 text-slate-600 mx-auto stroke-1" />
                <p className="text-sm font-semibold text-slate-300">No results found for "{query}"</p>
                <p className="text-xs text-slate-500">Try searching for key terms, project names, or specific document titles.</p>
              </div>
            ) : (
              <div className="space-y-2.5">
                <div className="flex items-center justify-between text-xs text-slate-400 px-1">
                  <span>Found {results.length} relevant results</span>
                  <span className="text-[10px] text-slate-500 font-mono">Hybrid RRF Fusion</span>
                </div>

                {results.map(item => (
                  <div
                    key={item.id}
                    onClick={() => handleDeepLinkClick(item)}
                    className="p-3.5 bg-slate-950/40 border border-slate-800/80 hover:border-indigo-500/50 hover:bg-slate-800/40 rounded-xl cursor-pointer transition-all group relative space-y-2"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center space-x-2 min-w-0">
                        <div className="p-1.5 rounded-lg bg-slate-800/80 border border-slate-700/60 shrink-0">
                          {getResultIcon(item.source_type || 'document')}
                        </div>
                        <div className="min-w-0">
                          <h4 className="font-semibold text-slate-100 text-xs truncate group-hover:text-indigo-300 transition-colors">
                            {item.title}
                          </h4>
                          <p className="text-[10px] text-slate-400 flex items-center space-x-2 mt-0.5">
                            <span className="capitalize px-1.5 py-0.2 bg-slate-800 rounded font-mono text-indigo-300">
                              {item.source_type || 'document'}
                            </span>
                            <span>•</span>
                            <span>{item.location || 'Workspace'}</span>
                            {item.created_at && (
                              <>
                                <span>•</span>
                                <span>{new Date(item.created_at).toLocaleDateString()}</span>
                              </>
                            )}
                          </p>
                        </div>
                      </div>

                      {/* AI Handoff Action Button */}
                      <button
                        type="button"
                        onClick={(e) => handleAskHandoff(item, e)}
                        className="opacity-0 group-hover:opacity-100 flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-indigo-600/90 hover:bg-indigo-500 text-white text-[11px] font-medium transition-all shadow-sm shrink-0"
                        title="Ask MindMesh about this search result"
                      >
                        <Sparkles className="w-3 h-3" />
                        <span>Ask MindMesh</span>
                      </button>
                    </div>

                    {/* Snippet preview with bold markdown highlights */}
                    <p className="text-xs text-slate-300 leading-relaxed pl-8 line-clamp-2">
                      {item.snippet}
                    </p>
                  </div>
                ))}
              </div>
            )
          ) : (
            /* Recent Searches Section */
            recent.length > 0 && (
              <div className="space-y-3 pt-2">
                <div className="flex items-center justify-between px-1">
                  <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Recent Searches</p>
                  <button
                    type="button"
                    onClick={handleClearHistory}
                    className="text-[11px] text-slate-500 hover:text-rose-400 flex items-center space-x-1 transition-colors"
                  >
                    <Trash2 className="w-3 h-3" />
                    <span>Clear</span>
                  </button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {recent.map((r, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => setQuery(r)}
                      className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-800/50 border border-slate-700/50 hover:bg-slate-800 hover:border-slate-600 text-xs text-slate-200 rounded-xl transition-all"
                    >
                      <Clock className="w-3 h-3 text-slate-400" />
                      <span>{r}</span>
                    </button>
                  ))}
                </div>
              </div>
            )
          )}
        </div>
      </div>
    </div>
  );
};
