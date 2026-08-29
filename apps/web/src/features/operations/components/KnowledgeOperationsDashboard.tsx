import React, { useState, useEffect, useCallback } from 'react';
import {
  fetchKnowledgeHealth, fetchProjectCoverage, fetchKnowledgeGaps, generateProjectHandoff,
  KnowledgeHealthResponse, ProjectCoverageProfile, KnowledgeGapItem, ProjectHandoffBrief
} from '../operations-api';
import {
  Activity, ShieldCheck, AlertTriangle, FileText, CheckCircle2, RefreshCw,
  Loader2, Layers, Search, Sparkles, Folder, FileCheck, ArrowRight, X
} from 'lucide-react';

interface KnowledgeOperationsDashboardProps {
  workspaceId?: string;
  token?: string;
}

export const KnowledgeOperationsDashboard: React.FC<KnowledgeOperationsDashboardProps> = ({
  workspaceId,
  token
}) => {
  const [health, setHealth] = useState<KnowledgeHealthResponse | null>(null);
  const [coverage, setCoverage] = useState<ProjectCoverageProfile[]>([]);
  const [gaps, setGaps] = useState<KnowledgeGapItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const [selectedHandoff, setSelectedHandoff] = useState<ProjectHandoffBrief | null>(null);
  const [isGeneratingHandoff, setIsGeneratingHandoff] = useState<boolean>(false);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [h, c, g] = await Promise.all([
        fetchKnowledgeHealth(workspaceId, token),
        fetchProjectCoverage(workspaceId, token),
        fetchKnowledgeGaps(workspaceId, token)
      ]);
      setHealth(h);
      setCoverage(c);
      setGaps(g);
    } catch (err) {
      console.error('Failed loading knowledge operations data:', err);
    } finally {
      setIsLoading(false);
    }
  }, [workspaceId, token]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleGenerateHandoff = async (projectId: string) => {
    setIsGeneratingHandoff(true);
    try {
      const brief = await generateProjectHandoff(projectId, token);
      setSelectedHandoff(brief);
    } catch (err) {
      console.error('Failed generating handoff brief:', err);
    } finally {
      setIsGeneratingHandoff(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-slate-400 space-y-3">
        <Loader2 className="w-7 h-7 animate-spin text-indigo-400" />
        <span className="text-xs font-medium">Analyzing organizational memory health & coverage...</span>
      </div>
    );
  }

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6 text-slate-100 font-sans select-none">
      
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/60 to-slate-900 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-indigo-400 px-2 py-0.5 bg-indigo-950 rounded border border-indigo-800/60">
              ORGANIZATIONAL MEMORY OBSERVABILITY
            </span>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <Activity className="w-7 h-7 text-indigo-400" />
              <span>Knowledge Operations</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Observe memory health, project documentation coverage, knowledge gaps, and generate source-backed project handoff briefs without employee surveillance.
            </p>
          </div>

          <button
            type="button"
            onClick={loadData}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors shrink-0 self-start md:self-auto"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        {/* Knowledge Health Overview Cards */}
        {health && (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 pt-2">
            <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-2xl">
              <span className="text-[10px] text-slate-500 font-medium block">Total Docs</span>
              <h4 className="text-lg font-bold text-white">{health.total_documents}</h4>
            </div>

            <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-2xl">
              <span className="text-[10px] text-slate-500 font-medium block">Verified</span>
              <h4 className="text-lg font-bold text-emerald-400">{health.verified_knowledge}</h4>
            </div>

            <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-2xl">
              <span className="text-[10px] text-slate-500 font-medium block">Needs Review</span>
              <h4 className="text-lg font-bold text-amber-400">{health.needs_review}</h4>
            </div>

            <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-2xl">
              <span className="text-[10px] text-slate-500 font-medium block">Conflicts</span>
              <h4 className="text-lg font-bold text-rose-400">{health.conflicting_knowledge}</h4>
            </div>

            <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-2xl">
              <span className="text-[10px] text-slate-500 font-medium block">Stale Docs</span>
              <h4 className="text-lg font-bold text-slate-400">{health.potentially_stale_documents}</h4>
            </div>

            <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-2xl">
              <span className="text-[10px] text-slate-500 font-medium block">Active Tasks</span>
              <h4 className="text-lg font-bold text-indigo-400">{health.total_tasks}</h4>
            </div>
          </div>
        )}
      </div>

      {/* Main Grid Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Project Coverage Section */}
        <div className="bg-slate-900/70 border border-slate-800 p-5 rounded-3xl space-y-4 shadow-md">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <div className="flex items-center space-x-2">
              <Folder className="w-5 h-5 text-indigo-400" />
              <h3 className="text-sm font-bold text-slate-100">Project Knowledge Coverage</h3>
            </div>
            <span className="text-[10px] font-mono text-slate-400">{coverage.length} Projects</span>
          </div>

          <div className="space-y-3 max-h-[420px] overflow-y-auto pr-1">
            {coverage.map((p) => (
              <div key={p.project_id} className="p-4 bg-slate-950/70 border border-slate-800/80 rounded-2xl space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-slate-100">{p.project_name}</h4>
                  <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded border ${
                    p.coverage_status === 'STRONG'
                      ? 'bg-emerald-950/60 text-emerald-400 border-emerald-800/60'
                      : 'bg-amber-950/60 text-amber-400 border-amber-800/60'
                  }`}>
                    {p.coverage_status}
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2 text-center text-[10px]">
                  <div className="bg-slate-900 p-2 rounded-xl border border-slate-800">
                    <span className="text-slate-500 block">Docs</span>
                    <span className="font-bold text-slate-200">{p.document_count}</span>
                  </div>
                  <div className="bg-slate-900 p-2 rounded-xl border border-slate-800">
                    <span className="text-slate-500 block">Decisions</span>
                    <span className="font-bold text-slate-200">{p.decision_count}</span>
                  </div>
                  <div className="bg-slate-900 p-2 rounded-xl border border-slate-800">
                    <span className="text-slate-500 block">Tasks</span>
                    <span className="font-bold text-slate-200">{p.task_count}</span>
                  </div>
                </div>

                <div className="flex justify-end">
                  <button
                    type="button"
                    onClick={() => handleGenerateHandoff(p.project_id)}
                    disabled={isGeneratingHandoff}
                    className="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-[11px] font-bold shadow-md transition-all flex items-center space-x-1.5"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Project Brief / Handoff</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Knowledge Gap & Recommendations Section */}
        <div className="bg-slate-900/70 border border-slate-800 p-5 rounded-3xl space-y-4 shadow-md">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
              <h3 className="text-sm font-bold text-slate-100">Knowledge Gaps & Recommendations</h3>
            </div>
            <span className="text-[10px] font-mono text-slate-400">{gaps.length} Signals</span>
          </div>

          <div className="space-y-3 max-h-[420px] overflow-y-auto pr-1">
            {gaps.map((gap) => (
              <div key={gap.id} className="p-4 bg-slate-950/70 border border-slate-800/80 rounded-2xl space-y-2 text-xs">
                <div className="flex items-start justify-between gap-2">
                  <span className="text-[9px] font-mono font-bold uppercase text-amber-400 px-2 py-0.5 bg-amber-950/60 rounded border border-amber-800/60">
                    {gap.gap_type}
                  </span>
                  <span className="text-[9px] font-mono text-rose-400 font-bold">{gap.severity} SEVERITY</span>
                </div>

                <h4 className="text-xs font-bold text-slate-100">{gap.title}</h4>
                <p className="text-[11px] text-slate-400">{gap.summary}</p>

                <div className="bg-indigo-950/30 border border-indigo-500/20 p-2.5 rounded-xl text-[10px] text-indigo-300 font-medium flex items-start space-x-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
                  <span>Recommendation: {gap.recommendation}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* Project Handoff Brief Modal */}
      {selectedHandoff && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 w-full max-w-2xl rounded-3xl p-6 space-y-4 max-h-[85vh] overflow-y-auto shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <Sparkles className="w-5 h-5 text-indigo-400" />
                <h3 className="text-base font-bold text-white">{selectedHandoff.project_name} — Knowledge Brief</h3>
              </div>

              <button
                type="button"
                onClick={() => setSelectedHandoff(null)}
                className="p-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-300 italic bg-slate-950 p-3 rounded-2xl border border-slate-800">
              "{selectedHandoff.overview}"
            </p>

            <div className="space-y-3 text-xs">
              <h4 className="font-bold text-indigo-400">Key Decisions ({selectedHandoff.key_decisions.length})</h4>
              <div className="space-y-1.5">
                {selectedHandoff.key_decisions.map((d) => (
                  <div key={d.id} className="p-2.5 bg-slate-950/70 border border-slate-800 rounded-xl text-slate-200">
                    • {d.content}
                  </div>
                ))}
              </div>

              <h4 className="font-bold text-indigo-400 pt-2">Active Tasks ({selectedHandoff.active_tasks.length})</h4>
              <div className="space-y-1.5">
                {selectedHandoff.active_tasks.map((t) => (
                  <div key={t.id} className="p-2.5 bg-slate-950/70 border border-slate-800 rounded-xl flex items-center justify-between text-slate-200">
                    <span>{t.title}</span>
                    <span className="text-[9px] font-mono px-2 py-0.5 bg-slate-800 rounded uppercase">{t.status}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="pt-2 text-right text-[10px] text-slate-500">
              Generated by {selectedHandoff.generated_by} on {selectedHandoff.generated_at.slice(0, 10)}
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
