import React, { useState, useEffect } from 'react';
import {
  fetchSpecialistAgents, decomposeTask, routeTask, executeAgentSubtask, verifyAndSynthesize,
  AgentDefinition, TaskDecompositionResponse, RouteResponse, SubtaskExecutionResponse, SynthesisResponse
} from '../multi-agent-api';
import {
  Cpu, Users, ShieldCheck, Zap, Layers, RefreshCw, FileText, ArrowRight, Activity, GitCommit, AlertOctagon, CheckCircle2
} from 'lucide-react';

interface MultiAgentCenterProps {
  initialProjectId?: string;
  token?: string;
}

export const MultiAgentCenter: React.FC<MultiAgentCenterProps> = ({
  initialProjectId,
  token
}) => {
  const [agents, setAgents] = useState<AgentDefinition[]>([]);
  const [intentInput, setIntentInput] = useState<string>('Evaluate whether Project Alpha should migrate backend service before next release.');

  const [decompRes, setDecompRes] = useState<TaskDecompositionResponse | null>(null);
  const [routeRes, setRouteRes] = useState<RouteResponse | null>(null);
  const [execTrace, setExecTrace] = useState<SubtaskExecutionResponse[]>([]);
  const [synthesisRes, setSynthesisRes] = useState<SynthesisResponse | null>(null);

  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const loadAgents = async () => {
    setIsLoading(true);
    try {
      const data = await fetchSpecialistAgents(token);
      setAgents(data);
    } catch (err) {
      console.error('Failed to fetch specialist agents:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAgents();
  }, [token]);

  const handleDecomposeAndRoute = async () => {
    setIsLoading(true);
    try {
      const decomp = await decomposeTask(intentInput, initialProjectId, token);
      setDecompRes(decomp);

      const route = await routeTask(decomp.decomposition_id, token);
      setRouteRes(route);

      setActionMessage(`Task decomposed into ${decomp.subtasks.length} subtasks and routed to specialist agents.`);
    } catch (err) {
      console.error('Decomposition failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunSubtasksAndSynthesize = async () => {
    if (!decompRes) return;
    setIsLoading(true);
    try {
      const traceResults: SubtaskExecutionResponse[] = [];
      for (const st of decompRes.subtasks) {
        const res = await executeAgentSubtask(st.subtask_id, st.assigned_agent_id, {}, token);
        traceResults.push(res);
      }
      setExecTrace(traceResults);

      const synth = await verifyAndSynthesize(traceResults.map(t => t.output), token);
      setSynthesisRes(synth);

      setActionMessage(`Executed ${traceResults.length} specialist agent subtasks. Verification status: ${synth.verification_status}`);
    } catch (err) {
      console.error('Subtask execution and synthesis failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6 text-slate-100 font-sans select-none">
      
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-violet-950/80 to-slate-900 border border-violet-800/60 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-violet-400 px-2.5 py-0.5 bg-violet-950 rounded border border-violet-800/60">
                CONTROLLED MULTI-AGENT INTELLIGENCE
              </span>
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center space-x-1">
                <ShieldCheck className="w-3 h-3" />
                <span>Bounded Delegation & Human Control</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <Cpu className="w-7 h-7 text-violet-400" />
              <span>MindMesh Multi-Agent Center</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Coordinates specialized AI roles with capability discovery, prompt-injection defense, and evidence-grounded synthesis.
            </p>
          </div>

          <div className="flex items-center space-x-4 bg-slate-950 p-3 rounded-2xl border border-slate-800 flex-shrink-0">
            <div className="text-center">
              <span className="text-[10px] font-mono text-slate-400 uppercase font-bold block">Specialists</span>
              <span className="text-lg font-black text-violet-400">{agents.length}</span>
            </div>
            <div className="h-8 w-px bg-slate-800" />
            <div className="text-center">
              <span className="text-[10px] font-mono text-slate-400 uppercase font-bold block">Policy</span>
              <span className="text-xs font-mono font-bold text-emerald-400">ISOLATED</span>
            </div>
          </div>
        </div>
      </div>

      {actionMessage && (
        <div className="p-3 bg-violet-950/80 border border-violet-800/60 rounded-2xl text-xs text-violet-200 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Activity className="w-4 h-4 text-violet-400" />
            <span>{actionMessage}</span>
          </div>
          <button type="button" onClick={() => setActionMessage(null)} className="text-[10px] text-slate-400 hover:text-white font-mono">Dismiss</button>
        </div>
      )}

      {/* Specialist Agent Registry */}
      <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
        <h3 className="text-xs font-bold text-white uppercase font-mono border-b border-slate-800 pb-2">Registered Specialist Agents</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
          {agents.map(ag => (
            <div key={ag.agent_id} className="p-3 bg-slate-950 border border-slate-800 rounded-2xl space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-violet-400 font-mono">{ag.name}</span>
                <span className="text-[9px] font-mono text-emerald-400 font-bold bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 uppercase">{ag.status}</span>
              </div>
              <p className="text-slate-300 text-[11px] font-bold">{ag.role}</p>
              <div className="flex flex-wrap gap-1 pt-1">
                {ag.capabilities.map(cap => (
                  <span key={cap} className="text-[8px] font-mono bg-slate-900 text-slate-400 px-1.5 py-0.5 rounded border border-slate-800">{cap}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Task Decomposition & Routing Input */}
      <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
        <h3 className="text-xs font-bold text-white uppercase font-mono border-b border-slate-800 pb-2">Orchestrate Complex Objective</h3>
        <div>
          <label className="text-slate-400 font-bold text-xs block mb-1">Complex User Intent:</label>
          <input
            type="text"
            value={intentInput}
            onChange={(e) => setIntentInput(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-white focus:outline-none"
          />
        </div>
        <div className="flex items-center space-x-3">
          <button
            type="button"
            onClick={handleDecomposeAndRoute}
            disabled={isLoading}
            className="px-4 py-2 bg-violet-600 hover:bg-violet-500 rounded-xl text-white font-bold text-xs flex items-center space-x-2"
          >
            <Zap className="w-4 h-4" />
            <span>Decompose & Route Task</span>
          </button>

          {decompRes && (
            <button
              type="button"
              onClick={handleRunSubtasksAndSynthesize}
              disabled={isLoading}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-xl text-white font-bold text-xs flex items-center space-x-2"
            >
              <Users className="w-4 h-4" />
              <span>Execute Specialists & Synthesize</span>
            </button>
          )}
        </div>
      </div>

      {/* Decomposition DAG & Subtask Routes */}
      {decompRes && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
          <h3 className="text-xs font-bold text-white uppercase font-mono border-b border-slate-800 pb-2">Subtask Decomposition DAG</h3>
          <div className="space-y-2 text-xs">
            {decompRes.subtasks.map(st => (
              <div key={st.subtask_id} className="p-3 bg-slate-950 border border-slate-800 rounded-2xl flex items-center justify-between">
                <div>
                  <span className="font-bold text-violet-400 font-mono uppercase">{st.subtask_id}</span>
                  <span className="text-white ml-2 font-bold">{st.goal}</span>
                </div>
                <span className="text-[10px] font-mono text-slate-400 font-bold bg-slate-900 px-2 py-0.5 rounded border border-slate-800 uppercase">
                  Assigned: {st.assigned_agent_id}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Execution Trace & Evidence Synthesis */}
      {synthesisRes && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <span className="text-[10px] font-mono text-emerald-400 font-bold uppercase bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60">
              STATUS: {synthesisRes.verification_status}
            </span>
            <h3 className="text-base font-bold text-white mt-1">{synthesisRes.synthesized_brief.title}</h3>
          </div>

          <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-3 text-xs">
            <span className="font-bold text-violet-400 font-mono block uppercase">Synthesized Recommendation</span>
            <p className="text-white font-bold text-sm">{synthesisRes.synthesized_brief.recommended_choice}</p>
            <p className="text-slate-300">• Evidence Provenance: {synthesisRes.synthesized_brief.evidence_provenance.join(', ')}</p>

            {synthesisRes.conflicts_detected.length > 0 && (
              <div className="pt-2 space-y-2">
                <span className="font-bold text-amber-400 font-mono block uppercase">Agent Disagreement Resolved</span>
                {synthesisRes.conflicts_detected.map(c => (
                  <div key={c.conflict_id} className="p-2.5 bg-amber-950/30 border border-amber-800/60 rounded-xl text-slate-200">
                    <p>• <strong>{c.agent_a}:</strong> {c.claim_a}</p>
                    <p>• <strong>{c.agent_b}:</strong> {c.claim_b}</p>
                    <p className="text-emerald-400 font-bold mt-1">• Resolution: {c.resolution}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

    </div>
  );
};
