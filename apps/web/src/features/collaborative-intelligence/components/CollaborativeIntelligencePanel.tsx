import React, { useState, useEffect } from 'react';
import {
  fetchConversationContext, detectSuggestions, confirmDecision, confirmTask, fetchTeamDigest, createReviewRoom, resolveReview,
  ConversationContextResponse, SuggestionItem, TeamDigestResponse, ReviewRoomResponse
} from '../collaborative-intelligence-api';
import {
  Users, MessageSquare, Sparkles, CheckCircle2, HelpCircle, FileText, ArrowRight, ShieldCheck, Activity, CornerDownRight, Check, X
} from 'lucide-react';

interface CollaborativeIntelligencePanelProps {
  initialConversationId?: string;
  token?: string;
}

export const CollaborativeIntelligencePanel: React.FC<CollaborativeIntelligencePanelProps> = ({
  initialConversationId = '70f1236a-7280-4167-8ed3-22bbb857509c',
  token
}) => {
  const [context, setContext] = useState<ConversationContextResponse | null>(null);
  const [suggestions, setSuggestions] = useState<SuggestionItem[]>([]);
  const [digest, setDigest] = useState<TeamDigestResponse | null>(null);
  const [activeReviewRoom, setActiveReviewRoom] = useState<ReviewRoomResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [cRes, sRes, dRes] = await Promise.all([
        fetchConversationContext(initialConversationId, token).catch(() => null),
        detectSuggestions(initialConversationId, token).catch(() => null),
        fetchTeamDigest(token).catch(() => null)
      ]);
      if (cRes) setContext(cRes);
      if (sRes) setSuggestions(sRes.suggestions);
      if (dRes) setDigest(dRes);
    } catch (err) {
      console.error('Failed to load collaborative data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [initialConversationId, token]);

  const handleConfirmDecision = async (suggId: string) => {
    try {
      await confirmDecision(suggId, token);
      setSuggestions((prev) => prev.map((s) => s.suggestion_id === suggId ? { ...s, status: 'CONFIRMED' } : s));
    } catch (err) {
      console.error('Failed to confirm decision:', err);
    }
  };

  const handleConfirmTask = async (suggId: string) => {
    try {
      await confirmTask(suggId, token);
      setSuggestions((prev) => prev.map((s) => s.suggestion_id === suggId ? { ...s, status: 'CONFIRMED' } : s));
    } catch (err) {
      console.error('Failed to confirm task:', err);
    }
  };

  const handleCreateReviewRoom = async () => {
    try {
      const room = await createReviewRoom('JWT Expiry Contradiction Review', ['Auth Arch v1 (15m)', 'Decision #D-102 (30m)'], token);
      setActiveReviewRoom(room);
    } catch (err) {
      console.error('Failed to create review room:', err);
    }
  };

  const handleResolveReview = async () => {
    if (!activeReviewRoom) return;
    try {
      await resolveReview(activeReviewRoom.room_id, 'Confirmed 30 minutes expiry as current architecture.', token);
      setActiveReviewRoom({ ...activeReviewRoom, status: 'RESOLVED' });
    } catch (err) {
      console.error('Failed to resolve review:', err);
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
                COLLABORATIVE INTELLIGENCE LAYER
              </span>
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center space-x-1">
                <Users className="w-3 h-3" />
                <span>Team Context Connected</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <MessageSquare className="w-7 h-7 text-indigo-400" />
              <span>Collaborative Intelligence & Team Memory</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Turn team conversations into structured, shared organizational memory. Detect potential decisions, tasks, and questions while preserving explicit human confirmation authority.
            </p>
          </div>

          <button
            type="button"
            onClick={handleCreateReviewRoom}
            className="px-4 py-2 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-md transition-all flex items-center space-x-1.5 flex-shrink-0"
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Open Review Room</span>
          </button>
        </div>
      </div>

      {/* Main Split Layout */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Left 2 Cols: Conversation Context & AI Suggestions */}
        <div className="md:col-span-2 space-y-5">
          
          {/* Active Conversation Context Header */}
          {context && (
            <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-3xl shadow-xl space-y-3 backdrop-blur-md">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <h3 className="text-xs font-bold text-white flex items-center space-x-2">
                  <Users className="w-4 h-4 text-indigo-400" />
                  <span>Group Discussion: {context.project_name}</span>
                </h3>
                <span className="text-[10px] font-mono text-slate-500">{context.participants.length} Active Members</span>
              </div>

              <div className="flex flex-wrap gap-2 text-[10px] font-mono">
                {context.related_files.map((f, i) => (
                  <span key={i} className="bg-slate-950 px-2.5 py-1 rounded-lg border border-slate-800 text-slate-300">
                    📄 {f}
                  </span>
                ))}
                {context.related_decisions.map((d, i) => (
                  <span key={i} className="bg-indigo-950/60 text-indigo-300 px-2.5 py-1 rounded-lg border border-indigo-800/60">
                    💡 {d}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* AI Suggestions List */}
          <div className="bg-slate-900/80 border border-indigo-800/60 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-xs font-bold text-white flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-indigo-400" />
                <span>Live AI Conversation Suggestions ({suggestions.length})</span>
              </h3>
              <span className="text-[9px] font-mono text-amber-400">Requires Confirmation</span>
            </div>

            <div className="space-y-3">
              {suggestions.map((item) => (
                <div
                  key={item.suggestion_id}
                  className={`p-4 rounded-2xl border transition-all space-y-2 ${
                    item.status === 'CONFIRMED'
                      ? 'bg-emerald-950/30 border-emerald-800/60'
                      : 'bg-slate-950 border-slate-800'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded uppercase ${
                      item.type === 'SUGGESTED_DECISION'
                        ? 'bg-indigo-950 text-indigo-400'
                        : item.type === 'SUGGESTED_TASK'
                        ? 'bg-amber-950 text-amber-400'
                        : 'bg-rose-950 text-rose-400'
                    }`}>
                      {item.type}
                    </span>

                    <span className={`text-[9px] font-mono font-bold uppercase ${
                      item.status === 'CONFIRMED' ? 'text-emerald-400' : 'text-amber-400'
                    }`}>
                      {item.status}
                    </span>
                  </div>

                  <h4 className="font-bold text-xs text-white">{item.title}</h4>
                  {item.reason && <p className="text-[11px] text-slate-300">{item.reason}</p>}
                  {item.source_message && (
                    <p className="text-[10px] font-mono text-slate-500">Source Message: "{item.source_message}"</p>
                  )}

                  {item.status !== 'CONFIRMED' && (
                    <div className="flex space-x-3 pt-2 border-t border-slate-800/80">
                      {item.type === 'SUGGESTED_DECISION' && (
                        <button
                          type="button"
                          onClick={() => handleConfirmDecision(item.suggestion_id)}
                          className="px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-md transition-all flex items-center space-x-1"
                        >
                          <Check className="w-3.5 h-3.5" />
                          <span>Confirm Decision</span>
                        </button>
                      )}
                      {item.type === 'SUGGESTED_TASK' && (
                        <button
                          type="button"
                          onClick={() => handleConfirmTask(item.suggestion_id)}
                          className="px-3.5 py-1.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs shadow-md transition-all flex items-center space-x-1"
                        >
                          <Check className="w-3.5 h-3.5" />
                          <span>Confirm Task</span>
                        </button>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

        </div>

        {/* Right Col: Knowledge Review Room & Team Digest */}
        <div className="space-y-4">
          
          {/* Active Review Room */}
          {activeReviewRoom && (
            <div className="bg-slate-900/80 border border-indigo-800/60 p-5 rounded-3xl shadow-xl space-y-3 backdrop-blur-md">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <h4 className="text-xs font-bold text-white flex items-center space-x-2">
                  <ShieldCheck className="w-4 h-4 text-indigo-400" />
                  <span>Knowledge Review Room</span>
                </h4>
                <span className="text-[9px] font-mono text-indigo-400 uppercase">{activeReviewRoom.status}</span>
              </div>

              <div className="space-y-2 text-xs">
                <h5 className="font-bold text-slate-100">{activeReviewRoom.title}</h5>
                <div className="space-y-1 text-[10px] font-mono text-slate-400 bg-slate-950 p-2 rounded-xl border border-slate-800">
                  {activeReviewRoom.conflicting_sources.map((src, i) => (
                    <div key={i}>• {src}</div>
                  ))}
                </div>

                {activeReviewRoom.status !== 'RESOLVED' && (
                  <button
                    type="button"
                    onClick={handleResolveReview}
                    className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl transition-all"
                  >
                    Confirm Resolution
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Team Digest Preview */}
          {digest && (
            <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-3xl shadow-xl space-y-3 backdrop-blur-md">
              <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
                <FileText className="w-4 h-4 text-indigo-400" />
                <h4 className="text-xs font-bold text-white">Team Digest: {digest.project_name}</h4>
              </div>

              <div className="space-y-2 text-xs">
                <div className="p-2 bg-slate-950 border border-slate-800 rounded-xl space-y-1">
                  <span className="text-[9px] font-mono font-bold text-indigo-400 uppercase">Recent Decisions</span>
                  {digest.recent_decisions.map((d, i) => (
                    <div key={i} className="text-slate-200 text-[11px] font-bold">💡 {d.title}</div>
                  ))}
                </div>

                <div className="p-2 bg-slate-950 border border-slate-800 rounded-xl space-y-1">
                  <span className="text-[9px] font-mono font-bold text-amber-400 uppercase">Unresolved Questions</span>
                  {digest.unresolved_questions.map((q, i) => (
                    <div key={i} className="text-slate-300 text-[10px]">❓ {q}</div>
                  ))}
                </div>
              </div>
            </div>
          )}

        </div>

      </div>

    </div>
  );
};
