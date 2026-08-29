import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  fetchHubOverview,
  fetchProjectKnowledgeOverview,
  HubOverviewResponse,
  KnowledgeItem,
  ProjectKnowledgeOverviewResponse
} from '../hub-api';
import { KnowledgeCard } from './KnowledgeCard';
import { ImportantForYouWidget } from '../../intelligence/components/ImportantForYouWidget';
import {
  Brain, Search, Sparkles, Loader2, RefreshCw,
  FileText, MessageSquare, Briefcase, CheckCircle2, Clock,
  Network, ArrowRight, Database, FolderCheck
} from 'lucide-react';

interface UnifiedKnowledgeHubProps {
  organizationId?: string;
  workspaceId?: string;
  token?: string;
  onAskMindMesh?: (prompt: string) => void;
}

export const UnifiedKnowledgeHub: React.FC<UnifiedKnowledgeHubProps> = ({
  organizationId,
  workspaceId,
  token,
  onAskMindMesh
}) => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [category, setCategory] = useState<string>('all');
  const [data, setData] = useState<HubOverviewResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [projectOverview, setProjectOverview] = useState<ProjectKnowledgeOverviewResponse | null>(null);

  const loadHub = useCallback(async () => {
    setIsLoading(true);
    try {
      const overview = await fetchHubOverview(workspaceId, 30, token);
      setData(overview);
    } catch (err) {
      console.error('Failed to load Knowledge Hub:', err);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [workspaceId, token]);

  useEffect(() => {
    loadHub();
  }, [loadHub]);

  const handleRefresh = () => {
    setIsRefreshing(true);
    loadHub();
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery)}`);
    }
  };

  const handleAskHandoff = () => {
    const promptText = searchQuery.trim()
      ? `What does our workspace knowledge say about "${searchQuery}"?`
      : 'What are the key active decisions and tasks in our workspace?';

    if (onAskMindMesh) {
      onAskMindMesh(promptText);
    } else {
      navigate('/ask', { state: { initialPrompt: promptText } });
    }
  };

  const filteredKnowledge = (data?.recent_knowledge || []).filter(item => {
    if (category === 'all') return true;
    if (category === 'decisions') return item.type.toUpperCase() === 'DECISION';
    if (category === 'tasks') return item.type.toUpperCase() === 'TASK';
    if (category === 'documents') return item.type.toUpperCase() === 'DOCUMENT';
    if (category === 'conversations') return item.type.toUpperCase() === 'CONVERSATION';
    return true;
  });

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6 text-slate-100 select-none">
      
      {/* Header & Main Search Section */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/60 to-slate-900 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-5 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-indigo-400 px-2 py-0.5 bg-indigo-950 rounded border border-indigo-800/60">
              ORGANIZATIONAL MEMORY
            </span>
            <h1 className="text-2xl font-black text-white mt-1 flex items-center space-x-2">
              <Brain className="w-7 h-7 text-indigo-400" />
              <span>Unified Knowledge Hub</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Discover, navigate, and query connected documents, conversations, decisions, tasks, and project history in one place.
            </p>
          </div>

          <button
            type="button"
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-slate-800/80 hover:bg-slate-800 text-xs font-semibold text-slate-200 border border-slate-700 transition-all shrink-0 self-start md:self-auto"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span>Refresh Hub</span>
          </button>
        </div>

        {/* Universal Search & Ask MindMesh Input */}
        <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row gap-2.5 pt-1">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search workspace memory (e.g. PostgreSQL, JWT expiry, Authentication)..."
              className="w-full bg-slate-950/70 border border-slate-800 rounded-xl pl-9 pr-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-all font-medium shadow-inner"
            />
          </div>

          <div className="flex items-center space-x-2 shrink-0">
            <button
              type="submit"
              className="flex-1 sm:flex-none px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold border border-slate-700 transition-all"
            >
              Search
            </button>
            <button
              type="button"
              onClick={handleAskHandoff}
              className="flex-1 sm:flex-none flex items-center justify-center space-x-1.5 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md transition-all"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Ask MindMesh</span>
            </button>
          </div>
        </form>
      </div>

      {/* Real Database Count Badges */}
      {data?.counts && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
          <div className="p-3.5 bg-slate-900/80 border border-slate-800 rounded-2xl flex items-center space-x-3 shadow-md">
            <div className="p-2 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
              <FileText className="w-4 h-4" />
            </div>
            <div>
              <span className="text-[10px] text-slate-400 font-medium">Documents</span>
              <h4 className="text-base font-bold text-white">{data.counts.documents}</h4>
            </div>
          </div>

          <div className="p-3.5 bg-slate-900/80 border border-slate-800 rounded-2xl flex items-center space-x-3 shadow-md">
            <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <CheckCircle2 className="w-4 h-4" />
            </div>
            <div>
              <span className="text-[10px] text-slate-400 font-medium">Decisions</span>
              <h4 className="text-base font-bold text-white">{data.counts.decisions}</h4>
            </div>
          </div>

          <div className="p-3.5 bg-slate-900/80 border border-slate-800 rounded-2xl flex items-center space-x-3 shadow-md">
            <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <CheckCircle2 className="w-4 h-4" />
            </div>
            <div>
              <span className="text-[10px] text-slate-400 font-medium">Tasks</span>
              <h4 className="text-base font-bold text-white">{data.counts.tasks}</h4>
            </div>
          </div>

          <div className="p-3.5 bg-slate-900/80 border border-slate-800 rounded-2xl flex items-center space-x-3 shadow-md">
            <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <MessageSquare className="w-4 h-4" />
            </div>
            <div>
              <span className="text-[10px] text-slate-400 font-medium">Conversations</span>
              <h4 className="text-base font-bold text-white">{data.counts.conversations}</h4>
            </div>
          </div>

          <div className="p-3.5 bg-slate-900/80 border border-slate-800 rounded-2xl flex items-center space-x-3 shadow-md">
            <div className="p-2 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
              <Briefcase className="w-4 h-4" />
            </div>
            <div>
              <span className="text-[10px] text-slate-400 font-medium">Projects</span>
              <h4 className="text-base font-bold text-white">{data.counts.projects}</h4>
            </div>
          </div>
        </div>
      )}

      {/* Category Filter Tabs */}
      <div className="flex items-center space-x-2 overflow-x-auto pb-1 scrollbar-none">
        {['all', 'decisions', 'tasks', 'documents', 'conversations'].map((cat) => (
          <button
            key={cat}
            type="button"
            onClick={() => setCategory(cat)}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold capitalize transition-all whitespace-nowrap ${
              category === cat
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'bg-slate-900/80 hover:bg-slate-800 text-slate-400 border border-slate-800'
            }`}
          >
            {cat}
          </button>
        ))}

        <div className="h-4 w-px bg-slate-800 mx-1 shrink-0" />

        <button
          type="button"
          onClick={() => navigate('/timeline')}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-slate-300 text-xs font-medium border border-slate-800 shrink-0"
        >
          <Clock className="w-3.5 h-3.5 text-amber-400" />
          <span>Timeline View</span>
        </button>

        <button
          type="button"
          onClick={() => navigate('/knowledge/graph')}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-slate-300 text-xs font-medium border border-slate-800 shrink-0"
        >
          <Network className="w-3.5 h-3.5 text-indigo-400" />
          <span>Relationship Graph</span>
        </button>
      </div>

      {/* Main Content Area */}
      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-20 text-slate-400 space-y-3">
          <Loader2 className="w-7 h-7 animate-spin text-indigo-400" />
          <span className="text-xs font-medium">Aggregating workspace memory...</span>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Recent Knowledge Feed (2 cols) */}
          <div className="lg:col-span-2 space-y-4">
            <h3 className="text-sm font-bold text-slate-200 flex items-center space-x-2">
              <FolderCheck className="w-4 h-4 text-indigo-400" />
              <span>Recent Knowledge Items</span>
            </h3>

            {filteredKnowledge.length === 0 ? (
              <div className="p-8 text-center text-slate-400 text-xs bg-slate-900/40 border border-slate-800 rounded-2xl space-y-2">
                <Database className="w-8 h-8 text-slate-600 mx-auto stroke-1" />
                <p>No organizational knowledge items found for this filter.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                {filteredKnowledge.map((item) => (
                  <KnowledgeCard
                    key={item.id}
                    item={item}
                    onAskMindMesh={onAskMindMesh}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Activity Timeline Feed (1 col) */}
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-slate-200 flex items-center space-x-2">
              <Clock className="w-4 h-4 text-amber-400" />
              <span>Recent Activity Timeline</span>
            </h3>

            <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-2xl space-y-3 max-h-[500px] overflow-y-auto">
              {data?.recent_activity.length === 0 ? (
                <p className="text-xs text-slate-500 text-center py-6">No recent timeline events recorded.</p>
              ) : (
                data?.recent_activity.map((act) => (
                  <div key={act.id} className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-xl space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-[9px] font-mono uppercase text-indigo-400 font-bold px-1.5 py-0.5 bg-indigo-950 rounded">
                        {act.event_type}
                      </span>
                      <span className="text-[9px] text-slate-500 font-mono">
                        {act.occurred_at ? act.occurred_at.slice(0, 10) : ''}
                      </span>
                    </div>
                    <h5 className="text-xs font-semibold text-slate-200 line-clamp-1">{act.title}</h5>
                    <p className="text-[11px] text-slate-400 line-clamp-2">{act.description}</p>
                  </div>
                ))
              )}
            </div>
          </div>

        </div>
      )}
    </div>
  );
};
