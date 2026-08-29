import React, { useState } from 'react';
import { WorkflowDetailsResponse, approveWorkflow, pauseWorkflow, resumeWorkflow } from '../workflows-api';
import {
  Workflow, CheckCircle2, Play, Pause, AlertCircle, Clock, ArrowRight, Loader2, Sparkles, X, ShieldAlert
} from 'lucide-react';

interface AgenticWorkflowCardProps {
  workflow: WorkflowDetailsResponse;
  token?: string;
  onUpdated?: (updatedWf: WorkflowDetailsResponse) => void;
}

export const AgenticWorkflowCard: React.FC<AgenticWorkflowCardProps> = ({
  workflow,
  token,
  onUpdated
}) => {
  const [currentWf, setCurrentWf] = useState<WorkflowDetailsResponse>(workflow);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const handleApproveAndRun = async () => {
    setIsLoading(true);
    try {
      const updated = await approveWorkflow(currentWf.id, undefined, token);
      setCurrentWf(updated);
      if (onUpdated) onUpdated(updated);
    } catch (err) {
      console.error('Failed to approve workflow:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePause = async () => {
    setIsLoading(true);
    try {
      const updated = await pauseWorkflow(currentWf.id, token);
      setCurrentWf(updated);
      if (onUpdated) onUpdated(updated);
    } catch (err) {
      console.error('Failed to pause workflow:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResume = async () => {
    setIsLoading(true);
    try {
      const updated = await resumeWorkflow(currentWf.id, token);
      setCurrentWf(updated);
      if (onUpdated) onUpdated(updated);
    } catch (err) {
      console.error('Failed to resume workflow:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full bg-slate-900/80 border border-slate-800 p-5 rounded-3xl space-y-4 font-sans text-xs shadow-xl backdrop-blur-md">
      
      {/* Workflow Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
        <div>
          <span className="text-[9px] font-mono font-bold uppercase text-indigo-400 px-2 py-0.5 bg-indigo-950/80 rounded border border-indigo-800/60 flex items-center space-x-1 w-fit">
            <Workflow className="w-3 h-3 text-indigo-400" />
            <span>AGENTIC WORKFLOW ORCHESTRATION</span>
          </span>
          <h3 className="text-base font-bold text-white mt-1">{currentWf.goal}</h3>
        </div>

        <div className="flex items-center space-x-2">
          <span className={`text-[10px] font-mono font-bold px-2.5 py-1 rounded-xl uppercase border ${
            currentWf.status === 'COMPLETED'
              ? 'bg-emerald-950 text-emerald-400 border-emerald-800/60'
              : currentWf.status === 'RUNNING'
              ? 'bg-indigo-950 text-indigo-400 border-indigo-800/60'
              : currentWf.status === 'PAUSED' || currentWf.status === 'WAITING_FOR_APPROVAL'
              ? 'bg-amber-950 text-amber-400 border-amber-800/60'
              : 'bg-slate-800 text-slate-300 border-slate-700'
          }`}>
            {currentWf.status.replace('_', ' ')}
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
          <span>Progress: {currentWf.completed_steps} / {currentWf.total_steps} Steps</span>
          <span>{currentWf.progress_pct}%</span>
        </div>

        <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
          <div
            className="bg-gradient-to-r from-indigo-500 to-emerald-400 h-2 transition-all duration-500 rounded-full"
            style={{ width: `${currentWf.progress_pct}%` }}
          />
        </div>
      </div>

      {/* Workflow Step Sequence */}
      <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
        {currentWf.steps.map((s) => (
          <div
            key={s.id}
            className="p-3 bg-slate-950/70 border border-slate-800 rounded-2xl flex items-center justify-between text-xs"
          >
            <div className="space-y-0.5">
              <div className="flex items-center space-x-2">
                <span className="text-[9px] font-mono font-bold text-slate-500">
                  STEP #{s.step_index}
                </span>
                <span className="font-bold text-slate-200">{s.title}</span>
              </div>
              <p className="text-[11px] text-slate-400">{s.description}</p>
            </div>

            <div>
              <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${
                s.status === 'COMPLETED'
                  ? 'bg-emerald-950 text-emerald-400 border-emerald-800/60'
                  : s.status === 'RUNNING'
                  ? 'bg-indigo-950 text-indigo-400 border-indigo-800/60 animate-pulse'
                  : s.status === 'READY'
                  ? 'bg-amber-950 text-amber-400 border-amber-800/60'
                  : 'bg-slate-900 text-slate-500 border-slate-800'
              }`}>
                {s.status}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Interactive Controls */}
      <div className="flex items-center justify-end space-x-2 pt-2 border-t border-slate-800">
        {currentWf.status === 'WAITING_FOR_APPROVAL' && (
          <button
            type="button"
            onClick={handleApproveAndRun}
            disabled={isLoading}
            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-md transition-all flex items-center space-x-1.5"
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            <span>Approve & Run Plan</span>
          </button>
        )}

        {currentWf.status === 'RUNNING' && (
          <button
            type="button"
            onClick={handlePause}
            disabled={isLoading}
            className="px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs shadow-md transition-all flex items-center space-x-1.5"
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Pause className="w-4 h-4" />}
            <span>Pause Workflow</span>
          </button>
        )}

        {currentWf.status === 'PAUSED' && (
          <button
            type="button"
            onClick={handleResume}
            disabled={isLoading}
            className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-md transition-all flex items-center space-x-1.5"
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            <span>Resume Execution</span>
          </button>
        )}
      </div>

    </div>
  );
};
