import React, { useState, useEffect } from 'react';
import {
  fetchProactiveFeed, dismissInsight, snoozeInsight, followEntity, fetchIntelligenceInbox,
  ProactiveInsightItem, IntelligenceInboxResponse
} from '../proactive-workspace-api';
import {
  Zap, Bell, AlertOctagon, AlertTriangle, ShieldCheck, CheckCircle2, Eye, EyeOff, Clock, UserPlus, ArrowRight, CornerDownRight, RefreshCw, Filter, Layers, Check
} from 'lucide-react';

interface ProactiveKnowledgeWorkspaceProps {
  initialProjectId?: string;
  token?: string;
}

export const ProactiveKnowledgeWorkspace: React.FC<ProactiveKnowledgeWorkspaceProps> = ({
  initialProjectId = 'proj-auth-101',
  token
}) => {
  const [feed, setFeed] = useState<ProactiveInsightItem[]>([]);
  const [inbox, setInbox] = useState<IntelligenceInboxResponse | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>('UNREAD');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [feedRes, inboxRes] = await Promise.all([
        fetchProactiveFeed(initialProjectId, filterStatus, token),
        fetchIntelligenceInbox(token)
      ]);
      setFeed(feedRes);
      setInbox(inboxRes);
    } catch (err) {
      console.error('Failed to load proactive feed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [initialProjectId, filterStatus, token]);

  const handleDismiss = async (insightId: string) => {
    try {
      const res = await dismissInsight(insightId, 'Already Handled', token);
      setActionMessage(res.message);
      loadData();
    } catch (err) {
      console.error('Failed dismiss:', err);
    }
  };

  const handleSnooze = async (insightId: string) => {
    try {
      const res = await snoozeInsight(insightId, '1d', token);
      setActionMessage(res.message);
      loadData();
    } catch (err) {
      console.error('Failed snooze:', err);
    }
  };

  const handleFollow = async (entityId: string) => {
    try {
      const res = await followEntity(entityId, token);
      setActionMessage(res.message);
    } catch (err) {
      console.error('Failed follow:', err);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6 text-slate-100 font-sans select-none">
      
      {/* Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/80 to-slate-900 border border-indigo-800/60 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-indigo-400 px-2.5 py-0.5 bg-indigo-950 rounded border border-indigo-800/60">
                PROACTIVE KNOWLEDGE WORKSPACE
              </span>
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center space-x-1">
                <ShieldCheck className="w-3 h-3" />
                <span>Noise-Filtered & Human-in-the-Loop</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <Zap className="w-7 h-7 text-indigo-400" />
              <span>Proactive Intelligence Feed</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Proactively surfaces relevant changes, decision impacts, knowledge conflicts, and risk warnings before you ask.
            </p>
          </div>

          {/* Inbox Counter Stats */}
          {inbox && (
            <div className="flex items-center space-x-3 bg-slate-950 p-2.5 rounded-2xl border border-slate-800 flex-shrink-0">
              <div className="text-center px-3 border-r border-slate-800">
                <span className="text-[9px] font-mono text-slate-500 uppercase block">Unread</span>
                <span className="text-base font-black text-white">{inbox.unread_count}</span>
              </div>
              <div className="text-center px-3 border-r border-slate-800">
                <span className="text-[9px] font-mono text-slate-500 uppercase block">Critical</span>
                <span className="text-base font-black text-red-400">{inbox.critical_count}</span>
              </div>
              <div className="text-center px-3">
                <span className="text-[9px] font-mono text-slate-500 uppercase block">Important</span>
                <span className="text-base font-black text-amber-400">{inbox.important_count}</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Action Notification Toast */}
      {actionMessage && (
        <div className="p-3 bg-indigo-950/80 border border-indigo-800/60 rounded-2xl text-xs text-indigo-200 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Check className="w-4 h-4 text-emerald-400" />
            <span>{actionMessage}</span>
          </div>
          <button type="button" onClick={() => setActionMessage(null)} className="text-[10px] text-slate-400 hover:text-white font-mono">Dismiss</button>
        </div>
      )}

      {/* Filter Toolbar */}
      <div className="flex items-center justify-between bg-slate-900/80 border border-slate-800 p-3 rounded-2xl backdrop-blur-md">
        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-indigo-400" />
          <span className="text-xs font-bold text-slate-300">Filter View:</span>
          {['UNREAD', 'ALL', 'DISMISSED', 'SNOOZED'].map((st) => (
            <button
              key={st}
              type="button"
              onClick={() => setFilterStatus(st)}
              className={`px-3 py-1 rounded-xl text-xs font-bold transition-all ${
                filterStatus === st ? 'bg-indigo-600 text-white' : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
              }`}
            >
              {st}
            </button>
          ))}
        </div>

        <button
          type="button"
          onClick={() => loadData()}
          className="p-1.5 bg-slate-950 hover:bg-slate-800 border border-slate-800 rounded-xl text-slate-400 hover:text-white"
        >
          <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Proactive Feed Cards */}
      <div className="space-y-4">
        {feed.length === 0 ? (
          <div className="p-8 text-center bg-slate-900/60 border border-slate-800 rounded-3xl space-y-2">
            <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto" />
            <h3 className="text-xs font-bold text-white">No active proactive insights</h3>
            <p className="text-xs text-slate-400">Your organizational memory feed is clear of active conflicts or blockers.</p>
          </div>
        ) : (
          feed.map((ins) => (
            <div
              key={ins.insight_id}
              className={`bg-slate-900/80 border p-5 rounded-3xl shadow-xl space-y-3 backdrop-blur-md transition-all ${
                ins.priority === 'CRITICAL' ? 'border-red-800/60' : ins.priority === 'IMPORTANT' ? 'border-amber-800/60' : 'border-indigo-800/60'
              }`}
            >
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-slate-800 pb-3">
                <div className="flex items-center space-x-2">
                  {ins.priority === 'CRITICAL' ? (
                    <AlertOctagon className="w-4 h-4 text-red-400" />
                  ) : (
                    <AlertTriangle className="w-4 h-4 text-amber-400" />
                  )}
                  <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${
                    ins.priority === 'CRITICAL' ? 'bg-red-950 text-red-400 border-red-800/60' : 'bg-amber-950 text-amber-400 border-amber-800/60'
                  }`}>
                    {ins.priority} • {ins.type}
                  </span>
                  <h3 className="text-xs font-bold text-white">{ins.title}</h3>
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    type="button"
                    onClick={() => handleSnooze(ins.insight_id)}
                    className="px-2.5 py-1 bg-slate-950 hover:bg-slate-800 border border-slate-800 rounded-xl text-[10px] text-slate-300 font-bold flex items-center space-x-1"
                  >
                    <Clock className="w-3 h-3" />
                    <span>Snooze</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => handleDismiss(ins.insight_id)}
                    className="px-2.5 py-1 bg-slate-950 hover:bg-slate-800 border border-slate-800 rounded-xl text-[10px] text-slate-300 font-bold flex items-center space-x-1"
                  >
                    <EyeOff className="w-3 h-3" />
                    <span>Dismiss</span>
                  </button>
                </div>
              </div>

              {/* Summary & Observable Reason */}
              <p className="text-xs text-slate-200 leading-relaxed font-medium">{ins.summary}</p>
              
              <div className="p-3 bg-slate-950 border border-slate-800 rounded-2xl space-y-1 text-xs">
                <span className="text-[9px] font-mono text-indigo-400 uppercase font-bold">Why am I seeing this?</span>
                <p className="text-[11px] text-slate-300">{ins.reason}</p>
              </div>

              {/* Evidence Section */}
              <div className="space-y-1 text-xs">
                <span className="text-[9px] font-mono text-slate-500 uppercase block">Observable Evidence</span>
                <div className="flex flex-wrap gap-2">
                  {ins.evidence.map((ev, idx) => (
                    <span key={idx} className="text-[10px] text-slate-300 bg-slate-950 px-2.5 py-1 rounded-xl border border-slate-800">
                      • {ev}
                    </span>
                  ))}
                </div>
              </div>

              {/* Recommended Next Step */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pt-2 border-t border-slate-800">
                <div className="flex items-center space-x-1 text-xs text-emerald-400">
                  <CornerDownRight className="w-3.5 h-3.5" />
                  <span className="font-bold">{ins.suggested_action}</span>
                </div>

                <button
                  type="button"
                  onClick={() => handleFollow(ins.related_entities[0] || 'entity')}
                  className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-white font-bold text-xs flex items-center space-x-1 flex-shrink-0"
                >
                  <UserPlus className="w-3 h-3" />
                  <span>Follow Entity</span>
                </button>
              </div>

            </div>
          ))
        )}
      </div>

    </div>
  );
};
