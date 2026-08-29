import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { executeUniversalSearch, fetchTypeaheadSuggestions, UniversalSearchResponse, UniversalSearchResultItem, TypeaheadSuggestion } from '../universal-search-api';
import {
  Search, Sparkles, Filter, FileText, MessageSquare, Briefcase, CheckSquare, Layers, ArrowRight, ExternalLink, Network, RefreshCw, X
} from 'lucide-react';

interface UniversalSearchCenterProps {
  workspaceId?: string;
  projectId?: string;
  token?: string;
  initialQuery?: string;
}

export const UniversalSearchCenter: React.FC<UniversalSearchCenterProps> = ({
  workspaceId,
  projectId,
  token,
  initialQuery = 'authentication'
}) => {
  const navigate = useNavigate();
  const [query, setQuery] = useState<string>(initialQuery);
  const [activeFilter, setActiveFilter] = useState<string>('ALL');
  const [searchResponse, setSearchResponse] = useState<UniversalSearchResponse | null>(null);
  const [suggestions, setSuggestions] = useState<TypeaheadSuggestion[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const handleSearch = useCallback(async (qText: string, filter: string) => {
    if (!qText.trim()) return;
    setIsLoading(true);
    try {
      const res = await executeUniversalSearch(qText, filter, workspaceId, projectId, token);
      setSearchResponse(res);
    } catch (err) {
      console.error('Failed to execute search:', err);
    } finally {
      setIsLoading(false);
    }
  }, [workspaceId, projectId, token]);

  useEffect(() => {
    handleSearch(query, activeFilter);
  }, [activeFilter]);

  const handleInputChange = async (val: string) => {
    setQuery(val);
    if (val.trim().length >= 2) {
      try {
        const suggs = await fetchTypeaheadSuggestions(val, token);
        setSuggestions(suggs);
      } catch (err) {
        console.error('Failed to fetch suggestions:', err);
      }
    } else {
      setSuggestions([]);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6 text-slate-100 font-sans select-none">
      
      {/* Search Header */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/60 to-slate-900 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-indigo-400 px-2 py-0.5 bg-indigo-950 rounded border border-indigo-800/60">
              UNIVERSAL KNOWLEDGE RETRIEVAL
            </span>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <Search className="w-7 h-7 text-indigo-400" />
              <span>Universal Knowledge Search</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              One search query across Direct Messages, Groups, Documents, Specialized Files, Tasks, Decisions, and Knowledge Graph connections.
            </p>
          </div>
        </div>

        {/* Search Bar Input */}
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-slate-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => handleInputChange(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && (setSuggestions([]), handleSearch(query, activeFilter))}
            placeholder="Search organizational memory (e.g. 'Why did we choose PostgreSQL?', 'JWT settings')..."
            className="w-full bg-slate-950/80 border border-slate-800 pl-10 pr-12 py-3 rounded-2xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />

          <button
            type="button"
            onClick={() => (setSuggestions([]), handleSearch(query, activeFilter))}
            className="absolute right-2 top-2 px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs"
          >
            Search
          </button>

          {/* Typeahead Suggestions Dropdown */}
          {suggestions.length > 0 && (
            <div className="absolute left-0 right-0 top-12 z-50 bg-slate-900 border border-slate-800 rounded-2xl p-2 shadow-2xl space-y-1">
              {suggestions.map((s, idx) => (
                <div
                  key={idx}
                  onClick={() => {
                    setQuery(s.title);
                    setSuggestions([]);
                    handleSearch(s.title, activeFilter);
                  }}
                  className="p-2 hover:bg-slate-800 rounded-xl cursor-pointer text-xs flex items-center justify-between"
                >
                  <span className="font-semibold text-slate-200">{s.title}</span>
                  <span className="text-[9px] font-mono uppercase px-1.5 py-0.2 bg-slate-950 text-indigo-400 rounded">
                    {s.entity_type}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Natural Language Intent & Entity Filters */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div className="flex flex-wrap items-center gap-1.5">
          {(['ALL', 'DOCUMENT', 'MESSAGE', 'DECISION', 'TASK', 'FILE'] as const).map((filter) => (
            <button
              key={filter}
              type="button"
              onClick={() => setActiveFilter(filter)}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                activeFilter === filter
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'bg-slate-900/60 text-slate-400 hover:text-white border border-slate-800'
              }`}
            >
              {filter}
            </button>
          ))}
        </div>

        {searchResponse && (
          <div className="flex items-center space-x-2 text-[10px] font-mono text-slate-400">
            <span className="px-2 py-0.5 bg-slate-900 rounded border border-slate-800 text-indigo-400 font-bold">
              INTENT: {searchResponse.intent}
            </span>
            <span>{searchResponse.total_results} Results Found</span>
          </div>
        )}
      </div>

      {/* Search Results Grid */}
      <div className="space-y-3">
        {!searchResponse || searchResponse.results.length === 0 ? (
          <div className="py-16 text-center space-y-2 bg-slate-900/40 border border-slate-800/60 rounded-3xl">
            <Search className="w-8 h-8 text-slate-600 mx-auto" />
            <h4 className="text-xs font-bold text-slate-300">No matching organizational knowledge found</h4>
            <p className="text-[11px] text-slate-500">Try broadening your search query or selecting a different filter.</p>
          </div>
        ) : (
          searchResponse.results.map((res) => (
            <div
              key={res.id}
              className="p-4 bg-slate-900/70 border border-slate-800 hover:border-slate-700 rounded-3xl space-y-2.5 transition-all shadow-md"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${
                    res.entity_type === 'DECISION'
                      ? 'bg-emerald-950 text-emerald-400 border-emerald-800/60'
                      : res.entity_type === 'TASK'
                      ? 'bg-indigo-950 text-indigo-400 border-indigo-800/60'
                      : 'bg-slate-800 text-slate-300 border-slate-700'
                  }`}>
                    {res.entity_type}
                  </span>

                  {res.governance_status && (
                    <span className={`text-[8px] font-mono px-1.5 py-0.2 rounded border uppercase ${
                      res.governance_status === 'SUPERSEDED'
                        ? 'bg-amber-950 text-amber-400 border-amber-800/60'
                        : 'bg-emerald-950 text-emerald-400 border-emerald-800/60'
                    }`}>
                      {res.governance_status}
                    </span>
                  )}
                </div>

                {res.project_name && (
                  <span className="text-[9px] font-mono text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                    Project: {res.project_name}
                  </span>
                )}
              </div>

              <div>
                <h3 className="text-sm font-bold text-slate-100">{res.title}</h3>
                <p className="text-[11px] text-slate-400 mt-1 italic bg-slate-950 p-2.5 rounded-xl border border-slate-800">
                  "{res.excerpt}"
                </p>
              </div>

              <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1">
                <span>{res.relevance_reason}</span>

                <div className="flex items-center space-x-2">
                  <button
                    type="button"
                    onClick={() => navigate('/knowledge/graph')}
                    className="px-2.5 py-1 rounded-xl bg-slate-800 hover:bg-slate-700 text-indigo-400 font-bold text-[10px] flex items-center space-x-1"
                  >
                    <Network className="w-3 h-3" />
                    <span>Explore Connections</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => navigate('/hub')}
                    className="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-[10px] shadow-md flex items-center space-x-1"
                  >
                    <span>Open Source</span>
                    <ExternalLink className="w-3 h-3" />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

    </div>
  );
};
