import React, { useState, useEffect } from 'react';
import {
  fetchPersonalContext, fetchFocusRecommendations, fetchAwaySummary, pinProject, unpinProject,
  UserPersonalContextResponse, FocusRecommendationItem, AwaySummaryResponse
} from '../personal-context-api';
import {
  UserCheck, Sparkles, Pin, PinOff, CheckSquare, AlertCircle, Clock, ShieldCheck, ArrowRight, Layers, Sliders, ToggleLeft, ToggleRight
} from 'lucide-react';

interface MyMindMeshCenterProps {
  activeProjectId?: string;
  token?: string;
}

export const MyMindMeshCenter: React.FC<MyMindMeshCenterProps> = ({
  activeProjectId,
  token
}) => {
  const [contextData, setContextData] = useState<UserPersonalContextResponse | null>(null);
  const [focusRecs, setFocusRecs] = useState<FocusRecommendationItem[]>([]);
  const [awaySummary, setAwaySummary] = useState<AwaySummaryResponse | null>(null);
  const [personalizationEnabled, setPersonalizationEnabled] = useState<boolean>(true);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    async function loadPersonalContext() {
      setIsLoading(true);
      try {
        const [cRes, fRes, aRes] = await Promise.all([
          fetchPersonalContext(activeProjectId, token),
          fetchFocusRecommendations(activeProjectId, token),
          fetchAwaySummary(token)
        ]);
        setContextData(cRes);
        setFocusRecs(fRes);
        setAwaySummary(aRes);
      } catch (err) {
        console.error('Failed to load personal context:', err);
      } finally {
        setIsLoading(false);
      }
    }
    loadPersonalContext();
  }, [activeProjectId, token]);

  const handleTogglePin = async (pId: string, isPinned: boolean) => {
    try {
      if (isPinned) {
        await unpinProject(pId, token);
      } else {
        await pinProject(pId, token);
      }
      const updated = await fetchPersonalContext(activeProjectId, token);
      setContextData(updated);
    } catch (err) {
      console.error('Failed to toggle pin:', err);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6 text-slate-100 font-sans select-none">
      
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/70 to-slate-900 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-indigo-400 px-2 py-0.5 bg-indigo-950 rounded border border-indigo-800/60">
              MY MINDSMESH PERSONAL DASHBOARD
            </span>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <UserCheck className="w-7 h-7 text-indigo-400" />
              <span>Personal Context & Focus</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Personalized knowledge relevance tailored to your active work, assigned tasks, and pinned projects—with 100% zero employee surveillance or productivity scoring.
            </p>
          </div>

          <div className="flex items-center space-x-3 bg-slate-950/80 p-3 rounded-2xl border border-slate-800">
            <span className="text-xs text-slate-300 font-semibold">Personalization</span>
            <button
              type="button"
              onClick={() => setPersonalizationEnabled(!personalizationEnabled)}
              className="text-indigo-400 hover:text-indigo-300 transition-all"
            >
              {personalizationEnabled ? <ToggleRight className="w-7 h-7" /> : <ToggleLeft className="w-7 h-7 text-slate-600" />}
            </button>
          </div>
        </div>

        {/* Current Active Context Pill */}
        {contextData && (
          <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-800/80 text-xs">
            <span className="text-slate-400 font-mono">Active Project:</span>
            <span className="font-bold text-white bg-indigo-950 px-2.5 py-1 rounded-xl border border-indigo-800/60">
              {contextData.active_project_name}
            </span>

            <span className="text-slate-400 font-mono ml-4">Assigned Tasks:</span>
            <span className="font-bold text-indigo-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800 font-mono">
              {contextData.assigned_tasks_count}
            </span>
          </div>
        )}
      </div>

      {/* Main Dashboard Layout */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Left Column: Focus Section */}
        <div className="md:col-span-2 space-y-4">
          <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <Sparkles className="w-5 h-5 text-indigo-400" />
                <h3 className="text-sm font-bold text-white">What Needs Your Attention?</h3>
              </div>
              <span className="text-[9px] font-mono text-slate-400">Grounded Recommendations</span>
            </div>

            <div className="space-y-3">
              {focusRecs.map((rec) => (
                <div
                  key={rec.id}
                  className="p-4 bg-slate-950 border border-slate-800 hover:border-indigo-800/60 rounded-2xl flex items-center justify-between transition-all"
                >
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded uppercase ${
                        rec.priority === 'HIGH' ? 'bg-rose-950 text-rose-400 border border-rose-800/60' : 'bg-slate-800 text-slate-300'
                      }`}>
                        {rec.priority}
                      </span>
                      <h4 className="font-bold text-slate-100 text-xs">{rec.title}</h4>
                    </div>
                    <p className="text-[11px] text-slate-400">{rec.reason}</p>
                  </div>

                  <button
                    type="button"
                    className="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-[10px] shadow-md flex items-center space-x-1"
                  >
                    <span>Action</span>
                    <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Away Summary Section */}
          {awaySummary && (
            <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-3xl shadow-xl space-y-3 backdrop-blur-md">
              <div className="flex items-center space-x-2 border-b border-slate-800 pb-3">
                <Clock className="w-5 h-5 text-indigo-400" />
                <h3 className="text-sm font-bold text-white">While You Were Away</h3>
              </div>

              <div className="space-y-2">
                {awaySummary.summary_items.map((item, idx) => (
                  <div key={idx} className="p-3 bg-slate-950 border border-slate-800/80 rounded-2xl flex items-center justify-between text-xs">
                    <div>
                      <span className="text-[9px] font-mono text-indigo-400 bg-indigo-950 px-2 py-0.5 rounded">
                        {item.project_name}
                      </span>
                      <h5 className="font-bold text-slate-200 mt-1">{item.title}</h5>
                      <p className="text-[11px] text-slate-400">{item.reason}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Context Signals & Priority */}
        <div className="space-y-4">
          
          {/* Signal Priority Explanation */}
          <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-3xl shadow-xl space-y-3 backdrop-blur-md">
            <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
              <Layers className="w-4 h-4 text-indigo-400" />
              <h4 className="text-xs font-bold text-white">Context Signal Priority</h4>
            </div>

            <ol className="space-y-1.5 text-[11px] text-slate-300 font-mono">
              {contextData?.context_priority.map((p, idx) => (
                <li key={idx} className="flex items-center space-x-2 bg-slate-950 p-2 rounded-xl border border-slate-800/60">
                  <span className="w-4 h-4 rounded-full bg-indigo-950 text-indigo-400 text-[9px] font-bold flex items-center justify-center">
                    {idx + 1}
                  </span>
                  <span>{p}</span>
                </li>
              ))}
            </ol>
          </div>

          {/* Assigned Tasks Summary */}
          <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-3xl shadow-xl space-y-3 backdrop-blur-md">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <div className="flex items-center space-x-2">
                <CheckSquare className="w-4 h-4 text-indigo-400" />
                <h4 className="text-xs font-bold text-white">Assigned Tasks</h4>
              </div>
              <span className="text-[10px] font-mono text-indigo-400 font-bold">{contextData?.assigned_tasks.length || 0} Tasks</span>
            </div>

            <div className="space-y-2">
              {contextData?.assigned_tasks.map((t) => (
                <div key={t.id} className="p-2.5 bg-slate-950 border border-slate-800 rounded-xl text-xs space-y-1">
                  <h5 className="font-bold text-slate-200">{t.title}</h5>
                  <span className="text-[9px] font-mono uppercase px-1.5 py-0.2 bg-slate-800 text-slate-400 rounded">
                    Status: {t.status}
                  </span>
                </div>
              ))}
            </div>
          </div>

        </div>

      </div>

    </div>
  );
};
