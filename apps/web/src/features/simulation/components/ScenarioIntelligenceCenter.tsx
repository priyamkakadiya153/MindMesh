import React, { useState, useEffect } from 'react';
import {
  fetchDigitalTwinSnapshot, createScenario, runSimulation, compareScenarios, handoffScenarioToWorkflow,
  DigitalTwinResponse, CreateScenarioResponse, RunSimulationResponse, CompareScenariosResponse, HandoffScenarioResponse
} from '../organizational-simulation-api';
import {
  Cpu, Play, Layers, GitBranch, ArrowRight, ShieldCheck, AlertTriangle, CheckCircle2, RefreshCw, BarChart3, HelpCircle, Activity, Sparkles
} from 'lucide-react';

interface ScenarioIntelligenceCenterProps {
  initialProjectId?: string;
  token?: string;
}

export const ScenarioIntelligenceCenter: React.FC<ScenarioIntelligenceCenterProps> = ({
  initialProjectId,
  token
}) => {
  const [activeTab, setActiveTab] = useState<'TWIN' | 'SIMULATE' | 'PROPAGATION' | 'COMPARE' | 'HANDOFF'>('TWIN');
  const [digitalTwin, setDigitalTwin] = useState<DigitalTwinResponse | null>(null);

  // Scenario Creation state
  const [nlQueryInput, setNlQueryInput] = useState<string>('What if we delay Project Alpha by 2 weeks, but add 1 engineer and run testing in parallel?');
  const [createdScenario, setCreatedScenario] = useState<CreateScenarioResponse | null>(null);

  // Simulation Run state
  const [simulationResult, setSimulationResult] = useState<RunSimulationResponse | null>(null);

  // Comparison state
  const [comparisonResult, setComparisonResult] = useState<CompareScenariosResponse | null>(null);

  // Handoff & Stale Guard state
  const [simulateStaleCheck, setSimulateStaleCheck] = useState<boolean>(false);
  const [handoffResult, setHandoffResult] = useState<HandoffScenarioResponse | null>(null);

  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const loadDigitalTwin = async () => {
    setIsLoading(true);
    try {
      const data = await fetchDigitalTwinSnapshot(token);
      setDigitalTwin(data);
    } catch (err) {
      console.error('Failed to load digital twin:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDigitalTwin();
  }, [token]);

  const handleCreateScenario = async () => {
    setIsLoading(true);
    try {
      const scn = await createScenario('Project Alpha Scenario A', nlQueryInput, [], token);
      setCreatedScenario(scn);
      setActionMessage(`Scenario '${scn.scenario_id}' created with ${scn.changes.length} structured changes.`);
    } catch (err) {
      console.error('Create scenario failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunSimulation = async () => {
    if (!createdScenario) return;
    setIsLoading(true);
    try {
      const res = await runSimulation(createdScenario.scenario_id, token);
      setSimulationResult(res);
      setActionMessage(`Simulation run '${res.simulation_run_id}' completed with ${res.simulation_confidence}.`);
    } catch (err) {
      console.error('Run simulation failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCompareScenarios = async () => {
    setIsLoading(true);
    try {
      const scnId = createdScenario?.scenario_id || 'scn-opt-a';
      const res = await compareScenarios([scnId, 'scn-opt-b'], token);
      setComparisonResult(res);
      setActionMessage(`Compared ${res.scenarios_evaluated.length} scenarios side-by-side.`);
    } catch (err) {
      console.error('Compare scenarios failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleHandoff = async () => {
    if (!createdScenario) return;
    setIsLoading(true);
    try {
      const res = await handoffScenarioToWorkflow(createdScenario.scenario_id, simulateStaleCheck, token);
      setHandoffResult(res);
      setActionMessage(`Handoff status: ${res.handoff_status}.`);
    } catch (err) {
      console.error('Handoff scenario failed:', err);
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
                ORGANIZATIONAL DIGITAL TWIN & WHAT-IF ENGINE
              </span>
              <span className="text-[10px] font-mono font-bold text-amber-400 bg-amber-950 px-2 py-0.5 rounded border border-amber-800/60 flex items-center space-x-1">
                <ShieldCheck className="w-3 h-3" />
                <span>Simulation != Execution Guard Active</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <Cpu className="w-7 h-7 text-indigo-400" />
              <span>MindMesh Scenario Intelligence Center</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Simulates possible futures before committing to decisions. Propagates downstream graph impact, models uncertainty ranges, and detects stale state before execution.
            </p>
          </div>

          <div className="flex items-center space-x-4 bg-slate-950 p-3 rounded-2xl border border-slate-800 flex-shrink-0">
            <div className="text-center">
              <span className="text-[10px] font-mono text-slate-400 uppercase font-bold block">Twin State</span>
              <span className="text-lg font-black text-emerald-400">{digitalTwin?.data_freshness || 'CURRENT'}</span>
            </div>
            <div className="h-8 w-px bg-slate-800" />
            <div className="text-center">
              <span className="text-[10px] font-mono text-slate-400 uppercase font-bold block">Entities</span>
              <span className="text-lg font-black text-indigo-400">
                {digitalTwin ? digitalTwin.modeled_entities.projects_count + digitalTwin.modeled_entities.tasks_count : 32}
              </span>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex flex-wrap items-center gap-2 bg-slate-950 p-1.5 rounded-2xl border border-slate-800 w-fit">
          <button
            type="button"
            onClick={() => setActiveTab('TWIN')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
              activeTab === 'TWIN' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Digital Twin Inspector
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('SIMULATE')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
              activeTab === 'SIMULATE' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            What-If Scenario Builder
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('PROPAGATION')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
              activeTab === 'PROPAGATION' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Impact Propagation & Sensitivity
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('COMPARE')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
              activeTab === 'COMPARE' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Scenario Comparison
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('HANDOFF')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
              activeTab === 'HANDOFF' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Workflow Execution Handoff
          </button>
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

      {/* Tab Contents */}
      {activeTab === 'TWIN' && digitalTwin && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Digital Twin Snapshot ({digitalTwin.snapshot_id})</h3>
            <p className="text-xs text-slate-400 mt-1">Structured snapshot of organizational entities, relationships, constraints, and freshness.</p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 text-center">
              <span className="text-slate-400 font-mono text-[10px] uppercase block">Projects</span>
              <span className="text-xl font-black text-indigo-400">{digitalTwin.modeled_entities.projects_count}</span>
            </div>
            <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 text-center">
              <span className="text-slate-400 font-mono text-[10px] uppercase block">Tasks</span>
              <span className="text-xl font-black text-indigo-400">{digitalTwin.modeled_entities.tasks_count}</span>
            </div>
            <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 text-center">
              <span className="text-slate-400 font-mono text-[10px] uppercase block">Dependencies</span>
              <span className="text-xl font-black text-indigo-400">{digitalTwin.modeled_entities.dependencies_count}</span>
            </div>
            <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 text-center">
              <span className="text-slate-400 font-mono text-[10px] uppercase block">Active Risks</span>
              <span className="text-xl font-black text-amber-400">{digitalTwin.modeled_entities.active_risks_count}</span>
            </div>
            <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 text-center">
              <span className="text-slate-400 font-mono text-[10px] uppercase block">Operating Controls</span>
              <span className="text-xl font-black text-emerald-400">{digitalTwin.modeled_entities.operating_controls_count}</span>
            </div>
            <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 text-center">
              <span className="text-slate-400 font-mono text-[10px] uppercase block">Workflows</span>
              <span className="text-xl font-black text-teal-400">{digitalTwin.modeled_entities.active_workflows_count}</span>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'SIMULATE' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Natural Language What-If Scenario Builder</h3>
            <p className="text-xs text-slate-400 mt-1">Parses what-if hypotheses into structured change specs with declared assumptions.</p>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <label className="text-slate-300 font-bold block mb-1">What-If Natural Language Query:</label>
              <textarea
                value={nlQueryInput}
                onChange={(e) => setNlQueryInput(e.target.value)}
                rows={3}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white focus:outline-none"
              />
            </div>

            <button
              type="button"
              onClick={handleCreateScenario}
              disabled={isLoading}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-white font-bold text-xs flex items-center space-x-2"
            >
              <Sparkles className="w-4 h-4" />
              <span>Parse & Construct Scenario Spec</span>
            </button>
          </div>

          {createdScenario && (
            <div className="p-4 bg-slate-950 border border-indigo-800/60 rounded-2xl space-y-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-bold text-indigo-400 font-mono">Scenario Spec: {createdScenario.scenario_id}</span>
                <span className="text-[9px] font-mono text-emerald-400 font-bold bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 uppercase">{createdScenario.status}</span>
              </div>
              <p className="text-slate-300 font-bold">• {createdScenario.name}</p>

              <div className="space-y-1">
                <span className="text-slate-400 font-mono text-[10px] uppercase font-bold block">Structured Changes ({createdScenario.changes.length}):</span>
                {createdScenario.changes.map((chg, idx) => (
                  <div key={idx} className="text-slate-300 bg-slate-900 p-2 rounded-xl border border-slate-800">
                    <span className="font-bold text-indigo-300">{chg.target}</span>: {chg.attribute} ({chg.original_value} → {chg.new_value}) - <span className="italic text-slate-400">{chg.reason}</span>
                  </div>
                ))}
              </div>

              <button
                type="button"
                onClick={handleRunSimulation}
                disabled={isLoading}
                className="mt-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-xl text-white font-bold text-xs flex items-center space-x-2"
              >
                <Play className="w-4 h-4" />
                <span>Run What-If Simulation Engine</span>
              </button>
            </div>
          )}
        </div>
      )}

      {activeTab === 'PROPAGATION' && simulationResult && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Graph Impact Propagation & Uncertainty Ranges</h3>
            <p className="text-xs text-slate-400 mt-1">Calculates direct and indirect downstream graph impacts across cost, time, and risk.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2">
              <span className="font-bold text-indigo-400 font-mono uppercase block">Modeled Delta Outcomes</span>
              <p className="text-slate-300">• Duration: {simulationResult.modeled_delta.duration_delta}</p>
              <p className="text-slate-300">• Cost: {simulationResult.modeled_delta.cost_delta}</p>
              <p className="text-slate-300">• Risk: {simulationResult.modeled_delta.risk_delta}</p>
              <p className="text-slate-300">• Compliance: {simulationResult.modeled_delta.compliance_impact}</p>
            </div>

            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2">
              <span className="font-bold text-teal-400 font-mono uppercase block">Range-First Uncertainty</span>
              <p className="text-emerald-400">• Best Case: {simulationResult.uncertainty_range.best_case}</p>
              <p className="text-indigo-300">• Expected Case: {simulationResult.uncertainty_range.expected_case}</p>
              <p className="text-amber-400">• Worst Case: {simulationResult.uncertainty_range.worst_case}</p>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'COMPARE' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Multi-Scenario Comparison Matrix</h3>
            <p className="text-xs text-slate-400 mt-1">Side-by-side trade-off matrix comparing duration, cost, and risk profiles.</p>
          </div>

          <button
            type="button"
            onClick={handleCompareScenarios}
            disabled={isLoading}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-white font-bold text-xs flex items-center space-x-2"
          >
            <BarChart3 className="w-4 h-4" />
            <span>Generate Side-by-Side Matrix</span>
          </button>

          {comparisonResult && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                {comparisonResult.scenarios_evaluated.map(s => (
                  <div key={s.scenario_id} className="p-4 bg-slate-950 border border-indigo-800/60 rounded-2xl space-y-2">
                    <span className="font-bold text-indigo-400 font-mono block">Rank #{s.recommendation_rank}: {s.name}</span>
                    <p className="text-slate-300">• Duration: {s.duration_estimate}</p>
                    <p className="text-slate-300">• Cost: {s.cost_estimate}</p>
                    <p className="text-slate-300">• Risk Level: {s.risk_level}</p>
                  </div>
                ))}
              </div>
              <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-300 italic">
                Trade-off Summary: {comparisonResult.tradeoff_summary}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'HANDOFF' && createdScenario && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Workflow Execution Handoff & Stale Guard</h3>
            <p className="text-xs text-slate-400 mt-1">Validates freshness before creating a Phase 6.27 execution workflow from an approved scenario.</p>
          </div>

          <div className="flex items-center space-x-2 text-xs">
            <input
              type="checkbox"
              id="staleCheck"
              checked={simulateStaleCheck}
              onChange={(e) => setSimulateStaleCheck(e.target.checked)}
              className="rounded bg-slate-950 border-slate-800 text-indigo-600"
            />
            <label htmlFor="staleCheck" className="text-slate-400">Simulate production state mutation (Triggers STALE scenario block)</label>
          </div>

          <button
            type="button"
            onClick={handleHandoff}
            disabled={isLoading}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-white font-bold text-xs flex items-center space-x-2"
          >
            <GitBranch className="w-4 h-4" />
            <span>Validate & Hand Off Scenario to Workflow</span>
          </button>

          {handoffResult && (
            <div className={`p-4 rounded-2xl space-y-2 text-xs border ${
              handoffResult.handoff_status.includes('BLOCKED') ? 'bg-red-950/40 border-red-800/60 text-red-200' : 'bg-emerald-950/40 border-emerald-800/60 text-emerald-200'
            }`}>
              <span className="font-bold font-mono block uppercase">Handoff Status: {handoffResult.handoff_status}</span>
              {handoffResult.error_reason ? (
                <p className="text-red-400 font-bold">• Error: {handoffResult.error_reason}</p>
              ) : (
                <div className="space-y-1">
                  <p className="text-emerald-400 font-bold">• Created Workflow ID: {handoffResult.created_workflow_id}</p>
                  <p className="text-slate-300">• Workflow Name: {handoffResult.workflow_name}</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

    </div>
  );
};
