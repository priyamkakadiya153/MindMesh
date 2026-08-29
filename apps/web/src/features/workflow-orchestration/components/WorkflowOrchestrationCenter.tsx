import React, { useState, useEffect } from 'react';
import {
  fetchWorkflowCenter, createWorkflowPlan, approveWorkflow, executeWorkflowStep, retryWorkflowStep, generateWorkflowPostmortem, fetchWorkflowDigest,
  WorkflowItem, StepExecutionResponse, RetryResponse, PostmortemResponse, WorkflowDigestResponse
} from '../workflow-orchestration-api';
import {
  Workflow, ShieldCheck, CheckCircle2, AlertTriangle, Layers, Play, Check, RotateCcw, FileText, Activity, AlertOctagon, Sparkles
} from 'lucide-react';

interface WorkflowOrchestrationCenterProps {
  initialProjectId?: string;
  token?: string;
}

export const WorkflowOrchestrationCenter: React.FC<WorkflowOrchestrationCenterProps> = ({
  initialProjectId = 'bfb4530e-bc5d-4c1f-aaf3-217a55bcaba4',
  token
}) => {
  const [activeTab, setActiveTab] = useState<'QUEUE' | 'DAG' | 'APPROVAL' | 'POSTMORTEM'>('QUEUE');
  const [workflows, setWorkflows] = useState<WorkflowItem[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState<WorkflowItem | null>(null);
  const [digest, setDigest] = useState<WorkflowDigestResponse | null>(null);

  const [executionResult, setExecutionResult] = useState<StepExecutionResponse | null>(null);
  const [retryResult, setRetryResult] = useState<RetryResponse | null>(null);
  const [postmortem, setPostmortem] = useState<PostmortemResponse | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [centerRes, dig] = await Promise.all([
        fetchWorkflowCenter(token),
        fetchWorkflowDigest(token)
      ]);
      setWorkflows(centerRes.workflows);
      if (centerRes.workflows.length > 0) {
        setSelectedWorkflow(centerRes.workflows[0]);
      }
      setDigest(dig);
    } catch (err) {
      console.error('Failed to load workflow orchestration center:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [initialProjectId, token]);

  const handleCreatePlan = async () => {
    try {
      const res = await createWorkflowPlan(initialProjectId, 'Safely migrate authentication from JWT to OAuth', token);
      setSelectedWorkflow(res);
      setActionMessage(`Constructed 10-step executable Workflow Plan '${res.workflow_id}'.`);
      loadData();
    } catch (err) {
      console.error('Failed plan creation:', err);
    }
  };

  const handleApprove = async (wfId: string) => {
    try {
      const res = await approveWorkflow(wfId, token);
      setActionMessage(res.message);
      loadData();
    } catch (err) {
      console.error('Failed workflow approval:', err);
    }
  };

  const handleExecuteStep = async (wfId: string, stepId: string) => {
    try {
      const res = await executeWorkflowStep(wfId, stepId, token);
      setExecutionResult(res);
      setActionMessage(`Step '${stepId}' executed and verified! Idempotency Key: ${res.idempotency_key}`);
    } catch (err) {
      console.error('Failed step execution:', err);
    }
  };

  const handleRetry = async (wfId: string, stepId: string) => {
    try {
      const res = await retryWorkflowStep(wfId, stepId, token);
      setRetryResult(res);
      setActionMessage(res.message);
    } catch (err) {
      console.error('Failed step retry:', err);
    }
  };

  const handlePostmortem = async (wfId: string) => {
    try {
      const res = await generateWorkflowPostmortem(wfId, token);
      setPostmortem(res);
      setActionMessage(`Generated evidence-grounded postmortem for '${wfId}'.`);
    } catch (err) {
      console.error('Failed postmortem generation:', err);
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
                INTELLIGENT WORKFLOW ORCHESTRATION & CONTROLLED AUTONOMY
              </span>
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center space-x-1">
                <ShieldCheck className="w-3 h-3" />
                <span>Human Approval Gated</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <Workflow className="w-7 h-7 text-indigo-400" />
              <span>Workflow Orchestration Center</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Constructs executable multi-step DAG plans, verifies idempotency, manages human approval gates, and handles failure recovery.
            </p>
          </div>

          {/* Navigation Mode Tabs */}
          <div className="flex items-center space-x-2 bg-slate-950 p-1.5 rounded-2xl border border-slate-800 flex-shrink-0">
            <button
              type="button"
              onClick={() => setActiveTab('QUEUE')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'QUEUE' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Workflow Queue
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('DAG')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'DAG' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              DAG Visualizer
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('APPROVAL')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'APPROVAL' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Approval Gate
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('POSTMORTEM')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'POSTMORTEM' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Postmortem Summary
            </button>
          </div>
        </div>

        {/* Digest Counters Bar */}
        {digest && (
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-2 border-t border-slate-800/60">
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Workflows Executed</span>
              <span className="text-lg font-black text-indigo-400">{digest.total_workflows_executed}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Idempotent Actions</span>
              <span className="text-lg font-black text-emerald-400">{digest.idempotent_actions_verified}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Approvals Passed</span>
              <span className="text-lg font-black text-purple-400">{digest.human_approval_gates_passed}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Circuit Breakers</span>
              <span className="text-lg font-black text-amber-400">{digest.circuit_breakers_tripped}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Improvements</span>
              <span className="text-lg font-black text-cyan-400">{digest.process_improvements_suggested}</span>
            </div>
          </div>
        )}
      </div>

      {/* Action Toast */}
      {actionMessage && (
        <div className="p-3 bg-indigo-950/80 border border-indigo-800/60 rounded-2xl text-xs text-indigo-200 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Check className="w-4 h-4 text-emerald-400" />
            <span>{actionMessage}</span>
          </div>
          <button type="button" onClick={() => setActionMessage(null)} className="text-[10px] text-slate-400 hover:text-white font-mono">Dismiss</button>
        </div>
      )}

      {/* Tab Views */}
      {activeTab === 'QUEUE' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono flex items-center space-x-2">
              <Layers className="w-4 h-4 text-indigo-400" />
              <span>Active Workflow Queue</span>
            </h3>

            <button
              type="button"
              onClick={() => handleCreatePlan()}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-2xl text-white font-bold text-xs shadow-lg flex items-center space-x-1.5"
            >
              <Sparkles className="w-4 h-4" />
              <span>Construct 10-Step Workflow Plan</span>
            </button>
          </div>

          <div className="space-y-3">
            {workflows.map((wf) => (
              <div key={wf.workflow_id} className="p-4 bg-slate-950 border border-slate-800 rounded-2xl flex items-center justify-between text-xs">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className={`text-[8px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${
                      wf.status === 'RUNNING' ? 'bg-emerald-950 text-emerald-400 border-emerald-800/60' : 'bg-amber-950 text-amber-400 border-amber-800/60'
                    }`}>{wf.status}</span>
                    <span className="text-[9px] font-mono text-indigo-400 bg-slate-900 px-2 py-0.5 rounded">{wf.workflow_id}</span>
                  </div>
                  <h4 className="font-bold text-white mt-1">{wf.goal}</h4>
                </div>

                {wf.status === 'AWAITING_APPROVAL' && (
                  <button
                    type="button"
                    onClick={() => handleApprove(wf.workflow_id)}
                    className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 rounded-xl text-white font-bold text-xs flex items-center space-x-1"
                  >
                    <Check className="w-3.5 h-3.5" />
                    <span>Authorize Execution</span>
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'DAG' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Workflow DAG Step Visualizer</h3>
            <p className="text-xs text-slate-400 mt-1">Multi-step executable DAG plan with serial/parallel dependencies.</p>
          </div>

          {selectedWorkflow && selectedWorkflow.steps && (
            <div className="space-y-3">
              {selectedWorkflow.steps.map((s, idx) => (
                <div key={s.step_id} className="p-3 bg-slate-950 border border-slate-800 rounded-2xl flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-3">
                    <span className="w-6 h-6 rounded-full bg-slate-900 text-indigo-400 border border-indigo-800 text-[10px] font-mono font-bold flex items-center justify-center">{idx + 1}</span>
                    <div>
                      <h5 className="font-bold text-white">{s.name}</h5>
                      {s.depends_on.length > 0 && (
                        <span className="text-[9px] font-mono text-slate-500">Depends on: {s.depends_on.join(', ')}</span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <span className={`text-[8px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${
                      s.status === 'COMPLETED' ? 'bg-emerald-950 text-emerald-400 border-emerald-800/60' : 'bg-slate-900 text-slate-400 border-slate-800'
                    }`}>{s.status}</span>
                    <button
                      type="button"
                      onClick={() => handleExecuteStep(selectedWorkflow.workflow_id, s.step_id)}
                      className="px-2.5 py-1 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-white font-bold text-[10px] flex items-center space-x-1"
                    >
                      <Play className="w-3 h-3" />
                      <span>Execute</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => handleRetry(selectedWorkflow.workflow_id, s.step_id)}
                      className="px-2 py-1 bg-slate-800 hover:bg-slate-700 rounded-lg text-slate-300 font-bold text-[10px] flex items-center space-x-1"
                    >
                      <RotateCcw className="w-3 h-3" />
                      <span>Retry</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {executionResult && (
            <div className="p-4 bg-slate-950 border border-emerald-800/60 rounded-2xl text-xs space-y-1">
              <span className="text-[9px] font-mono text-emerald-400 uppercase font-bold">Action Verification Result</span>
              <p className="text-white font-bold">Idempotency Key: {executionResult.idempotency_key}</p>
              <p className="text-slate-300">Expected: {executionResult.observed_vs_expected.expected_state}</p>
              <p className="text-slate-300">Observed: {executionResult.observed_vs_expected.observed_state}</p>
            </div>
          )}

          {retryResult && (
            <div className="p-4 bg-slate-950 border border-amber-800/60 rounded-2xl text-xs space-y-1">
              <span className="text-[9px] font-mono text-amber-400 uppercase font-bold">Circuit Breaker & Retry State</span>
              <p className="text-white font-bold">Attempt #{retryResult.retry_count} | Tripped: {String(retryResult.circuit_breaker_tripped)}</p>
              <p className="text-slate-300">{retryResult.message}</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'APPROVAL' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Human Approval Gate Authorization</h3>
            <p className="text-xs text-slate-400 mt-1">Full context preview before executing consequential actions (No blind approvals).</p>
          </div>

          <div className="p-5 bg-slate-950 border border-indigo-800/60 rounded-3xl space-y-4 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-[9px] font-mono text-amber-400 bg-amber-950 px-2 py-0.5 rounded border border-amber-800/60 font-bold uppercase">HUMAN APPROVAL REQUIRED</span>
              <span className="text-[9px] font-mono text-slate-400">Step #6: Production Migration</span>
            </div>

            <div className="space-y-2">
              <span className="text-[9px] font-mono text-slate-500 uppercase font-bold block">Action Details</span>
              <p className="text-white font-bold">Goal: "Safely migrate authentication from JWT to OAuth 2.0 Provider"</p>
              <p className="text-slate-300">• Affected Resources: PostgreSQL Session Storage, Auth API Router</p>
              <p className="text-slate-300">• Potential Risk: Database session pool max connection limit spike</p>
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="button"
                onClick={() => selectedWorkflow && handleApprove(selectedWorkflow.workflow_id)}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-2xl text-white font-bold text-xs shadow-lg flex items-center space-x-1.5"
              >
                <Check className="w-4 h-4" />
                <span>Confirm & Authorize Execution</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'POSTMORTEM' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-white uppercase font-mono">Evidence-Grounded Postmortem & Process Improvement</h3>
              <p className="text-xs text-slate-400 mt-1">Analyzes workflow execution outcomes to surface process improvement candidates.</p>
            </div>
            
            <button
              type="button"
              onClick={() => selectedWorkflow && handlePostmortem(selectedWorkflow.workflow_id)}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-2xl text-white font-bold text-xs shadow-lg flex items-center space-x-1.5"
            >
              <FileText className="w-4 h-4" />
              <span>Generate Postmortem</span>
            </button>
          </div>

          {postmortem && (
            <div className="p-5 bg-slate-950 border border-indigo-800/60 rounded-3xl space-y-4 text-xs">
              <h4 className="font-bold text-white text-sm">{postmortem.postmortem_title}</h4>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-3 bg-slate-900 rounded-2xl space-y-1">
                  <span className="text-[9px] font-mono text-emerald-400 uppercase font-bold block">What Worked</span>
                  {postmortem.what_worked.map((ww, i) => (
                    <p key={i} className="text-slate-300">• {ww}</p>
                  ))}
                </div>

                <div className="p-3 bg-slate-900 rounded-2xl space-y-1">
                  <span className="text-[9px] font-mono text-amber-400 uppercase font-bold block">What Failed</span>
                  {postmortem.what_failed.map((wf, i) => (
                    <p key={i} className="text-slate-300">• {wf}</p>
                  ))}
                </div>
              </div>

              <div className="p-4 bg-indigo-950/80 border border-indigo-800/60 rounded-2xl space-y-1">
                <span className="text-[9px] font-mono text-indigo-400 uppercase font-bold block">Process Improvement Candidate</span>
                <p className="text-white font-bold">{postmortem.process_improvement_candidate.title}</p>
                <p className="text-[10px] text-indigo-300 mt-1">{postmortem.process_improvement_candidate.recommendation}</p>
              </div>
            </div>
          )}
        </div>
      )}

    </div>
  );
};
