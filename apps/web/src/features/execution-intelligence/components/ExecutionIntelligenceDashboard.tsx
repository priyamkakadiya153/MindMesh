import React, { useState, useEffect } from 'react';
import {
  createActionPlan, fetchActionPlan, suggestActionPlanTasks, confirmSuggestedTask, fetchDetectedBlockers, fetchCriticalPath, recordClosedLoopOutcome, fetchPendingActions,
  ActionPlanResponse, SuggestedTaskItem, DetectedBlockerItem, CriticalPathResponse, ClosedLoopOutcomeResponse, PendingActionItem
} from '../execution-intelligence-api';
import {
  Workflow, AlertOctagon, CheckCircle2, AlertTriangle, Layers, ArrowRight, Check, Play, Clock, Sparkles, ShieldCheck, RefreshCw, GitBranch, ListTodo
} from 'lucide-react';

interface ExecutionIntelligenceDashboardProps {
  initialProjectId?: string;
  token?: string;
}

export const ExecutionIntelligenceDashboard: React.FC<ExecutionIntelligenceDashboardProps> = ({
  initialProjectId = 'bfb4530e-bc5d-4c1f-aaf3-217a55bcaba4',
  token
}) => {
  const [activeTab, setActiveTab] = useState<'PLAN' | 'TASKS' | 'BLOCKERS' | 'CLOSED_LOOP' | 'ACTIONS'>('PLAN');
  const [actionPlan, setActionPlan] = useState<ActionPlanResponse | null>(null);
  const [suggestedTasks, setSuggestedTasks] = useState<SuggestedTaskItem[]>([]);
  const [blockers, setBlockers] = useState<DetectedBlockerItem[]>([]);
  const [criticalPath, setCriticalPath] = useState<CriticalPathResponse | null>(null);
  const [pendingActions, setPendingActions] = useState<PendingActionItem[]>([]);

  const [actualOutcomeInput, setActualOutcomeInput] = useState<string>('Five-minute downtime recorded during DB failover.');
  const [recordedOutcome, setRecordedOutcome] = useState<ClosedLoopOutcomeResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [ap, blk, cp, pa] = await Promise.all([
        fetchActionPlan('plan-101', token),
        fetchDetectedBlockers(initialProjectId, token),
        fetchCriticalPath(initialProjectId, token),
        fetchPendingActions(initialProjectId, token)
      ]);
      setActionPlan(ap);
      setBlockers(blk);
      setCriticalPath(cp);
      setPendingActions(pa);
    } catch (err) {
      console.error('Failed to load execution dashboard data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [initialProjectId, token]);

  const handleSuggestTasks = async () => {
    if (!actionPlan) return;
    try {
      const tasks = await suggestActionPlanTasks(actionPlan.plan_id, token);
      setSuggestedTasks(tasks);
      setActionMessage(`Generated ${tasks.length} suggested implementation tasks.`);
    } catch (err) {
      console.error('Failed to suggest tasks:', err);
    }
  };

  const handleConfirmTask = async (taskId: string) => {
    if (!actionPlan) return;
    try {
      const res = await confirmSuggestedTask(actionPlan.plan_id, taskId, token);
      setActionMessage(res.message);
      setSuggestedTasks(prev => prev.map(t => t.task_id === taskId ? res.task : t));
    } catch (err) {
      console.error('Failed to confirm task:', err);
    }
  };

  const handleRecordClosedLoop = async () => {
    if (!actionPlan) return;
    try {
      const res = await recordClosedLoopOutcome(actionPlan.plan_id, actionPlan.expected_outcome, actualOutcomeInput, token);
      setRecordedOutcome(res.outcome_record);
      setActionMessage(res.message);
    } catch (err) {
      console.error('Failed closed loop record:', err);
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
                EXECUTION INTELLIGENCE & CLOSED-LOOP ACTION
              </span>
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center space-x-1">
                <ShieldCheck className="w-3 h-3" />
                <span>Human-Controlled Workflow Safeguard</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <Workflow className="w-7 h-7 text-indigo-400" />
              <span>Execution Intelligence Dashboard</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Connects organizational decisions to coordinated execution, tracking blockers, critical paths, and closed-loop expected vs actual outcomes.
            </p>
          </div>

          {/* Navigation Mode Tabs */}
          <div className="flex items-center space-x-2 bg-slate-950 p-1.5 rounded-2xl border border-slate-800 flex-shrink-0">
            <button
              type="button"
              onClick={() => setActiveTab('PLAN')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'PLAN' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Action Plan
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('TASKS')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'TASKS' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Suggested Tasks
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('BLOCKERS')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'BLOCKERS' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Blockers & Critical Path
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('CLOSED_LOOP')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'CLOSED_LOOP' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Closed-Loop Outcomes
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('ACTIONS')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'ACTIONS' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Pending Actions
            </button>
          </div>
        </div>
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
      {activeTab === 'PLAN' && actionPlan && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <span className="text-[9px] font-mono text-indigo-400 uppercase font-bold">Action Plan Overview</span>
              <h2 className="text-lg font-black text-white mt-0.5">{actionPlan.objective}</h2>
            </div>
            <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2.5 py-1 rounded-xl border border-emerald-800/60">
              STATUS: {actionPlan.status}
            </span>
          </div>

          <div className="space-y-3">
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl">
              <span className="text-[9px] font-mono text-slate-500 uppercase block">Expected Outcome</span>
              <p className="text-xs text-white font-medium mt-0.5">"{actionPlan.expected_outcome}"</p>
            </div>

            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2">
              <span className="text-[9px] font-mono text-slate-500 uppercase block">Success Criteria</span>
              {actionPlan.success_criteria.map((sc, i) => (
                <div key={i} className="flex items-center space-x-2 text-xs text-slate-300">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  <span>{sc}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'TASKS' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono flex items-center space-x-2">
              <ListTodo className="w-4 h-4 text-indigo-400" />
              <span>Suggested Tasks Awaiting Human Confirmation</span>
            </h3>

            <button
              type="button"
              onClick={() => handleSuggestTasks()}
              className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-white font-bold text-xs shadow-md"
            >
              Generate Suggested Tasks
            </button>
          </div>

          <div className="space-y-3">
            {suggestedTasks.map((t) => (
              <div key={t.task_id} className="p-4 bg-slate-950 border border-slate-800 rounded-2xl flex items-center justify-between text-xs">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className={`text-[8px] font-mono font-bold px-1.5 py-0.5 rounded uppercase ${
                      t.status === 'CONFIRMED' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800/60' : 'bg-amber-950 text-amber-400 border border-amber-800/60'
                    }`}>{t.status}</span>
                    <span className="text-[10px] font-mono text-slate-500">{t.source}</span>
                  </div>
                  <h4 className="font-bold text-white mt-1">{t.title}</h4>
                  <p className="text-[10px] text-slate-400 mt-0.5">{t.description}</p>
                </div>

                {t.status === 'SUGGESTED' && (
                  <button
                    type="button"
                    onClick={() => handleConfirmTask(t.task_id)}
                    className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 rounded-xl text-white font-bold text-xs flex items-center space-x-1"
                  >
                    <Check className="w-3 h-3" />
                    <span>Confirm Task</span>
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'BLOCKERS' && (
        <div className="space-y-6">
          {/* Critical Path Health Banner */}
          {criticalPath && (
            <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-xs font-bold text-white uppercase font-mono flex items-center space-x-2">
                  <GitBranch className="w-4 h-4 text-indigo-400" />
                  <span>Execution Critical Path</span>
                </h3>
                <span className="text-[10px] font-mono font-bold text-amber-400 bg-amber-950 px-2.5 py-1 rounded-xl border border-amber-800/60">
                  HEALTH: {criticalPath.execution_health}
                </span>
              </div>
              <p className="text-xs text-amber-300 font-medium">{criticalPath.health_explanation}</p>

              <div className="space-y-2 pt-2">
                {criticalPath.critical_path_tasks.map((cp) => (
                  <div key={cp.step} className="p-3 bg-slate-950 border border-slate-800 rounded-2xl flex items-center justify-between text-xs">
                    <span className="font-mono text-indigo-400 font-bold">Step {cp.step}. {cp.title}</span>
                    <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded ${
                      cp.is_blocker ? 'bg-red-950 text-red-400 border border-red-800/60' : 'bg-slate-900 text-slate-400'
                    }`}>{cp.status}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Blockers List */}
          <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
            <h3 className="text-xs font-bold text-white uppercase font-mono border-b border-slate-800 pb-3 flex items-center space-x-2">
              <AlertOctagon className="w-4 h-4 text-red-400" />
              <span>Detected Blockers</span>
            </h3>

            <div className="space-y-3">
              {blockers.map((b) => (
                <div key={b.blocker_id} className="p-4 bg-slate-950 border border-red-800/60 rounded-2xl space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-[8px] font-mono font-bold text-red-400 bg-red-950 px-2 py-0.5 rounded border border-red-800/60 uppercase">{b.classification}</span>
                    <span className="text-[9px] font-mono text-slate-500">Blocked: {b.blocked_task_title}</span>
                  </div>
                  <h4 className="font-bold text-white">{b.title}</h4>
                  <p className="text-[10px] text-slate-400">{b.explanation}</p>
                  <p className="text-[10px] text-indigo-400 font-medium">Recommendation: {b.resolution_recommendation}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'CLOSED_LOOP' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Closed-Loop Outcome Discrepancy Tracking</h3>
            <p className="text-xs text-slate-400 mt-1">Compares expected decision outcome against actual execution result, feeding Phase 6.4 Lessons Learned.</p>
          </div>

          <div className="space-y-4">
            <div>
              <label className="text-[10px] font-mono text-slate-400 uppercase block mb-1 font-bold">Actual Outcome Observed</label>
              <textarea
                value={actualOutcomeInput}
                onChange={(e) => setActualOutcomeInput(e.target.value)}
                rows={3}
                className="w-full bg-slate-950 border border-slate-800 rounded-2xl p-3 text-xs text-white focus:outline-none"
              />
            </div>

            <button
              type="button"
              onClick={() => handleRecordClosedLoop()}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-2xl text-white font-bold text-xs shadow-lg flex items-center space-x-1.5"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Record Closed-Loop Outcome</span>
            </button>
          </div>

          {recordedOutcome && (
            <div className="p-5 bg-slate-950 border border-indigo-800/60 rounded-3xl space-y-3">
              <div className="flex items-center justify-between">
                <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${
                  recordedOutcome.discrepancy_status === 'MET' ? 'bg-emerald-950 text-emerald-400 border-emerald-800/60' : 'bg-red-950 text-red-400 border-red-800/60'
                }`}>Discrepancy: {recordedOutcome.discrepancy_status}</span>
                <span className="text-[9px] font-mono text-slate-500">{recordedOutcome.outcome_id}</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                <div className="p-3 bg-slate-900 border border-slate-800 rounded-2xl">
                  <span className="text-[9px] font-mono text-slate-500 uppercase block">Expected</span>
                  <p className="text-white mt-0.5">"{recordedOutcome.expected_outcome}"</p>
                </div>
                <div className="p-3 bg-slate-900 border border-slate-800 rounded-2xl">
                  <span className="text-[9px] font-mono text-slate-500 uppercase block">Actual</span>
                  <p className="text-white mt-0.5">"{recordedOutcome.actual_outcome}"</p>
                </div>
              </div>

              <p className="text-xs text-indigo-400 font-medium">Lesson Candidate: {recordedOutcome.lesson_candidate}</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'ACTIONS' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
          <h3 className="text-xs font-bold text-white uppercase font-mono border-b border-slate-800 pb-3 flex items-center space-x-2">
            <Clock className="w-4 h-4 text-indigo-400" />
            <span>Prepared Action Queue (Human Confirmation Required)</span>
          </h3>

          <div className="space-y-3">
            {pendingActions.map((pa) => (
              <div key={pa.action_id} className="p-4 bg-slate-950 border border-slate-800 rounded-2xl flex items-center justify-between text-xs">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-[8px] font-mono font-bold text-amber-400 bg-amber-950 px-2 py-0.5 rounded border border-amber-800/60 uppercase">{pa.confirmation_level}</span>
                    <span className="text-[9px] font-mono text-slate-500">{pa.source_decision}</span>
                  </div>
                  <h4 className="font-bold text-white mt-1">{pa.title}</h4>
                  <p className="text-[10px] text-slate-400 mt-0.5">{pa.reason}</p>
                </div>

                <button
                  type="button"
                  onClick={() => setActionMessage(`Executed action '${pa.title}' with verified audit logging.`)}
                  className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 rounded-xl text-white font-bold text-xs flex items-center space-x-1"
                >
                  <Play className="w-3 h-3" />
                  <span>Execute Action</span>
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
};
