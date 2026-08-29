import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchProjectIntelligence, ProjectIntelligenceResponse } from '../project-intelligence-api';
import {
  Activity, AlertTriangle, CheckCircle2, Clock, Sparkles, Loader2,
  RefreshCw, FileText, CheckSquare, MessageSquare, Network, HelpCircle,
  Briefcase, ArrowRight, ShieldCheck, AlertCircle
} from 'lucide-react';

interface ProjectIntelligenceProps {
  projectId: string;
  token?: string;
  onAskMindMesh?: (prompt: string) => void;
}

export const ProjectIntelligence: React.FC<ProjectIntelligenceProps> = ({
  projectId,
  token,
  onAskMindMesh
}) => {
  const navigate = useNavigate();
  const [data, setData] = useState<ProjectIntelligenceResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  const loadIntelligence = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await fetchProjectIntelligence(projectId, token);
      setData(res);
    } catch (err) {
      console.error('Failed to load Project Intelligence:', err);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [projectId, token]);

  useEffect(() => {
    loadIntelligence();
  }, [loadIntelligence]);

  const handleRefresh = () => {
    setIsRefreshing(true);
    loadIntelligence();
  };

  const handleAskQuestion = (question: string) => {
    const promptText = `[Project Context: ${data?.name || 'Project'}] ${question}`;
    if (onAskMindMesh) {
      onAskMindMesh(promptText);
    } else {
      navigate('/ask', { state: { initialPrompt: promptText } });
    }
  };

  const getHealthBadge = (status: string) => {
    switch (status.toUpperCase()) {
      case 'HEALTHY':
        return (
          <span className="px-3 py-1 rounded-xl text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center space-x-1.5">
            <CheckCircle2 className="w-4 h-4" />
            <span>HEALTHY</span>
          </span>
        );
      case 'AT_RISK':
        return (
          <span className="px-3 py-1 rounded-xl text-xs font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20 flex items-center space-x-1.5">
            <AlertTriangle className="w-4 h-4" />
            <span>AT RISK</span>
          </span>
        );
      case 'ATTENTION':
      default:
        return (
          <span className="px-3 py-1 rounded-xl text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center space-x-1.5">
            <AlertCircle className="w-4 h-4" />
            <span>NEEDS ATTENTION</span>
          </span>
        );
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-slate-400 space-y-3">
        <Loader2 className="w-7 h-7 animate-spin text-indigo-400" />
        <span className="text-xs font-medium">Synthesizing project intelligence...</span>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-8 text-center text-slate-400 text-xs bg-slate-900/40 border border-slate-800 rounded-3xl space-y-2">
        <AlertTriangle className="w-8 h-8 text-amber-400 mx-auto" />
        <p>Project intelligence could not be loaded.</p>
        <button
          type="button"
          onClick={loadIntelligence}
          className="px-4 py-2 rounded-xl bg-slate-800 text-slate-200 text-xs font-semibold"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6 text-slate-100 select-none">
      
      {/* Header & Health Section */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/60 to-slate-900 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-indigo-400 px-2 py-0.5 bg-indigo-950 rounded border border-indigo-800/60">
                PROJECT INTELLIGENCE
              </span>
              <span className="text-[10px] font-mono text-slate-400 uppercase px-2 py-0.5 bg-slate-800 rounded border border-slate-700">
                STATUS: {data.status}
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <Briefcase className="w-7 h-7 text-indigo-400" />
              <span>{data.name}</span>
            </h1>
          </div>

          <div className="flex items-center space-x-3 shrink-0">
            {getHealthBadge(data.health.status)}

            <button
              type="button"
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Health Explanation Banner */}
        <div className="bg-slate-950/70 border border-slate-800/80 p-3.5 rounded-2xl flex items-start space-x-3 text-xs">
          <ShieldCheck className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold text-slate-200">Health Signal: </span>
            <span className="text-slate-300">{data.health.explanation}</span>
          </div>
        </div>
      </div>

      {/* Current State & Task Summary Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Current State (2 cols) */}
        <div className="md:col-span-2 bg-slate-900/70 border border-slate-800 p-5 rounded-3xl space-y-3 shadow-md">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-2">
            <Activity className="w-4 h-4 text-indigo-400" />
            <span>Current Project State</span>
          </h3>
          <p className="text-xs text-slate-200 bg-slate-950/60 p-4 rounded-2xl border border-slate-800 leading-relaxed font-medium">
            {data.current_state}
          </p>

          {/* Preset Contextual Question Chips */}
          <div className="pt-2">
            <span className="text-[10px] text-slate-500 font-mono block mb-2">Ask MindMesh about this project:</span>
            <div className="flex flex-wrap gap-2">
              {[
                'Why is this project flagged for attention?',
                'What should we focus on next?',
                'What changed in authentication?',
                'What decisions were made?'
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

        {/* Task Breakdown Metrics (1 col) */}
        <div className="bg-slate-900/70 border border-slate-800 p-5 rounded-3xl space-y-4 shadow-md">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-2">
            <CheckSquare className="w-4 h-4 text-amber-400" />
            <span>Task Breakdown</span>
          </h3>

          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-2xl">
              <span className="text-[10px] text-slate-500 font-medium">Open</span>
              <h4 className="text-lg font-bold text-white">{data.task_summary.open}</h4>
            </div>

            <div className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-2xl">
              <span className="text-[10px] text-slate-500 font-medium">In Progress</span>
              <h4 className="text-lg font-bold text-blue-400">{data.task_summary.in_progress}</h4>
            </div>

            <div className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-2xl">
              <span className="text-[10px] text-slate-500 font-medium">Blocked</span>
              <h4 className="text-lg font-bold text-rose-400">{data.task_summary.blocked}</h4>
            </div>

            <div className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-2xl">
              <span className="text-[10px] text-slate-500 font-medium">Overdue</span>
              <h4 className="text-lg font-bold text-amber-400">{data.task_summary.overdue}</h4>
            </div>
          </div>
        </div>

      </div>

      {/* Decisions & Timeline Split */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Key Decisions */}
        <div className="bg-slate-900/70 border border-slate-800 p-5 rounded-3xl space-y-3 shadow-md">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>Key Decisions</span>
          </h3>

          <div className="space-y-2.5 max-h-[300px] overflow-y-auto">
            {data.key_decisions.length === 0 ? (
              <p className="text-xs text-slate-500 py-4 text-center">No explicit decisions recorded yet.</p>
            ) : (
              data.key_decisions.map((d) => (
                <div key={d.id} className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-xl space-y-1">
                  <p className="text-xs font-semibold text-slate-200">{d.content}</p>
                  <span className="text-[9px] text-slate-500 font-mono">Recorded: {d.created_at ? d.created_at.slice(0, 10) : ''}</span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Recent Changes Timeline */}
        <div className="bg-slate-900/70 border border-slate-800 p-5 rounded-3xl space-y-3 shadow-md">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center space-x-2">
              <Clock className="w-4 h-4 text-indigo-400" />
              <span>Recent Changes</span>
            </h3>

            <button
              type="button"
              onClick={() => navigate('/timeline')}
              className="text-[11px] font-semibold text-indigo-400 hover:text-indigo-300 flex items-center space-x-1"
            >
              <span>View Timeline</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </div>

          <div className="space-y-2.5 max-h-[300px] overflow-y-auto">
            {data.recent_changes.length === 0 ? (
              <p className="text-xs text-slate-500 py-4 text-center">No recent project changes.</p>
            ) : (
              data.recent_changes.map((c) => (
                <div key={c.id} className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-xl space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-[9px] font-mono font-bold uppercase text-indigo-400">{c.event_type}</span>
                    <span className="text-[9px] text-slate-500 font-mono">{c.occurred_at ? c.occurred_at.slice(0, 10) : ''}</span>
                  </div>
                  <h5 className="text-xs font-semibold text-slate-200">{c.title}</h5>
                </div>
              ))
            )}
          </div>
        </div>

      </div>

    </div>
  );
};
