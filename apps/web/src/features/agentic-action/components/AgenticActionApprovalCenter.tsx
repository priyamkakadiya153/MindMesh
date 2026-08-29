import React, { useState, useEffect } from 'react';
import {
  proposeActionPlan, fetchPendingApprovals, approveAction, rejectAction, fetchActionLog,
  ActionPlan, PendingApprovalItem, ActionLogItem
} from '../agentic-action-api';
import {
  ShieldAlert, Sparkles, CheckCircle2, XCircle, Play, AlertTriangle, Layers, Activity, FileText, ArrowRight, CornerDownRight
} from 'lucide-react';

interface AgenticActionApprovalCenterProps {
  initialProjectId?: string;
  token?: string;
}

export const AgenticActionApprovalCenter: React.FC<AgenticActionApprovalCenterProps> = ({
  initialProjectId = 'proj-auth-id',
  token
}) => {
  const [goalInput, setGoalInput] = useState<string>('Prepare the authentication project for release.');
  const [currentPlan, setCurrentPlan] = useState<ActionPlan | null>(null);
  const [pendingApprovals, setPendingApprovals] = useState<PendingApprovalItem[]>([]);
  const [actionLogs, setActionLogs] = useState<ActionLogItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const loadApprovalsAndLogs = async () => {
    try {
      const [appRes, logRes] = await Promise.all([
        fetchPendingApprovals(token).catch(() => []),
        fetchActionLog(token).catch(() => [])
      ]);
      setPendingApprovals(appRes);
      setActionLogs(logRes);
    } catch (err) {
      console.error('Failed to load approvals:', err);
    }
  };

  useEffect(() => {
    loadApprovalsAndLogs();
  }, [token]);

  const handleProposePlan = async () => {
    if (!goalInput.strip && !goalInput) return;
    setIsLoading(true);
    try {
      const plan = await proposeActionPlan(goalInput, initialProjectId, token);
      setCurrentPlan(plan);
      loadApprovalsAndLogs();
    } catch (err) {
      console.error('Failed to propose action plan:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApprove = async (planId: string, actionId: string) => {
    try {
      await approveAction(planId, actionId, token);
      loadApprovalsAndLogs();
      if (currentPlan && currentPlan.plan_id === planId) {
        const updatedSteps = currentPlan.steps.map((s) => s.action_id === actionId ? { ...s, status: 'COMPLETED' } : s);
        setCurrentPlan({ ...currentPlan, steps: updatedSteps });
      }
    } catch (err) {
      console.error('Failed to approve action:', err);
    }
  };

  const handleReject = async (planId: string, actionId: string) => {
    try {
      await rejectAction(planId, actionId, token);
      loadApprovalsAndLogs();
      if (currentPlan && currentPlan.plan_id === planId) {
        const updatedSteps = currentPlan.steps.map((s) => s.action_id === actionId ? { ...s, status: 'REJECTED' } : s);
        setCurrentPlan({ ...currentPlan, steps: updatedSteps });
      }
    } catch (err) {
      console.error('Failed to reject action:', err);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6 text-slate-100 font-sans select-none">
      
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/80 to-slate-900 border border-indigo-800/60 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-indigo-400 px-2.5 py-0.5 bg-indigo-950 rounded border border-indigo-800/60">
                CONTROLLED EXECUTION ENGINE
              </span>
              <span className="text-[10px] font-mono font-bold text-amber-400 bg-amber-950 px-2 py-0.5 rounded border border-amber-800/60 flex items-center space-x-1">
                <ShieldAlert className="w-3 h-3" />
                <span>Human Approval Required</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <Play className="w-7 h-7 text-indigo-400" />
              <span>Agentic Action Approval Center</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              AI proposes structured multi-step plans. Human approval remains the final authority before executing any consequential action.
            </p>
          </div>
        </div>

        {/* Goal Input Bar */}
        <div className="space-y-3 pt-3 border-t border-slate-800/80">
          <div className="flex items-center space-x-2">
            <input
              type="text"
              value={goalInput}
              onChange={(e) => setGoalInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleProposePlan()}
              placeholder="Enter goal for MindMesh (e.g. 'Prepare the authentication project for release.')"
              className="w-full bg-slate-950 border border-slate-800 rounded-2xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-medium"
            />
            <button
              type="button"
              onClick={handleProposePlan}
              disabled={isLoading}
              className="px-5 py-2.5 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-md transition-all flex items-center space-x-1.5 flex-shrink-0 disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4" />
              <span>{isLoading ? 'Planning...' : 'Propose Plan'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Split Layout */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Left 2 Cols: Active Proposed Plan & Steps */}
        <div className="md:col-span-2 space-y-4">
          
          {currentPlan && (
            <div className="bg-slate-900/80 border border-indigo-800/60 p-6 rounded-3xl shadow-xl space-y-5 backdrop-blur-md">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div>
                  <span className="text-[10px] font-mono font-bold text-indigo-400 uppercase">PROPOSED ACTION PLAN</span>
                  <h3 className="text-sm font-bold text-white mt-0.5">{currentPlan.goal}</h3>
                </div>
                <span className="text-[10px] font-mono font-bold text-amber-400 bg-amber-950 px-2 py-0.5 rounded border border-amber-800">
                  {currentPlan.status}
                </span>
              </div>

              {/* Step Cards */}
              <div className="space-y-4">
                {currentPlan.steps.map((step) => (
                  <div
                    key={step.action_id}
                    className={`p-4 rounded-2xl border transition-all space-y-3 ${
                      step.status === 'COMPLETED'
                        ? 'bg-emerald-950/30 border-emerald-800/60'
                        : step.status === 'REJECTED'
                        ? 'bg-rose-950/20 border-rose-800/40 opacity-60'
                        : 'bg-slate-950 border-slate-800'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="text-[10px] font-mono font-bold text-indigo-400 bg-slate-900 px-2 py-0.5 rounded">
                          Step {step.step_index}
                        </span>
                        <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded uppercase ${
                          step.risk_level === 'HIGH'
                            ? 'bg-rose-950 text-rose-400'
                            : step.risk_level === 'MEDIUM'
                            ? 'bg-amber-950 text-amber-400'
                            : 'bg-emerald-950 text-emerald-400'
                        }`}>
                          {step.risk_level} RISK
                        </span>
                      </div>

                      <span className={`text-[9px] font-mono font-bold uppercase ${
                        step.status === 'COMPLETED' ? 'text-emerald-400' : 'text-amber-400'
                      }`}>
                        {step.status}
                      </span>
                    </div>

                    <div>
                      <h4 className="font-bold text-xs text-white">{step.description}</h4>
                      <p className="text-[11px] text-slate-400 mt-0.5">Reason: {step.reason}</p>
                      <p className="text-[10px] font-mono text-slate-500 mt-0.5">Source: {step.source_citation}</p>
                    </div>

                    {step.status === 'AWAITING_APPROVAL' && (
                      <div className="flex space-x-3 pt-2 border-t border-slate-800/80">
                        <button
                          type="button"
                          onClick={() => handleApprove(currentPlan.plan_id, step.action_id)}
                          className="px-4 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-md transition-all flex items-center space-x-1"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Approve Action</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => handleReject(currentPlan.plan_id, step.action_id)}
                          className="px-4 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-rose-400 font-bold text-xs shadow-md transition-all flex items-center space-x-1"
                        >
                          <XCircle className="w-3.5 h-3.5" />
                          <span>Reject</span>
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>

        {/* Right Col: Pending Approvals Queue & Execution Log */}
        <div className="space-y-4">
          
          {/* Pending Queue */}
          <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-3xl shadow-xl space-y-3 backdrop-blur-md">
            <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
              <ShieldAlert className="w-4 h-4 text-amber-400" />
              <h4 className="text-xs font-bold text-white">Pending Approval Queue ({pendingApprovals.length})</h4>
            </div>

            {pendingApprovals.length === 0 ? (
              <p className="text-[11px] text-slate-500 text-center py-4">No pending actions awaiting approval.</p>
            ) : (
              <div className="space-y-2">
                {pendingApprovals.map((item, idx) => (
                  <div key={idx} className="p-2.5 bg-slate-950 border border-slate-800 rounded-xl space-y-1 text-xs">
                    <span className="text-[8px] font-mono font-bold text-amber-400 uppercase">{item.step.risk_level} RISK</span>
                    <h5 className="font-bold text-slate-200 text-[11px]">{item.step.description}</h5>
                    <div className="flex space-x-2 pt-1">
                      <button
                        type="button"
                        onClick={() => handleApprove(item.plan_id, item.step.action_id)}
                        className="text-[9px] font-bold text-emerald-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800"
                      >
                        Approve
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Execution Audit Log */}
          <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-3xl shadow-xl space-y-3 backdrop-blur-md">
            <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
              <Activity className="w-4 h-4 text-emerald-400" />
              <h4 className="text-xs font-bold text-white">Action Execution Log ({actionLogs.length})</h4>
            </div>

            <div className="space-y-2 max-h-60 overflow-y-auto font-mono text-[10px]">
              {actionLogs.map((log, idx) => (
                <div key={idx} className="p-2 bg-slate-950 border border-slate-800 rounded-xl flex items-center justify-between">
                  <div>
                    <span className="text-emerald-400 font-bold block">{log.tool_name}</span>
                    <span className="text-slate-500">Exec: {log.executor}</span>
                  </div>
                  <span className="text-slate-400">{log.status}</span>
                </div>
              ))}
            </div>
          </div>

        </div>

      </div>

    </div>
  );
};
