import React, { useState, useEffect } from 'react';
import {
  createWorkObjective, generateWorkPlan, previewPlan, executeWorkflowStep, handleWorkflowException, dryRunWorkflow, evaluatePlanVsActual,
  WorkObjectiveResponse, WorkPlanResponse, PlanPreviewResponse, StepExecutionResponse, ExceptionResponse, DryRunResponse, PlanEvaluationResponse
} from '../adaptive-workflows-api';
import {
  GitBranch, Play, Pause, CheckCircle2, AlertTriangle, ShieldCheck, Zap, Layers, RefreshCw, FileText, ArrowRight, Activity, Cpu, Eye
} from 'lucide-react';

interface WorkOrchestrationCenterProps {
  initialProjectId?: string;
  token?: string;
}

export const WorkOrchestrationCenter: React.FC<WorkOrchestrationCenterProps> = ({
  initialProjectId,
  token
}) => {
  const [activeSection, setActiveSection] = useState<'MY_WORK' | 'RUNNING' | 'WAITING' | 'BLOCKED' | 'APPROVAL' | 'COMPLETED'>('MY_WORK');
  const [intentInput, setIntentInput] = useState<string>('Prepare Project Alpha for release.');
  const [goalInput, setGoalInput] = useState<string>('Release Project Alpha v2.0 with SOC2 Compliance');

  const [objectiveRes, setObjectiveRes] = useState<WorkObjectiveResponse | null>(null);
  const [planRes, setPlanRes] = useState<WorkPlanResponse | null>(null);
  const [previewRes, setPreviewRes] = useState<PlanPreviewResponse | null>(null);
  const [execRes, setExecRes] = useState<StepExecutionResponse | null>(null);
  const [exceptionRes, setExceptionRes] = useState<ExceptionResponse | null>(null);
  const [dryRunRes, setDryRunRes] = useState<DryRunResponse | null>(null);
  const [evalRes, setEvalRes] = useState<PlanEvaluationResponse | null>(null);

  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const handleGenerateWorkflow = async () => {
    setIsLoading(true);
    try {
      const obj = await createWorkObjective(goalInput, 'Full Project Alpha codebase & microservices', 'HIGH', undefined, initialProjectId, token);
      setObjectiveRes(obj);

      const plan = await generateWorkPlan(obj.objective_id, intentInput, initialProjectId, token);
      setPlanRes(plan);

      const prev = await previewPlan(plan.plan_id, token);
      setPreviewRes(prev);

      setActionMessage(`Workflow Plan '${plan.plan_id}' generated successfully (Confidence: ${(plan.confidence_score * 100).toFixed(0)}%).`);
    } catch (err) {
      console.error('Failed to generate workflow:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExecuteStep = async (stepId: string, action: string) => {
    if (!planRes) return;
    setIsLoading(true);
    try {
      const res = await executeWorkflowStep(planRes.plan_id, stepId, action, token);
      setExecRes(res);
      setActionMessage(`Step '${stepId}' transition: ${action} -> State: ${res.step_state} (Plan Status: ${res.plan_status}).`);
      
      // Update local state preview
      setPlanRes(prev => {
        if (!prev) return null;
        return {
          ...prev,
          status: res.plan_status,
          steps: prev.steps.map(s => s.step_id === stepId ? { ...s, state: res.step_state } : s)
        };
      });
    } catch (err) {
      console.error('Step execution failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTriggerException = async () => {
    if (!planRes) return;
    setIsLoading(true);
    try {
      const exc = await handleWorkflowException(planRes.plan_id, 'step-2', 'HTTP 503 Auth0 sandbox timeout', token);
      setExceptionRes(exc);
      setActionMessage(`Exception logged for step-2 (${exc.severity}): ${exc.suggested_recovery}`);
    } catch (err) {
      console.error('Exception handling failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDryRun = async () => {
    if (!planRes) return;
    setIsLoading(true);
    try {
      const dr = await dryRunWorkflow(planRes.plan_id, token);
      setDryRunRes(dr);
      setActionMessage(`Dry-Run simulation completed. Production mutation: ${dr.production_mutation_occurred ? 'YES' : 'NO'}`);
    } catch (err) {
      console.error('Dry-Run simulation failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEvaluate = async () => {
    if (!planRes) return;
    setIsLoading(true);
    try {
      const ev = await evaluatePlanVsActual(planRes.plan_id, token);
      setEvalRes(ev);
      setActionMessage(`Plan vs Actual evaluated: ${ev.objective_achieved} (Lesson: ${ev.candidate_lesson})`);
    } catch (err) {
      console.error('Plan evaluation failed:', err);
    } finally {
      setIsLoading(false);
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
                ADAPTIVE WORK ORCHESTRATION
              </span>
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center space-x-1">
                <ShieldCheck className="w-3 h-3" />
                <span>Controlled Safe Autonomous Execution</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <GitBranch className="w-7 h-7 text-indigo-400" />
              <span>MindMesh Work Orchestration Center</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Coordinates complex objectives into dependency-aware, explainable workflows with human approval gates and exception safety.
            </p>
          </div>

          <div className="flex items-center space-x-2 bg-slate-950 p-2.5 rounded-2xl border border-slate-800">
            <span className="text-[10px] font-mono text-slate-400 uppercase font-bold">Autonomy Policy:</span>
            <span className="text-xs font-mono font-bold text-indigo-400 bg-indigo-950 px-2 py-1 rounded border border-indigo-800/60">APPROVE_GATED</span>
          </div>
        </div>

        {/* Dashboard Section Filter */}
        <div className="flex flex-wrap items-center gap-2 bg-slate-950 p-1.5 rounded-2xl border border-slate-800 w-fit">
          {(['MY_WORK', 'RUNNING', 'WAITING', 'BLOCKED', 'APPROVAL', 'COMPLETED'] as const).map(sec => (
            <button
              key={sec}
              type="button"
              onClick={() => setActiveSection(sec)}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeSection === sec ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              {sec.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {actionMessage && (
        <div className="p-3 bg-indigo-950/80 border border-indigo-800/60 rounded-2xl text-xs text-indigo-200 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Activity className="w-4 h-4 text-indigo-400" />
            <span>{actionMessage}</span>
          </div>
          <button type="button" onClick={() => setActionMessage(null)} className="text-[10px] text-slate-400 hover:text-white font-mono">Dismiss</button>
        </div>
      )}

      {/* Goal & Intent Generator */}
      <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
        <h3 className="text-xs font-bold text-white uppercase font-mono border-b border-slate-800 pb-2">Natural Language Objective & Plan Generator</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          <div>
            <label className="text-slate-400 font-bold block mb-1">User Intent:</label>
            <input
              type="text"
              value={intentInput}
              onChange={(e) => setIntentInput(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white focus:outline-none"
            />
          </div>
          <div>
            <label className="text-slate-400 font-bold block mb-1">Objective Goal:</label>
            <input
              type="text"
              value={goalInput}
              onChange={(e) => setGoalInput(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white focus:outline-none"
            />
          </div>
        </div>
        <button
          type="button"
          onClick={handleGenerateWorkflow}
          disabled={isLoading}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-white font-bold text-xs flex items-center space-x-2"
        >
          <Zap className="w-4 h-4" />
          <span>Generate Adaptive Work Plan</span>
        </button>
      </div>

      {/* Generated Plan & Step Execution */}
      {planRes && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-slate-800 pb-3 gap-2">
            <div>
              <span className="text-[10px] font-mono text-indigo-400 uppercase font-bold">Plan ID: {planRes.plan_id} (v{planRes.version})</span>
              <h3 className="text-base font-bold text-white mt-0.5">{planRes.user_intent}</h3>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-950 px-2.5 py-1 rounded-xl border border-emerald-800/60 uppercase">
                Status: {planRes.status}
              </span>
              <button
                type="button"
                onClick={handleDryRun}
                disabled={isLoading}
                className="px-3 py-1.5 bg-slate-950 hover:bg-slate-800 border border-slate-700 text-xs font-bold text-slate-200 rounded-xl flex items-center space-x-1"
              >
                <Eye className="w-3.5 h-3.5" />
                <span>Dry Run</span>
              </button>
              <button
                type="button"
                onClick={handleEvaluate}
                disabled={isLoading}
                className="px-3 py-1.5 bg-slate-950 hover:bg-slate-800 border border-slate-700 text-xs font-bold text-slate-200 rounded-xl"
              >
                Evaluate Plan vs Actual
              </button>
            </div>
          </div>

          {/* Workflow Steps */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-white uppercase font-mono">Dependency-Aware Workflow Steps</h4>
            {planRes.steps.map(step => (
              <div key={step.step_id} className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2 text-xs">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-[9px] font-mono text-indigo-400 bg-indigo-950 px-2 py-0.5 rounded border border-indigo-800/60 font-bold uppercase">{step.step_type}</span>
                    <span className="text-white font-bold">{step.name}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${
                      step.side_effect === 'IRREVERSIBLE' ? 'bg-red-950 text-red-400 border-red-800/60' : 'bg-slate-900 text-slate-400 border-slate-800'
                    }`}>
                      {step.side_effect}
                    </span>
                    <span className="text-[10px] font-mono text-emerald-400 font-bold uppercase">{step.state}</span>
                  </div>
                </div>

                <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
                  <span>• Owner: {step.owner} | Dependencies: {step.dependencies.length > 0 ? step.dependencies.join(', ') : 'None'}</span>
                  <div className="flex items-center space-x-2">
                    {step.state === 'READY' && (
                      <button
                        type="button"
                        onClick={() => handleExecuteStep(step.step_id, 'START')}
                        className="px-2.5 py-1 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-bold text-[10px]"
                      >
                        Start Step
                      </button>
                    )}
                    {step.state === 'RUNNING' && (
                      <button
                        type="button"
                        onClick={() => handleExecuteStep(step.step_id, 'COMPLETE')}
                        className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-bold text-[10px]"
                      >
                        Complete Step
                      </button>
                    )}
                    {step.requires_approval && step.state === 'PENDING' && (
                      <button
                        type="button"
                        onClick={() => handleExecuteStep(step.step_id, 'APPROVE')}
                        className="px-2.5 py-1 bg-amber-600 hover:bg-amber-500 text-white rounded-lg font-bold text-[10px]"
                      >
                        Approve & Deploy
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Exception Test Button */}
          <div className="pt-2">
            <button
              type="button"
              onClick={handleTriggerException}
              disabled={isLoading}
              className="px-3 py-1.5 bg-red-950/80 hover:bg-red-900/80 border border-red-800/60 text-red-200 text-xs font-bold rounded-xl"
            >
              Simulate Dependency Exception
            </button>
          </div>

          {/* Exception Details Card */}
          {exceptionRes && (
            <div className="p-4 bg-red-950/30 border border-red-800/60 rounded-2xl space-y-2 text-xs">
              <span className="font-bold text-red-400 font-mono block uppercase">Workflow Exception ({exceptionRes.severity})</span>
              <p className="text-slate-300">• Error: {exceptionRes.error_message}</p>
              <p className="text-slate-300">• Suggested Recovery: {exceptionRes.suggested_recovery}</p>
            </div>
          )}

          {/* Dry Run Card */}
          {dryRunRes && (
            <div className="p-4 bg-indigo-950/30 border border-indigo-800/60 rounded-2xl space-y-2 text-xs">
              <span className="font-bold text-indigo-400 font-mono block uppercase">Dry-Run Simulation Output</span>
              <p className="text-slate-300">• Affected Resources: {dryRunRes.resources_affected.join(', ')}</p>
              <p className="text-slate-300">• Potential Errors: {dryRunRes.potential_errors.join(', ')}</p>
            </div>
          )}

          {/* Evaluation Card */}
          {evalRes && (
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2 text-xs">
              <span className="font-bold text-teal-400 font-mono block uppercase">Plan vs Actual Evaluation</span>
              <p className="text-slate-300">• Planned: {evalRes.planned_duration_minutes}m | Actual: {evalRes.actual_duration_minutes}m</p>
              <p className="text-emerald-400 font-bold">• Candidate Lesson: {evalRes.candidate_lesson}</p>
            </div>
          )}
        </div>
      )}

    </div>
  );
};
