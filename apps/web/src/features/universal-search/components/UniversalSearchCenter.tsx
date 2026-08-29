import React, { useState, useEffect } from 'react';
import {
  executeSearch, fetchAutocompleteSuggestions, compareResultItems, fetchSearchFacets, rebuildSearchIndex,
  SearchQueryResponse, SearchResultItem, AutocompleteItem, CompareResultsResponse
} from '../universal-search-api';
import {
  Search, Command, Sparkles, Filter, ShieldCheck, RefreshCw, FileText, CheckCircle2, AlertTriangle, GitCompare, HelpCircle, Layers, ArrowRight, CornerDownRight
} from 'lucide-react';

interface UniversalSearchCenterProps {
  initialQuery?: string;
  initialProjectId?: string;
  token?: string;
}

export const UniversalSearchCenter: React.FC<UniversalSearchCenterProps> = ({
  initialQuery = 'JWT Expiry',
  initialProjectId,
  token
}) => {
  const [query, setQuery] = useState<string>(initialQuery);
  const [mode, setMode] = useState<string>('HYBRID');
  const [searchResults, setSearchResults] = useState<SearchQueryResponse | null>(null);
  const [autocompletes, setAutocompletes] = useState<AutocompleteItem[]>([]);
  const [facets, setFacets] = useState<Record<string, number>>({});
  const [selectedForCompare, setSelectedForCompare] = useState<string[]>([]);
  const [comparison, setComparison] = useState<CompareResultsResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const runSearch = async (searchQuery: string = query, searchMode: string = mode) => {
    if (!searchQuery.trim()) return;
    setIsLoading(true);
    try {
      const [sRes, fRes] = await Promise.all([
        executeSearch(searchQuery, searchMode, initialProjectId, undefined, token).catch(() => null),
        fetchSearchFacets(token).catch(() => ({}))
      ]);
      if (sRes) setSearchResults(sRes);
      setFacets(fRes);
    } catch (err) {
      console.error('Failed to execute search:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    runSearch();
  }, [initialQuery, token]);

  const handleInputChange = async (val: string) => {
    setQuery(val);
    if (val.length >= 2) {
      try {
        const auto = await fetchAutocompleteSuggestions(val, token);
        setAutocompletes(auto);
      } catch (err) {
        console.error('Autocomplete failed:', err);
      }
    } else {
      setAutocompletes([]);
    }
  };

  const handleToggleCompare = (id: string) => {
    setSelectedForCompare((prev) => {
      if (prev.includes(id)) return prev.filter((i) => i !== id);
      if (prev.length >= 2) return [prev[1], id];
      return [...prev, id];
    });
  };

  const handleExecuteCompare = async () => {
    if (selectedForCompare.length < 2) return;
    try {
      const cmp = await compareResultItems(selectedForCompare[0], selectedForCompare[1], token);
      setComparison(cmp);
    } catch (err) {
      console.error('Failed comparison:', err);
    }
  };

  const handleRebuild = async () => {
    try {
      await rebuildSearchIndex(token);
      runSearch();
    } catch (err) {
      console.error('Failed to rebuild search index:', err);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6 text-slate-100 font-sans select-none">
      
      {/* Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/80 to-slate-900 border border-indigo-800/60 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-indigo-400 px-2.5 py-0.5 bg-indigo-950 rounded border border-indigo-800/60 flex items-center space-x-1">
                <Command className="w-3 h-3" />
                <span>Cmd + K Universal Search</span>
              </span>
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center space-x-1">
                <ShieldCheck className="w-3 h-3" />
                <span>Side-Channel Leak Prevention</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <Search className="w-7 h-7 text-indigo-400" />
              <span>Universal Knowledge Discovery Engine</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Search across decisions, documents, conversations, tasks, and files. Rank by authority signal and flag knowledge contradictions.
            </p>
          </div>

          <div className="flex items-center space-x-3 flex-shrink-0">
            <div className="flex items-center space-x-1 bg-slate-950 px-3 py-1.5 rounded-2xl border border-slate-800 text-xs font-mono">
              {['HYBRID', 'KEYWORD', 'SEMANTIC'].map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => { setMode(m); runSearch(query, m); }}
                  className={`px-2 py-0.5 rounded font-bold transition-all ${
                    mode === m ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {m}
                </button>
              ))}
            </div>

            <button
              type="button"
              onClick={handleRebuild}
              className="px-4 py-2 rounded-2xl bg-slate-800 hover:bg-slate-700 text-indigo-400 font-bold text-xs shadow-md transition-all flex items-center space-x-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Rebuild Index</span>
            </button>
          </div>
        </div>

        {/* Search Input Box */}
        <div className="relative">
          <div className="flex items-center space-x-2 bg-slate-950 border border-slate-800 rounded-2xl px-4 py-3 shadow-inner">
            <Search className="w-5 h-5 text-indigo-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => handleInputChange(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && runSearch()}
              placeholder="Ask anything (e.g. 'Where did we decide to use PostgreSQL?' or 'JWT Expiry')"
              className="w-full bg-transparent text-sm text-white focus:outline-none placeholder-slate-500 font-medium"
            />
            <button
              type="button"
              onClick={() => runSearch()}
              className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-white font-bold text-xs shadow-md transition-all flex-shrink-0"
            >
              Search
            </button>
          </div>

          {/* Autocomplete Suggestions Popup */}
          {autocompletes.length > 0 && (
            <div className="absolute left-0 right-0 top-full mt-1 bg-slate-950 border border-slate-800 rounded-2xl p-2 shadow-2xl z-50 space-y-1 font-mono text-xs">
              {autocompletes.map((a) => (
                <div
                  key={a.id}
                  onClick={() => { setQuery(a.label); setAutocompletes([]); runSearch(a.label); }}
                  className="p-2 hover:bg-slate-900 rounded-xl cursor-pointer flex items-center justify-between text-slate-300"
                >
                  <span>{a.label}</span>
                  <span className="text-[9px] text-indigo-400 bg-slate-900 px-2 py-0.5 rounded">{a.type}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Main Split Layout */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Left 2 Cols: Search Results & Contradiction Alerts */}
        <div className="md:col-span-2 space-y-5">
          
          {/* Contradiction Alert Banner */}
          {searchResults?.has_contradictions && (
            <div className="bg-amber-950/40 border border-amber-800/60 p-4 rounded-2xl flex items-center space-x-3 text-xs text-amber-200 backdrop-blur-md">
              <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0" />
              <div>
                <span className="font-bold block">Potential Knowledge Conflict Detected</span>
                <span className="text-[11px] text-amber-300/80">{searchResults.contradiction_summary}</span>
              </div>
            </div>
          )}

          {/* Result Items Grouped */}
          <div className="bg-slate-900/80 border border-indigo-800/60 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-xs font-bold text-white flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-indigo-400" />
                <span>Search Results ({searchResults?.total_results || 0})</span>
              </h3>
              <span className="text-[9px] font-mono text-slate-500">Mode: {mode}</span>
            </div>

            <div className="space-y-4">
              {searchResults?.results.map((item) => (
                <div
                  key={item.id}
                  className={`p-4 rounded-2xl border transition-all space-y-2.5 ${
                    item.authority_status === 'CURRENT_GOVERNED'
                      ? 'bg-slate-950 border-emerald-800/50 shadow-emerald-950/20'
                      : item.authority_status === 'SUPERSEDED'
                      ? 'bg-slate-950 border-amber-800/40 opacity-80'
                      : 'bg-slate-950 border-slate-800'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="text-[9px] font-mono font-bold text-indigo-400 bg-slate-900 px-2 py-0.5 rounded uppercase">
                        {item.entity_type}
                      </span>
                      <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded uppercase ${
                        item.authority_status === 'CURRENT_GOVERNED'
                          ? 'text-emerald-400 bg-emerald-950 border border-emerald-800/60'
                          : 'text-amber-400 bg-amber-950 border border-amber-800/60'
                      }`}>
                        {item.authority_status}
                      </span>
                    </div>

                    <div className="flex items-center space-x-2">
                      <button
                        type="button"
                        onClick={() => handleToggleCompare(item.id)}
                        className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded border transition-all ${
                          selectedForCompare.includes(item.id)
                            ? 'bg-indigo-600 text-white border-indigo-500'
                            : 'bg-slate-900 text-slate-400 hover:text-white border-slate-800'
                        }`}
                      >
                        {selectedForCompare.includes(item.id) ? 'Selected' : 'Compare'}
                      </button>
                    </div>
                  </div>

                  <h4 className="font-bold text-xs text-white">{item.title}</h4>
                  <p className="text-[11px] text-slate-300 bg-slate-900/80 p-2.5 rounded-xl border border-slate-800/80">
                    "{item.snippet}"
                  </p>

                  <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 pt-1">
                    <span>Project: {item.project_name}</span>
                    <span>Explanation: {item.explanation}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>

        {/* Right Col: Category Facets & Compare Drawer */}
        <div className="space-y-4">
          
          {/* Facets Box */}
          <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-3xl shadow-xl space-y-3 backdrop-blur-md">
            <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
              <Filter className="w-4 h-4 text-indigo-400" />
              <h4 className="text-xs font-bold text-white">Entity Type Facets</h4>
            </div>

            <div className="space-y-1.5 text-xs font-mono">
              {Object.entries(facets).map(([et, count]) => (
                <div key={et} className="flex items-center justify-between p-2 bg-slate-950 rounded-xl border border-slate-800">
                  <span className="text-slate-300">{et}</span>
                  <span className="text-indigo-400 font-bold bg-slate-900 px-2 py-0.5 rounded">{count}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Comparison Drawer */}
          {selectedForCompare.length >= 2 && (
            <div className="bg-slate-900/80 border border-indigo-800/60 p-5 rounded-3xl shadow-xl space-y-3 backdrop-blur-md">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <h4 className="text-xs font-bold text-white flex items-center space-x-2">
                  <GitCompare className="w-4 h-4 text-indigo-400" />
                  <span>Item Comparison Drawer</span>
                </h4>
                <button
                  type="button"
                  onClick={handleExecuteCompare}
                  className="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-white font-bold text-xs"
                >
                  Compare
                </button>
              </div>

              {comparison && (
                <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-2 text-xs">
                  <span className="text-[9px] font-mono font-bold text-indigo-400 uppercase">Comparison Diff</span>
                  <p className="text-[11px] text-slate-300">{comparison.comparison_summary}</p>
                </div>
              )}
            </div>
          )}

        </div>

      </div>

    </div>
  );
};
