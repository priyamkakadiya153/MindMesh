import React, { useState, useEffect } from 'react';
import {
  fetchInsights, fetchKnowledgeEvolution, confirmInsight, dismissInsight, fetchReuseSuggestions, rebuildInsights,
  InsightItem, KnowledgeEvolutionResponse, ReuseSuggestionItem
} from '../organizational-learning-api';
import {
  Lightbulb, History, Sparkles, CheckCircle2, XCircle, RefreshCw, FileText, ArrowRight, CornerDownRight, ShieldCheck, Activity, Layers, Bookmark
} from 'lucide-react';

interface OrganizationalLearningDashboardProps {
  initialProjectId?: string;
  token?: string;
}

export const OrganizationalLearningDashboard: React.FC<OrganizationalLearningDashboardProps> = ({
  initialProjectId = 'proj-auth-id',
  token
}) => {
  const [insights, setInsights] = useState<InsightItem[]>([]);
  const [evolution, setEvolution] = useState<KnowledgeEvolutionResponse | null>(null);
  const [reuseSuggestions, setReuseSuggestions] = useState<ReuseSuggestionItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const loadAllData = async () => {
    setIsLoading(true);
    try {
      const [insRes, evoRes, reRes] = await Promise.all([
        fetchInsights(initialProjectId, token).catch(() => []),
        fetchKnowledgeEvolution('DECISION', '70f1236a-7280-4167-8ed3-22bbb857509c', token).catch(() => null),
        fetchReuseSuggestions('Authentication', token).catch(() => [])
      ]);
      setInsights(insRes);
      if (evoRes) setEvolution(evoRes);
      setReuseSuggestions(reRes);
    } catch (err) {
      console.error('Failed to load learning data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAllData();
  }, [initialProjectId, token]);

  const handleConfirmInsight = async (insId: string) => {
    try {
      await confirmInsight(insId, token);
      setInsights((prev) => prev.map((i) => i.insight_id === insId ? { ...i, status: 'CONFIRMED' } : i));
    } catch (err) {
      console.error('Failed to confirm insight:', err);
    }
  };

  const handleDismissInsight = async (insId: string) => {
    try {
      await dismissInsight(insId, token);
      setInsights((prev) => prev.map((i) => i.insight_id === insId ? { ...i, status: 'DISMISSED' } : i));
    } catch (err) {
      console.error('Failed to dismiss insight:', err);
    }
  };

  const handleRebuild = async () => {
    try {
      await rebuildInsights(token);
      loadAllData();
    } catch (err) {
      console.error('Failed to rebuild insights:', err);
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
                ORGANIZATIONAL LEARNING LAYER
              </span>
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center space-x-1">
                <ShieldCheck className="w-3 h-3" />
                <span>No Employee Profiling / Surveillance</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <Lightbulb className="w-7 h-7 text-indigo-400" />
              <span>Organizational Learning & Knowledge Evolution</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Observe how knowledge changes over time, identify document volatility, discover historical reuse patterns, and build long-term organizational wisdom.
            </p>
          </div>

          <button
            type="button"
            onClick={handleRebuild}
            className="px-4 py-2 rounded-2xl bg-slate-800 hover:bg-slate-700 text-indigo-400 font-bold text-xs shadow-md transition-all flex items-center space-x-1.5 flex-shrink-0"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Rebuild Insights</span>
          </button>
        </div>
      </div>

      {/* Main Split Layout */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Left 2 Cols: Derived Organizational Insights */}
        <div className="md:col-span-2 space-y-5">
          
          <div className="bg-slate-900/80 border border-indigo-800/60 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-xs font-bold text-white flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-indigo-400" />
                <span>Derived Organizational Insights ({insights.length})</span>
              </h3>
              <span className="text-[9px] font-mono text-slate-500">Derived from Primary Evidence</span>
            </div>

            <div className="space-y-4">
              {insights.map((item) => (
                <div
                  key={item.insight_id}
                  className={`p-4 rounded-2xl border transition-all space-y-3 ${
                    item.status === 'CONFIRMED'
                      ? 'bg-emerald-950/30 border-emerald-800/60'
                      : item.status === 'DISMISSED'
                      ? 'bg-rose-950/20 border-rose-800/40 opacity-60'
                      : 'bg-slate-950 border-slate-800'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="text-[10px] font-mono font-bold text-indigo-400 bg-slate-900 px-2 py-0.5 rounded">
                        {item.type}
                      </span>
                      <span className="text-[9px] font-mono font-bold text-amber-400 bg-amber-950 px-2 py-0.5 rounded uppercase">
                        {item.confidence}
                      </span>
                    </div>

                    <span className={`text-[9px] font-mono font-bold uppercase ${
                      item.status === 'CONFIRMED' ? 'text-emerald-400' : 'text-amber-400'
                    }`}>
                      {item.status}
                    </span>
                  </div>

                  <div>
                    <h4 className="font-bold text-xs text-white">{item.title}</h4>
                    <p className="text-[11px] text-slate-300 mt-0.5">{item.statement}</p>
                    <p className="text-[10px] font-mono text-slate-500 mt-1">
                      Evidence: {item.evidence.join(' • ')}
                    </p>
                  </div>

                  {item.status === 'DETECTED' && (
                    <div className="flex space-x-3 pt-2 border-t border-slate-800/80">
                      <button
                        type="button"
                        onClick={() => handleConfirmInsight(item.insight_id)}
                        className="px-4 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-md transition-all flex items-center space-x-1"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Confirm Insight</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDismissInsight(item.insight_id)}
                        className="px-4 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-rose-400 font-bold text-xs shadow-md transition-all flex items-center space-x-1"
                      >
                        <XCircle className="w-3.5 h-3.5" />
                        <span>Dismiss</span>
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

        </div>

        {/* Right Col: Knowledge Evolution & Historical Reuse Suggestions */}
        <div className="space-y-4">
          
          {/* Knowledge Evolution Timeline */}
          {evolution && (
            <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-3xl shadow-xl space-y-3 backdrop-blur-md">
              <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
                <History className="w-4 h-4 text-indigo-400" />
                <h4 className="text-xs font-bold text-white">Decision Evolution Progression</h4>
              </div>

              <div className="space-y-2 font-mono text-[10px]">
                {evolution.history.map((rev) => (
                  <div key={rev.version} className="p-2 bg-slate-950 border border-slate-800 rounded-xl space-y-0.5">
                    <span className="text-indigo-400 font-bold">v{rev.version}: {rev.value}</span>
                    <span className="text-slate-500 block">Source: {rev.source}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Historical Reuse Suggestions */}
          {reuseSuggestions.length > 0 && (
            <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-3xl shadow-xl space-y-3 backdrop-blur-md">
              <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
                <Bookmark className="w-4 h-4 text-amber-400" />
                <h4 className="text-xs font-bold text-white">Historical Knowledge Reuse</h4>
              </div>

              <div className="space-y-2 text-xs">
                {reuseSuggestions.map((item) => (
                  <div key={item.id} className="p-2.5 bg-slate-950 border border-slate-800 rounded-xl space-y-1">
                    <span className="text-[8px] font-mono font-bold text-amber-400 bg-amber-950 px-2 py-0.5 rounded uppercase">
                      {item.label}
                    </span>
                    <h5 className="font-bold text-slate-100 text-[11px]">{item.title}</h5>
                    <p className="text-[10px] text-slate-400">{item.relevance_summary}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>

      </div>

    </div>
  );
};
