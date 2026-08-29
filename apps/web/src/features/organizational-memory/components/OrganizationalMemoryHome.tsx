import React, { useState, useEffect } from 'react';
import {
  fetchMemoryHome, fetchEntityMemory, queryMemoryOS, fetchMemoryHealth, triggerMemoryReindex,
  MemoryHomeResponse, EntityMemoryResponse, MemoryQueryResult, MemoryHealthResponse
} from '../memory-os-api';
import {
  Cpu, Search, Sparkles, Activity, RefreshCw, Layers, ShieldCheck, CornerDownRight, ArrowRight, Bookmark, Compass, FileText, CheckSquare, MessageSquare, AlertCircle, Info
} from 'lucide-react';

interface OrganizationalMemoryHomeProps {
  token?: string;
}

export const OrganizationalMemoryHome: React.FC<OrganizationalMemoryHomeProps> = ({ token }) => {
  const [scope, setScope] = useState<string>('ORGANIZATION');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [homeData, setHomeData] = useState<MemoryHomeResponse | null>(null);
  const [queryResult, setQueryResult] = useState<MemoryQueryResult | null>(null);
  const [selectedEntityMemory, setSelectedEntityMemory] = useState<EntityMemoryResponse | null>(null);
  const [health, setHealth] = useState<MemoryHealthResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const loadMemoryHome = async () => {
    setIsLoading(true);
    try {
      const [hRes, hltRes] = await Promise.all([
        fetchMemoryHome(scope, token).catch(() => null),
        fetchMemoryHealth(token).catch(() => null)
      ]);
      if (hRes) setHomeData(hRes);
      if (hltRes) setHealth(hltRes);
    } catch (err) {
      console.error('Failed to load Memory Home:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadMemoryHome();
  }, [scope, token]);

  const handleQuery = async () => {
    if (!searchQuery.strip && !searchQuery) return;
    setIsLoading(true);
    try {
      const res = await queryMemoryOS(searchQuery, scope, token);
      setQueryResult(res);
    } catch (err) {
      console.error('Failed memory query:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReindex = async () => {
    try {
      await triggerMemoryReindex(token);
      loadMemoryHome();
    } catch (err) {
      console.error('Failed memory reindex:', err);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6 text-slate-100 font-sans select-none">
      
      {/* Flagship Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/80 to-slate-900 border border-indigo-800/60 p-6 rounded-3xl shadow-2xl space-y-4 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-indigo-400 px-2.5 py-0.5 bg-indigo-950 rounded border border-indigo-800/60">
                ORGANIZATIONAL MEMORY OS v5.0
              </span>
              {health && (
                <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center space-x-1">
                  <Activity className="w-3 h-3" />
                  <span>OS {health.overall_status}</span>
                </span>
              )}
            </div>
            <h1 className="text-3xl font-black text-white mt-1.5 flex items-center space-x-2">
              <Cpu className="w-8 h-8 text-indigo-400" />
              <span>MindMesh Memory</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              One unified organizational memory operating system orchestrating Search, Graph, Governance, Timeline, Synthesis, and Agentic Workflows.
            </p>
          </div>

          <button
            type="button"
            onClick={handleReindex}
            className="px-4 py-2 rounded-2xl bg-slate-800 hover:bg-slate-700 text-indigo-400 font-bold text-xs shadow-md transition-all flex items-center space-x-1.5"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Reindex Memory System</span>
          </button>
        </div>

        {/* Global Memory Search & Scope Bar */}
        <div className="space-y-3 pt-3 border-t border-slate-800/80">
          <div className="flex items-center space-x-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleQuery()}
                placeholder="Ask MindMesh Memory (e.g. 'What do we know about authentication?' or 'I'm new to this project. What should I know?')"
                className="w-full bg-slate-950 border border-slate-800 rounded-2xl pl-9 pr-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-medium"
              />
            </div>
            <button
              type="button"
              onClick={handleQuery}
              disabled={isLoading}
              className="px-5 py-2.5 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-md transition-all flex items-center space-x-1.5 flex-shrink-0 disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4" />
              <span>{isLoading ? 'Querying...' : 'Ask Memory'}</span>
            </button>
          </div>

          {/* Scope Selector Pills */}
          <div className="flex flex-wrap gap-2 pt-1">
            <span className="text-xs text-slate-400 font-mono py-1">Active Memory Scope:</span>
            {(['ORGANIZATION', 'CURRENT_PROJECT', 'WORKSPACE', 'PERSONAL'] as const).map((sc) => (
              <button
                key={sc}
                type="button"
                onClick={() => setScope(sc)}
                className={`px-3 py-1 rounded-xl text-[10px] font-bold font-mono transition-all ${
                  scope === sc
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
                }`}
              >
                {sc}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Query Result View if Active */}
      {queryResult && (
        <div className="bg-slate-900/90 border border-indigo-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono font-bold text-indigo-400 bg-indigo-950 px-2 py-0.5 rounded border border-indigo-800">
                {queryResult.query_type}
              </span>
              <h3 className="text-sm font-bold text-white">{queryResult.answer.title}</h3>
            </div>
            <button
              type="button"
              onClick={() => setQueryResult(null)}
              className="text-xs font-mono text-slate-500 hover:text-white"
            >
              Clear Query
            </button>
          </div>

          {queryResult.query_type === 'ONBOARDING_BRIEF' ? (
            <div className="space-y-3 text-xs">
              <p className="text-slate-300 font-medium">{queryResult.answer.purpose}</p>
              <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 space-y-1">
                <span className="text-[9px] font-mono font-bold text-indigo-400 uppercase">CURRENT STATE</span>
                <p className="text-white font-bold">{queryResult.answer.current_state}</p>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 space-y-1">
                  <span className="text-[9px] font-mono font-bold text-emerald-400 uppercase">KEY DECISIONS</span>
                  {queryResult.answer.key_decisions.map((d: string, idx: number) => (
                    <div key={idx} className="text-slate-200">{d}</div>
                  ))}
                </div>
                <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 space-y-1">
                  <span className="text-[9px] font-mono font-bold text-amber-400 uppercase">OPEN WORK & BLOCKERS</span>
                  {queryResult.answer.open_work.map((w: string, idx: number) => (
                    <div key={idx} className="text-slate-200">{w}</div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl">
              <p className="text-xs text-slate-200">{queryResult.answer.synthesis || queryResult.answer.recommendation}</p>
            </div>
          )}
        </div>
      )}

      {/* Main Memory OS Dashboard Split */}
      {homeData && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          
          {/* Left 2 Cols: Knowledge Feed & Active Project Memory */}
          <div className="md:col-span-2 space-y-5">
            
            {/* Active Project Memory Summary */}
            <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-3xl shadow-xl space-y-3 backdrop-blur-md">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <h3 className="text-xs font-bold text-white flex items-center space-x-2">
                  <Layers className="w-4 h-4 text-indigo-400" />
                  <span>Active Project Memory — {homeData.project_memory.name}</span>
                </h3>
                <span className="text-[9px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded">
                  {homeData.project_memory.status}
                </span>
              </div>

              <p className="text-xs text-slate-300 font-medium">{homeData.project_memory.current_state}</p>

              <div className="grid grid-cols-3 gap-2 pt-1 font-mono text-[10px]">
                <div className="p-2 bg-slate-950 rounded-xl border border-slate-800 text-center">
                  <span className="text-slate-400 block">Decisions</span>
                  <strong className="text-indigo-400 text-xs">{homeData.project_memory.important_decisions}</strong>
                </div>
                <div className="p-2 bg-slate-950 rounded-xl border border-slate-800 text-center">
                  <span className="text-slate-400 block">Open Tasks</span>
                  <strong className="text-white text-xs">{homeData.project_memory.open_tasks}</strong>
                </div>
                <div className="p-2 bg-slate-950 rounded-xl border border-slate-800 text-center">
                  <span className="text-slate-400 block">Blockers</span>
                  <strong className="text-rose-400 text-xs">{homeData.project_memory.blockers}</strong>
                </div>
              </div>
            </div>

            {/* Unified Knowledge Feed */}
            <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-xs font-bold text-white flex items-center space-x-2">
                  <Activity className="w-4 h-4 text-indigo-400" />
                  <span>Unified Knowledge Feed</span>
                </h3>
                <span className="text-[9px] font-mono text-slate-500">Significance-Based Grouping</span>
              </div>

              <div className="space-y-4">
                {homeData.knowledge_feed.map((grp) => (
                  <div key={grp.id} className="p-4 bg-slate-950 border border-slate-800/80 rounded-2xl space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="font-bold text-xs text-indigo-300">{grp.group_title}</h4>
                      <span className="text-[9px] font-mono text-slate-500">{grp.updates_count} updates</span>
                    </div>

                    <div className="space-y-2">
                      {grp.items.map((item, idx) => (
                        <div key={idx} className="p-3 bg-slate-900 border border-slate-800 rounded-xl space-y-1 text-xs">
                          <div className="flex items-center justify-between">
                            <span className="text-[9px] font-mono font-bold text-indigo-400 uppercase">{item.type}</span>
                            <span className={`text-[8px] font-mono font-bold px-1.5 py-0.2 rounded uppercase ${
                              item.governance_status === 'VERIFIED' ? 'bg-emerald-950 text-emerald-400' : 'bg-rose-950 text-rose-400'
                            }`}>
                              {item.governance_status}
                            </span>
                          </div>
                          <h5 className="font-bold text-slate-100 text-[11px]">{item.title}</h5>
                          <p className="text-[10px] text-slate-400">{item.why_it_matters}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

          </div>

          {/* Right Col: Suggested Exploration & System Health */}
          <div className="space-y-4">
            
            {/* Suggested Exploration Card */}
            <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-3xl shadow-xl space-y-3 backdrop-blur-md">
              <h4 className="text-xs font-bold text-white border-b border-slate-800 pb-2">Suggested Exploration</h4>
              <div className="space-y-2">
                {homeData.suggested_exploration.map((exp, idx) => (
                  <button
                    key={idx}
                    type="button"
                    className="w-full text-left p-2.5 bg-slate-950 hover:bg-slate-900 border border-slate-800 rounded-xl text-xs font-bold text-indigo-300 transition-all flex items-center justify-between"
                  >
                    <span>{exp}</span>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                  </button>
                ))}
              </div>
            </div>

            {/* System Health Card */}
            {health && (
              <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-3xl shadow-xl space-y-3 backdrop-blur-md font-mono text-xs">
                <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
                  <Activity className="w-4 h-4 text-emerald-400" />
                  <h4 className="font-bold text-white">Memory Subsystems Health</h4>
                </div>

                <div className="space-y-1 text-[11px]">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Search Index:</span>
                    <span className="text-emerald-400 font-bold">{health.search_index}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Knowledge Graph:</span>
                    <span className="text-emerald-400 font-bold">{health.knowledge_graph}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Governance:</span>
                    <span className="text-emerald-400 font-bold">{health.governance_engine}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">AI Synthesis:</span>
                    <span className="text-emerald-400 font-bold">{health.ai_synthesis_engine}</span>
                  </div>
                </div>
              </div>
            )}

          </div>

        </div>
      )}

    </div>
  );
};
