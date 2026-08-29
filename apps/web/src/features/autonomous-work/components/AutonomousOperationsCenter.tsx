import React, { useState, useEffect } from 'react';
import {
  parseIntentAndCreatePlan, executeDryRun, manageApprovalRequest, executePlanStep,
  emergencyStopAutonomy, fetchExecutionJournal, PlanResponse, DryRunResponse, ExecutionJournalResponse
} from '../autonomous-work-api';
import {
  Play, ShieldAlert, CheckCircle2, XCircle, AlertOctagon, Layers, ArrowRight, Activity, Terminal, Shield, Zap, FileText
} from 'lucide-react';

interface AutonomousOperationsCenterProps {
  initialProjectId?: string;
  token?: string;
}

export const AutonomousOperationsCenter: React.FC<AutonomousOperationsCenterProps> = ({
  initialProjectId,
  token
}) => {
  const [activeTab, setActiveTab] = useState<'APPROVAL_CENTER' | 'PLAN_GENERATOR' | 'EXECUTION_JOURNAL' | 'TOOL_REGISTRY'>('APPROVAL_CENTER');
  const [journal, setJournal] = useState<ExecutionJournalResponse | null>(null);
  const [currentPlan, setCurrentPlan] = useState<PlanResponse | null>(null);
  const [dryRunRes, setDryRunRes] = useState<DryRunResponse | null>(null);
  
  const [promptInput, setPromptInput] = useState<string>('Prepare the release checklist and verify OAuth token dependencies');
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const journalRes = await fetchExecutionJournal(token);
      setJournal(journalRes);
    } catch (err) {
      console.error('Failed to load autonomous operations center:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [token]);

  const handleGeneratePlan = async () => {
    setIsLoading(true);
    try {
      const res = await parseIntentAndCreatePlan(promptInput, initialProjectId, token);
      setCurrentPlan(res);
      if (res.status === 'REJECTED_PROMPT_INJECTION_DETECTED') {
        setActionMessage(`SECURITY ALERT: ${res.message}`);
      } else {
        setActionMessage(`Structured Plan Created: Goal '${res.goal}' (Level ${res.autonomy_level} Autonomy)`);
      }
    } catch (err) {
      console.error('Failed to generate plan:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunDryRun = async () => {
    if (!currentPlan) return;
    try {
      const res = await executeDryRun(currentPlan.plan_id, token);
      setDryRunRes(res);
      setActionMessage(`Dry-Run Executed: ${res.predicted_side_effects}`);
    } catch (err) {
      console.error('Dry run failed:', err);
    }
  };

  const handleApproval = async (action: 'APPROVE' | 'REJECT') => {
    if (!currentPlan) return;
    try {
      const res = await manageApprovalRequest(currentPlan.plan_id, action, token);
      setActionMessage(`Plan '${currentPlan.plan_id}' ${action}D successfully.`);
      loadData();
    } catch (err) {
      console.error('Approval failed:', err);
    }
  };

  const handleEmergencyStop = async () => {
    try {
      const res = await emergencyStopAutonomy('GLOBAL', token);
      setActionMessage(`EMERGENCY KILL SWITCH ACTIVATED: ${res.message}`);
    } catch (err) {
      console.error('Emergency stop failed:', err);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6 text-slate-100 font-sans select-none">
      
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-rose-950/80 to-slate-900 border border-rose-800/60 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-rose-400 px-2.5 py-0.5 bg-rose-950 rounded border border-rose-800/60">
                AUTONOMOUS KNOWLEDGE OPERATIONS & WORK EXECUTION
              </span>
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center space-x-1">
                <Shield className="w-3 h-3" />
                <span>Level 3 Approval Gate Enforced</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <Play className="w-7 h-7 text-rose-400" />
              <span>Autonomous Operations Center</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Intent parsing, dry-run simulation, approval gates, postcondition verification, and emergency kill switch.
            </p>
          </div>

          {/* Emergency Kill Switch Button */}
          <button
            type="button"
            onClick={handleEmergencyStop}
            className="px-4 py-2 bg-red-600 hover:bg-red-500 rounded-2xl font-mono text-xs font-bold text-white shadow-lg flex items-center space-x-2 flex-shrink-0"
          >
            <AlertOctagon className="w-4 h-4" />
            <span>GLOBAL EMERGENCY STOP</span>
          </button>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center space-x-2 bg-slate-950 p-1.5 rounded-2xl border border-slate-800 w-fit">
          <button
            type="button"
            onClick={() => setActiveTab('APPROVAL_CENTER')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
              activeTab === 'APPROVAL_CENTER' ? 'bg-rose-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Approval Center
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('PLAN_GENERATOR')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
              activeTab === 'PLAN_GENERATOR' ? 'bg-rose-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Plan & Dry-Run
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('EXECUTION_JOURNAL')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
              activeTab === 'EXECUTION_JOURNAL' ? 'bg-rose-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Execution Journal
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('TOOL_REGISTRY')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
              activeTab === 'TOOL_REGISTRY' ? 'bg-rose-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Tool Registry
          </button>
        </div>
      </div>

      {actionMessage && (
        <div className="p-3 bg-rose-950/80 border border-rose-800/60 rounded-2xl text-xs text-rose-200 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <ShieldAlert className="w-4 h-4 text-rose-400" />
            <span>{actionMessage}</span>
          </div>
          <button type="button" onClick={() => setActionMessage(null)} className="text-[10px] text-slate-400 hover:text-white font-mono">Dismiss</button>
        </div>
      )}

      {/* Tab Views */}
      {activeTab === 'PLAN_GENERATOR' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Structured Intent & Plan Generator</h3>
            <p className="text-xs text-slate-400 mt-1">Converts natural language into structured, inspectable plans with risk assessments.</p>
          </div>

          <div className="space-y-3">
            <textarea
              rows={2}
              value={promptInput}
              onChange={(e) => setPromptInput(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-2xl p-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-rose-500"
              placeholder="Enter intent..."
            />
            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={handleGeneratePlan}
                disabled={isLoading}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-500 rounded-xl text-white font-bold text-xs"
              >
                Generate Plan
              </button>
              {currentPlan && (
                <button
                  type="button"
                  onClick={handleRunDryRun}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl font-bold text-xs"
                >
                  Run Dry-Run Simulation
                </button>
              )}
            </div>
          </div>

          {currentPlan && (
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-bold text-white text-sm">Goal: {currentPlan.goal}</span>
                <span className="text-[9px] font-mono font-bold bg-amber-950 text-amber-400 px-2 py-0.5 rounded border border-amber-800/60 uppercase">Risk: {currentPlan.overall_risk}</span>
              </div>

              <div className="space-y-2">
                <span className="text-[10px] font-mono text-slate-400 uppercase font-bold">Planned Steps</span>
                {currentPlan.steps.map(step => (
                  <div key={step.step_number} className="p-3 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-between">
                    <span className="text-slate-300">{step.step_number}. {step.description}</span>
                    <span className="text-[9px] font-mono text-rose-400 uppercase font-bold">{step.risk} RISK</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {dryRunRes && (
            <div className="p-4 bg-slate-950 border border-emerald-800/60 rounded-2xl space-y-2 text-xs">
              <span className="font-bold text-emerald-400 block font-mono">Dry-Run Simulation Output</span>
              <p className="text-slate-300">• Mode: {dryRunRes.mode}</p>
              <p className="text-slate-300">• Predicted Side Effects: {dryRunRes.predicted_side_effects}</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'APPROVAL_CENTER' && currentPlan && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-white uppercase font-mono">MindMesh Approval Center</h3>
              <p className="text-xs text-slate-400 mt-1">Review plan, impact, evidence, and risk before approving execution.</p>
            </div>
            <span className="text-[9px] font-mono text-rose-400 bg-rose-950 px-2 py-0.5 rounded border border-rose-800/60 font-bold">LEVEL 3 APPROVAL GATE</span>
          </div>

          <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-3 text-xs">
            <span className="font-bold text-white text-sm">Plan ID: {currentPlan.plan_id}</span>
            <p className="text-slate-300">• <strong className="text-white">Goal:</strong> {currentPlan.goal}</p>
            <p className="text-slate-300">• <strong className="text-white">Autonomy Level:</strong> Level {currentPlan.autonomy_level} (Approval Required)</p>

            <div className="flex items-center space-x-3 pt-2">
              <button
                type="button"
                onClick={() => handleApproval('APPROVE')}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-xl text-white font-bold text-xs flex items-center space-x-1"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Approve Plan Execution</span>
              </button>
              <button
                type="button"
                onClick={() => handleApproval('REJECT')}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl font-bold text-xs flex items-center space-x-1"
              >
                <XCircle className="w-3.5 h-3.5" />
                <span>Reject Plan</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'EXECUTION_JOURNAL' && journal && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Autonomous Execution Journal & Audit Trace</h3>
            <p className="text-xs text-slate-400 mt-1">Traceable execution log mapping Intent → Plan → Evidence → Tool → Action → Outcome.</p>
          </div>

          <div className="space-y-3">
            {journal.entries.map(entry => (
              <div key={entry.execution_id} className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white">{entry.intent}</span>
                  <span className="text-[9px] font-mono text-emerald-400 uppercase font-bold">{entry.status}</span>
                </div>
                <p className="text-slate-300">• Action: <strong>{entry.action}</strong> via Tool: <strong className="text-indigo-400">{entry.tool}</strong></p>
                <p className="text-slate-400 text-[10px]">• Actor: {entry.actor} | Approved By: {entry.approved_by}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'TOOL_REGISTRY' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Tool Registry & Risk Inspector</h3>
            <p className="text-xs text-slate-400 mt-1">Validated executable tools with schema validation, timeouts, and rate limits.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2">
              <span className="font-bold text-indigo-400 block font-mono uppercase">TaskCreateTool</span>
              <p className="text-slate-300">• Risk Level: <strong className="text-amber-400">MEDIUM</strong></p>
              <p className="text-slate-300">• Permissions: <strong className="text-white">task:create</strong></p>
              <p className="text-slate-300">• Timeout: 5000 ms | Retry: Safe Transient Only</p>
            </div>

            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2">
              <span className="font-bold text-rose-400 block font-mono uppercase">DocumentDeleteTool</span>
              <p className="text-slate-300">• Risk Level: <strong className="text-red-400">CRITICAL</strong></p>
              <p className="text-slate-300">• Permissions: <strong className="text-white">document:delete</strong></p>
              <p className="text-slate-300">• Approval: Always Required (Level 3 Gate)</p>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
