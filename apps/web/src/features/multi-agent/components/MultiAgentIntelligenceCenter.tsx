import React, { useState, useEffect } from 'react';
import {
  fetchAgentRegistry, analyzeComplexQuestion, synthesizeAgentOutputs, draftPhase611Workflow, createDecisionFromAnalysis, fetchMultiAgentDigest,
  AgentRegistryItem, AnalysisJobResponse, SynthesisResponse, WorkflowDraftResponse, DecisionPromotedResponse, MultiAgentDigestResponse
} from '../multi-agent-api';
import {
  Users, ShieldCheck, CheckCircle2, AlertTriangle, Layers, Brain, Check, Sparkles, FileText, Activity, Workflow, ArrowRight
} from 'lucide-react';

interface MultiAgentIntelligenceCenterProps {
  initialProjectId?: string;
  token?: string;
}

export const MultiAgentIntelligenceCenter: React.FC<MultiAgentIntelligenceCenterProps> = ({
  initialProjectId = 'bfb4530e-bc5d-4c1f-aaf3-217a55bcaba4',
  token
}) => {
  const [activeTab, setActiveTab] = useState<'ROLES' | 'ANALYSIS' | 'SYNTHESIS' | 'HANDOFF'>('ROLES');
  const [registry, setRegistry] = useState<AgentRegistryItem[]>([]);
  const [digest, setDigest] = useState<MultiAgentDigestResponse | null>(null);

  const [job, setJob] = useState<AnalysisJobResponse | null>(null);
  const [synthesis, setSynthesis] = useState<SynthesisResponse | null>(null);
  const [workflowDraft, setWorkflowDraft] = useState<WorkflowDraftResponse | null>(null);
  const [promotedDecision, setPromotedDecision] = useState<DecisionPromotedResponse | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [reg, dig] = await Promise.all([
        fetchAgentRegistry(token),
        fetchMultiAgentDigest(token)
      ]);
      setRegistry(reg);
      setDigest(dig);
    } catch (err) {
      console.error('Failed to load multi-agent center:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [initialProjectId, token]);

  const handleAnalyze = async () => {
    try {
      const res = await analyzeComplexQuestion(initialProjectId, 'Should the organization migrate from JWT to OAuth?', token);
      setJob(res);
      setActionMessage(`Multi-Agent Routing triggered for question. 5 specialists assigned.`);
    } catch (err) {
      console.error('Failed complex analysis:', err);
    }
  };

  const handleSynthesize = async () => {
    if (!job) return;
    try {
      const res = await synthesizeAgentOutputs(job.job_id, token);
      setSynthesis(res);
      setActionMessage(`Synthesized 5 specialist outputs into grounded response '${res.synthesis_title}'.`);
    } catch (err) {
      console.error('Failed synthesis:', err);
    }
  };

  const handleDraftWorkflow = async () => {
    if (!job) return;
    try {
      const res = await draftPhase611Workflow(job.job_id, token);
      setWorkflowDraft(res);
      setActionMessage(`Created Phase 6.11 Workflow Draft '${res.draft_workflow_id}'. Proposal only, requires approval.`);
    } catch (err) {
      console.error('Failed drafting workflow:', err);
    }
  };

  const handleCreateDecision = async () => {
    if (!job) return;
    try {
      const res = await createDecisionFromAnalysis(job.job_id, 'Migrate to OAuth 2.0 Provider with 30m Sessions', token);
      setPromotedDecision(res);
      setActionMessage(`Created authorized Decision Record '${res.decision_id}' from analysis evidence.`);
    } catch (err) {
      console.error('Failed creating decision:', err);
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
                MULTI-AGENT INTELLIGENCE & COLLABORATIVE REASONING
              </span>
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center space-x-1">
                <ShieldCheck className="w-3 h-3" />
                <span>Governed Intelligence Fabric</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <Users className="w-7 h-7 text-indigo-400" />
              <span>Multi-Agent Intelligence Center</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Coordinates specialized internal AI roles (Knowledge, Decision, Risk, Dependency, Research, Quality) to analyze complex organizational problems.
            </p>
          </div>

          {/* Navigation Mode Tabs */}
          <div className="flex items-center space-x-2 bg-slate-950 p-1.5 rounded-2xl border border-slate-800 flex-shrink-0">
            <button
              type="button"
              onClick={() => setActiveTab('ROLES')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'ROLES' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Specialist Roles
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('ANALYSIS')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'ANALYSIS' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Multi-Agent Analysis
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('SYNTHESIS')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'SYNTHESIS' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Synthesis & Quality
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('HANDOFF')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'HANDOFF' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Phase 6.11 Handoff
            </button>
          </div>
        </div>

        {/* Digest Counters Bar */}
        {digest && (
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-2 border-t border-slate-800/60">
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Analyses Completed</span>
              <span className="text-lg font-black text-indigo-400">{digest.total_specialist_analyses_completed}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Disagreements Resolved</span>
              <span className="text-lg font-black text-emerald-400">{digest.disagreements_resolved}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Quality Gates Passed</span>
              <span className="text-lg font-black text-purple-400">{digest.quality_gates_passed}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Phase 6.11 Drafts</span>
              <span className="text-lg font-black text-amber-400">{digest.phase_611_workflow_drafts_created}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Active Providers</span>
              <span className="text-xs font-bold text-cyan-400 block mt-1">{digest.model_providers_active.join(' & ')}</span>
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
      {activeTab === 'ROLES' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
          <h3 className="text-xs font-bold text-white uppercase font-mono border-b border-slate-800 pb-3 flex items-center space-x-2">
            <Brain className="w-4 h-4 text-indigo-400" />
            <span>Registered Internal Specialist Capabilities</span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {registry.map(ag => (
              <div key={ag.agent_id} className="p-4 bg-slate-950 border border-slate-800 rounded-2xl text-xs space-y-1">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-white">{ag.name}</h4>
                  <span className="text-[8px] font-mono text-indigo-400 bg-slate-900 px-2 py-0.5 rounded font-bold">{ag.agent_id}</span>
                </div>
                <p className="text-[10px] text-slate-400">{ag.purpose}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'ANALYSIS' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-white uppercase font-mono">Multi-Agent Task Decomposition & Specialist Analysis</h3>
              <p className="text-xs text-slate-400 mt-1">Routes complex question across 5 parallel specialists with structured outputs.</p>
            </div>
            
            <button
              type="button"
              onClick={() => handleAnalyze()}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-2xl text-white font-bold text-xs shadow-lg flex items-center space-x-1.5"
            >
              <Sparkles className="w-4 h-4" />
              <span>Trigger Multi-Agent Analysis</span>
            </button>
          </div>

          {job && (
            <div className="space-y-4 text-xs">
              <div className="p-4 bg-slate-950 border border-indigo-800/60 rounded-2xl space-y-1">
                <span className="text-[9px] font-mono text-slate-500 uppercase font-bold">Complex Objective</span>
                <p className="text-white font-bold">"{job.question}"</p>
                <span className="text-[9px] font-mono text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 inline-block font-bold">Status: {job.status}</span>
              </div>

              <div className="space-y-3">
                <span className="text-[10px] font-mono text-slate-400 uppercase font-bold block">Specialist Analytical Outputs</span>
                {job.specialist_results.map(res => (
                  <div key={res.agent_id} className="p-3 bg-slate-950 border border-slate-800 rounded-2xl space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-white">{res.name}</span>
                      <span className="text-[8px] font-mono text-indigo-400 bg-slate-900 px-2 py-0.5 rounded uppercase">{res.confidence}</span>
                    </div>
                    <p className="text-slate-300">• {res.conclusion}</p>
                    <div className="flex items-center space-x-2 pt-1">
                      <span className="text-[8px] font-mono text-slate-500 uppercase font-bold">Evidence:</span>
                      {res.evidence.map((ev, i) => (
                        <span key={i} className="text-[8px] font-mono text-slate-400 bg-slate-900 px-2 py-0.5 rounded">{ev}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              {job.disagreements.length > 0 && (
                <div className="p-4 bg-amber-950/40 border border-amber-800/60 rounded-2xl space-y-2">
                  <span className="text-[9px] font-mono text-amber-400 bg-amber-950 px-2 py-0.5 rounded uppercase font-bold border border-amber-800/60">SPECIALIST DISAGREEMENT DETECTED</span>
                  {job.disagreements.map(dis => (
                    <div key={dis.disagreement_id} className="space-y-1">
                      <h5 className="font-bold text-white">{dis.topic}</h5>
                      <p className="text-[10px] text-slate-300">• {dis.specialist_A}</p>
                      <p className="text-[10px] text-slate-300">• {dis.specialist_B}</p>
                      <p className="text-[10px] text-emerald-400 font-bold mt-1">Resolution: {dis.resolution}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {activeTab === 'SYNTHESIS' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-white uppercase font-mono">Synthesis & Quality Gate Audit</h3>
              <p className="text-xs text-slate-400 mt-1">Combines specialist outputs into one coherent evidence-grounded response.</p>
            </div>
            
            <button
              type="button"
              onClick={() => handleSynthesize()}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-2xl text-white font-bold text-xs shadow-lg flex items-center space-x-1.5"
            >
              <Brain className="w-4 h-4" />
              <span>Synthesize Output</span>
            </button>
          </div>

          {synthesis && (
            <div className="p-5 bg-slate-950 border border-emerald-800/60 rounded-3xl space-y-4 text-xs">
              <div className="flex items-center justify-between">
                <h4 className="font-bold text-white text-sm">{synthesis.synthesis_title}</h4>
                <span className="text-[9px] font-mono text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 font-bold">{synthesis.quality_review_status}</span>
              </div>

              <div className="p-3 bg-slate-900 rounded-2xl space-y-1">
                <span className="text-[9px] font-mono text-slate-500 uppercase font-bold block">Summary Recommendation</span>
                <p className="text-white font-bold">{synthesis.summary_answer}</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-3 bg-slate-900 rounded-2xl space-y-1">
                  <span className="text-[9px] font-mono text-indigo-400 uppercase font-bold block">Trade-Offs</span>
                  {synthesis.trade_offs.map((to, i) => (
                    <p key={i} className="text-slate-300">• {to}</p>
                  ))}
                </div>

                <div className="p-3 bg-slate-900 rounded-2xl space-y-1">
                  <span className="text-[9px] font-mono text-amber-400 uppercase font-bold block">Known Risks</span>
                  {synthesis.known_risks.map((kr, i) => (
                    <p key={i} className="text-slate-300">• {kr}</p>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'HANDOFF' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-white uppercase font-mono">Phase 6.11 Controlled Workflow Handoff & Decision Promotion</h3>
              <p className="text-xs text-slate-400 mt-1">Converts approved multi-agent recommendations into Phase 6.11 draft workflows or decision records.</p>
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={() => handleCreateDecision()}
                className="px-3 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-2xl text-white font-bold text-xs flex items-center space-x-1"
              >
                <FileText className="w-4 h-4" />
                <span>Create Decision</span>
              </button>

              <button
                type="button"
                onClick={() => handleDraftWorkflow()}
                className="px-3 py-2 bg-purple-600 hover:bg-purple-500 rounded-2xl text-white font-bold text-xs flex items-center space-x-1"
              >
                <Workflow className="w-4 h-4" />
                <span>Draft Phase 6.11 Workflow</span>
              </button>
            </div>
          </div>

          {workflowDraft && (
            <div className="p-4 bg-slate-950 border border-purple-800/60 rounded-2xl text-xs space-y-1">
              <span className="text-[9px] font-mono text-purple-400 uppercase font-bold">Phase 6.11 Draft Workflow Proposal</span>
              <p className="text-white font-bold">Draft ID: {workflowDraft.draft_workflow_id} | Goal: "{workflowDraft.goal}"</p>
              <p className="text-slate-400">{workflowDraft.message}</p>
            </div>
          )}

          {promotedDecision && (
            <div className="p-4 bg-slate-950 border border-indigo-800/60 rounded-2xl text-xs space-y-1">
              <span className="text-[9px] font-mono text-indigo-400 uppercase font-bold">Authorized Decision Record</span>
              <p className="text-white font-bold">Decision ID: {promotedDecision.decision_id} | Title: "{promotedDecision.title}"</p>
              <p className="text-slate-400">Linked Evidence Sources: {promotedDecision.evidence_linked_count}</p>
            </div>
          )}
        </div>
      )}

    </div>
  );
};
