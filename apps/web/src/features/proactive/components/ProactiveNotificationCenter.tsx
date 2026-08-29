import React, { useState, useEffect } from 'react';
import { fetchProactiveInsights, markInsightsRead, dismissInsight, ProactiveInsightItem, UserInsightsResponse } from '../proactive-intelligence-api';
import {
  Bell, Sparkles, AlertTriangle, CheckCircle2, Info, ArrowRight, ExternalLink, CheckCheck, X, ShieldAlert, Filter
} from 'lucide-react';

interface ProactiveNotificationCenterProps {
  workspaceId?: string;
  token?: string;
}

export const ProactiveNotificationCenter: React.FC<ProactiveNotificationCenterProps> = ({
  workspaceId,
  token
}) => {
  const [data, setData] = useState<UserInsightsResponse | null>(null);
  const [activeFilter, setActiveFilter] = useState<string>('ALL');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const loadInsights = async () => {
    setIsLoading(true);
    try {
      const res = await fetchProactiveInsights(activeFilter, workspaceId, token);
      setData(res);
    } catch (err) {
      console.error('Failed to load proactive insights:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadInsights();
  }, [activeFilter, workspaceId, token]);

  const handleMarkAllRead = async () => {
    if (!data) return;
    const unreadIds = data.insights.filter((i) => i.status === 'UNREAD').map((i) => i.id);
    if (unreadIds.length === 0) return;
    try {
      await markInsightsRead(unreadIds, token);
      loadInsights();
    } catch (err) {
      console.error('Failed to mark all read:', err);
    }
  };

  const handleDismiss = async (insightId: string) => {
    try {
      await dismissInsight(insightId, token);
      loadInsights();
    } catch (err) {
      console.error('Failed to dismiss insight:', err);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6 text-slate-100 font-sans select-none">
      
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/70 to-slate-900 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-indigo-400 px-2 py-0.5 bg-indigo-950 rounded border border-indigo-800/60">
                PROACTIVE ANTICIPATORY INTELLIGENCE
              </span>
              {data && data.unread_count > 0 && (
                <span className="text-[10px] font-mono font-bold text-white bg-rose-600 px-2 py-0.5 rounded-full shadow-md animate-pulse">
                  {data.unread_count} Unread
                </span>
              )}
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <Bell className="w-7 h-7 text-indigo-400" />
              <span>Proactive Notification Center</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              MindMesh surfaces critical project decisions, assigned task updates, deadlines, and knowledge conflicts automatically before you search for them.
            </p>
          </div>

          <button
            type="button"
            onClick={handleMarkAllRead}
            className="px-4 py-2 rounded-2xl bg-slate-800 hover:bg-slate-700 text-indigo-400 font-bold text-xs shadow-md transition-all flex items-center space-x-1.5"
          >
            <CheckCheck className="w-4 h-4" />
            <span>Mark All as Read</span>
          </button>
        </div>

        {/* Filter Pills */}
        <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-800/80">
          {(['ALL', 'CRITICAL', 'IMPORTANT', 'TASK_ASSIGNED', 'DECISION_UPDATED', 'BLOCKER_CREATED'] as const).map((flt) => (
            <button
              key={flt}
              type="button"
              onClick={() => setActiveFilter(flt)}
              className={`px-3 py-1 rounded-xl text-xs font-bold transition-all ${
                activeFilter === flt
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
              }`}
            >
              {flt}
            </button>
          ))}
        </div>
      </div>

      {/* Insights List */}
      <div className="space-y-3">
        {!data || data.insights.length === 0 ? (
          <div className="py-16 text-center space-y-2 bg-slate-900/40 border border-slate-800/60 rounded-3xl">
            <Bell className="w-8 h-8 text-slate-600 mx-auto" />
            <h4 className="text-xs font-bold text-slate-300">No proactive insights available right now</h4>
            <p className="text-[11px] text-slate-500">MindMesh will notify you when meaningful project changes directly affect your work.</p>
          </div>
        ) : (
          data.insights.map((item) => (
            <div
              key={item.id}
              className={`p-5 rounded-3xl border transition-all space-y-3 shadow-lg ${
                item.status === 'UNREAD'
                  ? 'bg-slate-900/90 border-indigo-800/80 shadow-indigo-950/30'
                  : 'bg-slate-900/50 border-slate-800/80 opacity-90'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${
                    item.importance === 'CRITICAL'
                      ? 'bg-rose-950 text-rose-400 border-rose-800/60'
                      : item.importance === 'IMPORTANT'
                      ? 'bg-amber-950 text-amber-400 border-amber-800/60'
                      : 'bg-indigo-950 text-indigo-400 border-indigo-800/60'
                  }`}>
                    {item.importance}
                  </span>

                  <span className="text-[9px] font-mono text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                    Project: {item.project_name}
                  </span>
                </div>

                <div className="flex items-center space-x-2">
                  <span className="text-[10px] text-slate-500 font-mono">
                    {new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                  <button
                    type="button"
                    onClick={() => handleDismiss(item.id)}
                    className="text-slate-500 hover:text-slate-300 p-1"
                    title="Dismiss Notification"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>

              <div>
                <h3 className="text-sm font-bold text-slate-100">{item.title}</h3>
                <p className="text-xs text-slate-300 mt-1">{item.description}</p>
              </div>

              {/* Context Explanation */}
              <div className="p-2.5 bg-slate-950/80 rounded-xl border border-slate-800 flex items-center space-x-2 text-[11px] text-slate-400 italic">
                <Info className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0" />
                <span>Why am I seeing this? {item.context_explanation}</span>
              </div>

              {/* Action Button */}
              {item.action_payload && (
                <div className="flex justify-end pt-1">
                  <button
                    type="button"
                    className="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-[10px] shadow-md flex items-center space-x-1"
                  >
                    <span>{item.action_payload.label}</span>
                    <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
              )}
            </div>
          ))
        )}
      </div>

    </div>
  );
};
