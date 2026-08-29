import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  fetchTimelineEvents,
  triggerTimelineBackfill,
  TimelineEventItem
} from '../timeline-api';
import {
  Clock, Calendar, Sparkles, Filter, Search, Loader2, CheckCircle2,
  FileText, MessageSquare, Briefcase, AlertCircle, RefreshCw, ChevronRight
} from 'lucide-react';

interface KnowledgeTimelineProps {
  organizationId?: string;
  workspaceId?: string;
  projectId?: string;
  token?: string;
  onAskMindMesh?: (prompt: string) => void;
}

export const KnowledgeTimeline: React.FC<KnowledgeTimelineProps> = ({
  organizationId,
  workspaceId,
  projectId,
  token,
  onAskMindMesh
}) => {
  const navigate = useNavigate();
  const [events, setEvents] = useState<TimelineEventItem[]>([]);
  const [activeCategory, setActiveCategory] = useState<string>('all');
  const [activeImportance, setActiveImportance] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isBackfilling, setIsBackfilling] = useState<boolean>(false);

  const loadTimeline = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await fetchTimelineEvents(
        organizationId,
        workspaceId,
        projectId,
        activeCategory,
        activeImportance,
        searchQuery,
        1,
        50,
        token
      );
      setEvents(data.events || []);
    } catch (err) {
      console.error('Failed to load timeline:', err);
    } finally {
      setIsLoading(false);
    }
  }, [organizationId, workspaceId, projectId, activeCategory, activeImportance, searchQuery, token]);

  useEffect(() => {
    loadTimeline();
  }, [loadTimeline]);

  const handleBackfill = async () => {
    setIsBackfilling(true);
    try {
      await triggerTimelineBackfill(token);
      await loadTimeline();
    } catch (err) {
      console.error('Backfill error:', err);
    } finally {
      setIsBackfilling(false);
    }
  };

  const handleEventClick = (ev: TimelineEventItem) => {
    if (ev.deep_link) {
      if (ev.deep_link.startsWith('/')) {
        navigate(ev.deep_link);
      } else if (ev.deep_link.startsWith('file_preview:')) {
        const fileId = ev.deep_link.replace('file_preview:', '');
        navigate(`/files?preview=${fileId}`);
      }
    }
  };

  const handleAskEvolutionHandoff = (ev: TimelineEventItem, e: React.MouseEvent) => {
    e.stopPropagation();
    const promptText = `How did the decision or document "${ev.title}" evolve over time in our organization?`;
    if (onAskMindMesh) {
      onAskMindMesh(promptText);
    } else {
      navigate('/ask', { state: { initialPrompt: promptText } });
    }
  };

  const getEventIcon = (type: string, importance: string) => {
    switch (type) {
      case 'DECISION_MADE':
        return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
      case 'TASK_CREATED':
      case 'TASK_COMPLETED':
        return <CheckCircle2 className="w-4 h-4 text-amber-400" />;
      case 'DOCUMENT_CREATED':
      case 'DOCUMENT_UPDATED':
      case 'FILE_SHARED':
        return <FileText className="w-4 h-4 text-blue-400" />;
      case 'CONVERSATION_STARTED':
        return <MessageSquare className="w-4 h-4 text-indigo-400" />;
      case 'PROJECT_CREATED':
      case 'PROJECT_UPDATED':
      case 'MILESTONE':
        return <Briefcase className="w-4 h-4 text-purple-400" />;
      default:
        return <Clock className="w-4 h-4 text-slate-400" />;
    }
  };

  // Group events by Month Year
  const groupedEvents: Record<string, TimelineEventItem[]> = {};
  events.forEach(ev => {
    const d = ev.occurred_at ? new Date(ev.occurred_at) : new Date();
    const groupKey = d.toLocaleDateString('en-US', { month: 'long', year: 'numeric' }).toUpperCase();
    if (!groupedEvents[groupKey]) {
      groupedEvents[groupKey] = [];
    }
    groupedEvents[groupKey].push(ev);
  });

  return (
    <div className="w-full max-w-5xl mx-auto p-4 md:p-6 space-y-6 text-slate-100 select-none">
      
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/80 border border-slate-800 p-5 rounded-2xl shadow-lg backdrop-blur-md">
        <div>
          <h2 className="text-xl font-bold flex items-center space-x-2 text-white">
            <Clock className="w-5 h-5 text-indigo-400" />
            <span>Knowledge Timeline</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Organizational memory tracking chronological decisions, documents, tasks, and project milestones.
          </p>
        </div>

        <div className="flex items-center space-x-2 shrink-0">
          <button
            type="button"
            onClick={handleBackfill}
            disabled={isBackfilling}
            className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isBackfilling ? 'animate-spin' : ''}`} />
            <span>{isBackfilling ? 'Syncing Timeline...' : 'Sync History'}</span>
          </button>
        </div>
      </div>

      {/* Filter Tabs & Search Bar */}
      <div className="bg-slate-900/60 border border-slate-800/80 p-3.5 rounded-2xl space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
          
          {/* Category Tabs */}
          <div className="flex items-center space-x-1 overflow-x-auto pb-1 sm:pb-0">
            {['all', 'DECISION_MADE', 'TASK_CREATED', 'DOCUMENT_CREATED', 'PROJECT_CREATED'].map(cat => (
              <button
                key={cat}
                type="button"
                onClick={() => setActiveCategory(cat)}
                className={`px-3 py-1.5 rounded-xl capitalize font-medium transition-all ${
                  activeCategory === cat
                    ? 'bg-indigo-600 text-white font-semibold shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                {cat === 'all' ? 'All Events' : cat.replace('_CREATED', 's').replace('_MADE', 's').toLowerCase()}
              </button>
            ))}
          </div>

          {/* Importance Filter */}
          <div className="flex items-center space-x-1 shrink-0">
            <span className="text-[11px] text-slate-500 font-semibold uppercase tracking-wider mr-1">Importance:</span>
            {['all', 'HIGH', 'MEDIUM', 'LOW'].map(imp => (
              <button
                key={imp}
                type="button"
                onClick={() => setActiveImportance(imp)}
                className={`px-2.5 py-1 rounded-lg text-[11px] font-mono capitalize transition-all ${
                  activeImportance === imp
                    ? 'bg-slate-800 text-indigo-300 font-bold border border-indigo-500/40'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {imp}
              </button>
            ))}
          </div>
        </div>

        {/* Timeline Search Input */}
        <div className="relative">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-2.5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search timeline events by title, decision, or topic..."
            className="w-full bg-slate-950/60 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-all font-medium"
          />
        </div>
      </div>

      {/* Timeline Event Feed */}
      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-20 text-slate-400 space-y-3">
          <Loader2 className="w-7 h-7 animate-spin text-indigo-400" />
          <span className="text-xs font-medium">Loading organizational memory timeline...</span>
        </div>
      ) : Object.keys(groupedEvents).length === 0 ? (
        <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-12 text-center text-slate-400 space-y-3">
          <Clock className="w-10 h-10 text-slate-600 mx-auto stroke-1" />
          <h3 className="text-sm font-semibold text-slate-200">No knowledge events yet</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Once MindMesh processes your documents, conversations, decisions, and projects, key milestones will appear here.
          </p>
        </div>
      ) : (
        <div className="space-y-8 pl-2 relative before:absolute before:left-6 before:top-4 before:bottom-4 before:w-0.5 before:bg-slate-800">
          {Object.entries(groupedEvents).map(([monthGroup, groupItems]) => (
            <div key={monthGroup} className="space-y-4">
              
              {/* Month Header Badge */}
              <div className="sticky top-0 z-10 flex items-center space-x-2 bg-slate-950/90 backdrop-blur-md py-1.5 px-3 rounded-xl border border-slate-800/80 w-fit text-slate-300">
                <Calendar className="w-3.5 h-3.5 text-indigo-400" />
                <span className="text-[11px] font-bold uppercase tracking-wider font-mono">{monthGroup}</span>
              </div>

              {/* Event Cards */}
              <div className="space-y-3 pl-8 relative">
                {groupItems.map(ev => (
                  <div
                    key={ev.id}
                    onClick={() => handleEventClick(ev)}
                    className="p-4 bg-slate-900/60 border border-slate-800/80 hover:border-indigo-500/50 hover:bg-slate-800/50 rounded-2xl cursor-pointer transition-all group relative space-y-2"
                  >
                    {/* Event Dot Marker */}
                    <div className={`absolute -left-[38px] top-4 w-4 h-4 rounded-full border-2 border-slate-950 flex items-center justify-center ${
                      ev.importance === 'HIGH' ? 'bg-indigo-500 shadow-sm shadow-indigo-500/50' : 'bg-slate-700'
                    }`} />

                    <div className="flex items-start justify-between">
                      <div className="flex items-center space-x-2.5 min-w-0">
                        <div className="p-2 rounded-xl bg-slate-800/80 border border-slate-700/60 shrink-0">
                          {getEventIcon(ev.event_type, ev.importance)}
                        </div>
                        <div className="min-w-0">
                          <h4 className="font-semibold text-slate-100 text-xs truncate group-hover:text-indigo-300 transition-colors">
                            {ev.title}
                          </h4>
                          <div className="flex items-center space-x-2 text-[10px] text-slate-400 mt-0.5 font-mono">
                            <span className={`capitalize px-1.5 py-0.2 rounded font-semibold ${
                              ev.importance === 'HIGH' ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30' : 'bg-slate-800 text-slate-400'
                            }`}>
                              {ev.event_type.replace('_', ' ')}
                            </span>
                            <span>•</span>
                            <span>{ev.occurred_at ? new Date(ev.occurred_at).toLocaleDateString() : 'Date'}</span>
                          </div>
                        </div>
                      </div>

                      {/* AI Evolution Handoff Button */}
                      <button
                        type="button"
                        onClick={(e) => handleAskEvolutionHandoff(ev, e)}
                        className="opacity-0 group-hover:opacity-100 flex items-center space-x-1 px-2.5 py-1 rounded-xl bg-indigo-600/90 hover:bg-indigo-500 text-white text-[11px] font-medium transition-all shadow-sm shrink-0"
                        title="Ask MindMesh how this knowledge evolved"
                      >
                        <Sparkles className="w-3 h-3" />
                        <span>Evolution</span>
                      </button>
                    </div>

                    {ev.description && (
                      <p className="text-xs text-slate-300 leading-relaxed pl-10 line-clamp-2">
                        {ev.description}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
