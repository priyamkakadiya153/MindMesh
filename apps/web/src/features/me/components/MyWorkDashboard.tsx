import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchUserContext, fetchCatchUpSummary, UserContextResponse, CatchUpResponse } from '../me-context-api';
import {
  UserCheck, CheckSquare, Briefcase, FileText, Sparkles, Loader2,
  RefreshCw, AlertTriangle, Clock, ArrowRight, Zap, History,
  ShieldCheck, CheckCircle2, MessageSquare, X
} from 'lucide-react';

interface MyWorkDashboardProps {
  workspaceId?: string;
  token?: string;
  onAskMindMesh?: (prompt: string) => void;
}

export const MyWorkDashboard: React.FC<MyWorkDashboardProps> = ({
  workspaceId,
  token,
  onAskMindMesh
}) => {
  const navigate = useNavigate();
  const [data, setData] = useState<UserContextResponse | null>(null);
  const [catchUpData, setCatchUpData] = useState<CatchUpResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [showCatchUpModal, setShowCatchUpModal] = useState<boolean>(false);
  const [isCatchUpLoading, setIsCatchUpLoading] = useState<boolean>(false);

  const loadContext = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await fetchUserContext(workspaceId, token);
      setData(res);
    } catch (err) {
      console.error('Failed to load user context:', err);
    } finally {
      setIsLoading(false);
    }
  }, [workspaceId, token]);

  useEffect(() => {
    loadContext();
  }, [loadContext]);

  const handleCatchUp = async () => {
    setIsCatchUpLoading(true);
    setShowCatchUpModal(true);
    try {
      const summary = await fetchCatchUpSummary(workspaceId, undefined, token);
      setCatchUpData(summary);
    } catch (err) {
      console.error('Failed to load catch-up summary:', err);
    } finally {
      setIsCatchUpLoading(false);
    }
  };

  const handleAskQuestion = (question: string) => {
    if (onAskMindMesh) {
      onAskMindMesh(question);
    } else {
      navigate('/ask', { state: { initialPrompt: question } });
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-slate-400 space-y-3">
        <Loader2 className="w-7 h-7 animate-spin text-indigo-400" />
        <span className="text-xs font-medium">Loading your personal workspace context...</span>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-8 text-center text-slate-400 text-xs bg-slate-900/40 border border-slate-800 rounded-3xl space-y-2">
        <AlertTriangle className="w-8 h-8 text-amber-400 mx-auto" />
        <p>Personal context could not be loaded.</p>
        <button
          type="button"
          onClick={loadContext}
          className="px-4 py-2 rounded-xl bg-slate-800 text-slate-200 text-xs font-semibold"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6 text-slate-100 select-none">
      
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/60 to-slate-900 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-indigo-400 px-2 py-0.5 bg-indigo-950 rounded border border-indigo-800/60">
                MY WORKSPACE CONTEXT
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1 flex items-center space-x-2">
              <UserCheck className="w-7 h-7 text-indigo-400" />
              <span>My Work</span>
            </h1>
          </div>

          <div className="flex items-center space-x-3 shrink-0">
            <button
              type="button"
              onClick={handleCatchUp}
              className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-md transition-all"
            >
              <History className="w-4 h-4" />
              <span>Catch Me Up</span>
            </button>
          </div>
        </div>

        {/* Quick Context Prompt Chips */}
        <div className="pt-2 border-t border-slate-800/80">
          <span className="text-[10px] text-slate-500 font-mono block mb-2">Ask MindMesh about your work:</span>
          <div className="flex flex-wrap gap-2">
            {[
              'What should I work on next?',
              'Why is this task relevant to me?',
              'What changed since I last worked here?',
              'What tasks do I owe?'
            ].map((q, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleAskQuestion(q)}
                className="flex items-center space-x-1 px-3 py-1.5 rounded-xl bg-slate-800/80 hover:bg-indigo-950 text-indigo-300 border border-slate-700 text-xs font-medium transition-all"
              >
                <Sparkles className="w-3 h-3" />
                <span>{q}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Needs Attention Section (if overdue/blocked tasks exist) */}
      {(data.needs_attention.overdue_count > 0 || data.needs_attention.blocked_count > 0) && (
        <div className="bg-rose-950/30 border border-rose-500/30 p-5 rounded-3xl space-y-3 shadow-md">
          <div className="flex items-center space-x-2 text-rose-400">
            <AlertTriangle className="w-5 h-5" />
            <h3 className="text-xs font-bold uppercase tracking-wider">Needs Attention</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {data.needs_attention.items.map((item) => (
              <div key={item.id} className="bg-slate-950/80 border border-rose-500/20 p-3.5 rounded-2xl flex items-start justify-between">
                <div>
                  <h4 className="text-xs font-bold text-slate-100">{item.title}</h4>
                  <span className="text-[10px] text-rose-300 font-mono mt-0.5 block">{item.reason}</span>
                </div>
                <span className="text-[9px] font-mono font-bold px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30 uppercase">
                  {item.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Main 2-Col Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* My Tasks (2 cols) */}
        <div className="md:col-span-2 bg-slate-900/70 border border-slate-800 p-5 rounded-3xl space-y-4 shadow-md">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-2">
              <CheckSquare className="w-4 h-4 text-indigo-400" />
              <span>My Tasks ({data.my_tasks.length})</span>
            </h3>

            <button
              type="button"
              onClick={() => navigate('/tasks')}
              className="text-[11px] font-semibold text-indigo-400 hover:text-indigo-300 flex items-center space-x-1"
            >
              <span>View All Tasks</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="space-y-2.5 max-h-[350px] overflow-y-auto">
            {data.my_tasks.length === 0 ? (
              <p className="text-xs text-slate-500 py-6 text-center">No assigned tasks right now.</p>
            ) : (
              data.my_tasks.map((t) => (
                <div key={t.id} className="p-3.5 bg-slate-950/60 border border-slate-800/80 rounded-2xl flex items-center justify-between">
                  <div className="space-y-1">
                    <h4 className="text-xs font-bold text-slate-100">{t.title}</h4>
                    {t.due_date && (
                      <span className="text-[10px] text-slate-500 font-mono block">Due: {t.due_date.slice(0, 10)}</span>
                    )}
                  </div>
                  <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${
                    t.status === 'COMPLETED' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                    t.status === 'BLOCKED' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' :
                    'bg-slate-800 text-slate-300 border-slate-700'
                  }`}>
                    {t.status}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* My Projects & Recent Knowledge (1 col) */}
        <div className="space-y-6">
          
          {/* My Projects */}
          <div className="bg-slate-900/70 border border-slate-800 p-5 rounded-3xl space-y-3 shadow-md">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-2">
              <Briefcase className="w-4 h-4 text-emerald-400" />
              <span>My Projects ({data.my_projects.length})</span>
            </h3>

            <div className="space-y-2">
              {data.my_projects.length === 0 ? (
                <p className="text-xs text-slate-500 py-3 text-center">No active project memberships.</p>
              ) : (
                data.my_projects.map((p) => (
                  <div
                    key={p.id}
                    onClick={() => navigate(`/projects/${p.id}/intelligence`)}
                    className="p-3 bg-slate-950/60 hover:bg-slate-950 border border-slate-800/80 hover:border-indigo-500/40 rounded-xl cursor-pointer transition-all flex items-center justify-between"
                  >
                    <span className="text-xs font-semibold text-slate-200">{p.name}</span>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Recent Knowledge */}
          <div className="bg-slate-900/70 border border-slate-800 p-5 rounded-3xl space-y-3 shadow-md">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-2">
              <FileText className="w-4 h-4 text-blue-400" />
              <span>Recent Knowledge</span>
            </h3>

            <div className="space-y-2">
              {data.recent_knowledge.length === 0 ? (
                <p className="text-xs text-slate-500 py-3 text-center">No recent documents accessed.</p>
              ) : (
                data.recent_knowledge.map((d) => (
                  <div key={d.id} className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-xl space-y-1">
                    <h5 className="text-xs font-medium text-slate-200">{d.title}</h5>
                    <span className="text-[9px] text-slate-500 font-mono block">Updated: {d.updated_at ? d.updated_at.slice(0, 10) : ''}</span>
                  </div>
                ))
              )}
            </div>
          </div>

        </div>

      </div>

      {/* Catch Me Up Modal */}
      {showCatchUpModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-3xl max-w-xl w-full space-y-4 shadow-2xl relative">
            <button
              type="button"
              onClick={() => setShowCatchUpModal(false)}
              className="absolute right-4 top-4 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
            >
              <X className="w-4 h-4" />
            </button>

            <div className="flex items-center space-x-2">
              <History className="w-5 h-5 text-indigo-400" />
              <h3 className="text-sm font-bold text-white">Catch Me Up Summary</h3>
            </div>

            {isCatchUpLoading ? (
              <div className="py-8 text-center text-slate-400 space-y-2 text-xs">
                <Loader2 className="w-5 h-5 animate-spin text-indigo-400 mx-auto" />
                <p>Computing recent changes since your last activity...</p>
              </div>
            ) : catchUpData ? (
              <div className="space-y-4 max-h-[400px] overflow-y-auto pr-1">
                <p className="text-xs text-slate-300 bg-slate-950 p-3.5 rounded-2xl border border-slate-800 leading-relaxed font-medium">
                  {catchUpData.summary}
                </p>

                {catchUpData.new_decisions.length > 0 && (
                  <div className="space-y-2">
                    <span className="text-[10px] font-mono font-bold text-emerald-400 uppercase">New Decisions</span>
                    {catchUpData.new_decisions.map((d) => (
                      <div key={d.id} className="p-2.5 bg-slate-950 rounded-xl border border-slate-800/80 text-xs text-slate-200">
                        {d.content}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <p className="text-xs text-slate-400">Failed to load summary.</p>
            )}
          </div>
        </div>
      )}

    </div>
  );
};
