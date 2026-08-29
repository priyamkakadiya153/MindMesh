import React, { useState, useEffect } from 'react';
import {
  fetchProjectMemory, generateContextPack, synthesizeKnowledgeBrief, createKnowledgeHandoff, fetchDecisionMemory, fetchMemoryHealth, fetchMemoryDigest,
  ProjectMemoryResponse, ContextPackResponse, KnowledgeBriefResponse, KnowledgeHandoffResponse, DecisionMemoryResponse, MemoryHealthResponse, MemoryDigestResponse
} from '../memory-fabric-api';
import {
  Brain, Cpu, ShieldCheck, CheckCircle2, AlertTriangle, Layers, ArrowRight, BookOpen, Send, Sparkles, FileText, Check, Activity, Search
} from 'lucide-react';

interface OrganizationalMemoryFabricCenterProps {
  initialProjectId?: string;
  token?: string;
}

export const OrganizationalMemoryFabricCenter: React.FC<OrganizationalMemoryFabricCenterProps> = ({
  initialProjectId = 'bfb4530e-bc5d-4c1f-aaf3-217a55bcaba4',
  token
}) => {
  const [activeTab, setActiveTab] = useState<'PROJECT' | 'PACK' | 'BRIEF' | 'HANDOFF' | 'DECISION'>('PROJECT');
  const [projectMemory, setProjectMemory] = useState<ProjectMemoryResponse | null>(null);
  const [memoryHealth, setMemoryHealth] = useState<MemoryHealthResponse | null>(null);
  const [digest, setDigest] = useState<MemoryDigestResponse | null>(null);

  const [contextPack, setContextPack] = useState<ContextPackResponse | null>(null);
  const [knowledgeBrief, setKnowledgeBrief] = useState<KnowledgeBriefResponse | null>(null);
  const [handoff, setHandoff] = useState<KnowledgeHandoffResponse | null>(null);
  const [decisionMemory, setDecisionMemory] = useState<DecisionMemoryResponse | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [pm, mh, dig] = await Promise.all([
        fetchProjectMemory(initialProjectId, token),
        fetchMemoryHealth(token),
        fetchMemoryDigest(token)
      ]);
      setProjectMemory(pm);
      setMemoryHealth(mh);
      setDigest(dig);
    } catch (err) {
      console.error('Failed to load organizational memory fabric center:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [initialProjectId, token]);

  const handleGeneratePack = async () => {
    try {
      const res = await generateContextPack('TASK', 'task-deploy-101', token);
      setContextPack(res);
      setActionMessage(`Generated dynamic Context Pack for '${res.scope_id}'.`);
    } catch (err) {
      console.error('Failed context pack generation:', err);
    }
  };

  const handleSynthesizeBrief = async () => {
    try {
      const res = await synthesizeKnowledgeBrief(initialProjectId, token);
      setKnowledgeBrief(res);
      setActionMessage(`Synthesized evidence-grounded Knowledge Brief '${res.brief_title}'.`);
    } catch (err) {
      console.error('Failed brief synthesis:', err);
    }
  };

  const handleCreateHandoff = async () => {
    try {
      const res = await createKnowledgeHandoff(initialProjectId, 'user-recipient-404', token);
      setHandoff(res);
      setActionMessage(`Created context-rich Knowledge Handoff 'HND-101' for recipient.`);
    } catch (err) {
      console.error('Failed handoff creation:', err);
    }
  };

  const handleFetchDecisionMemory = async () => {
    try {
      const res = await fetchDecisionMemory('dec-102', token);
      setDecisionMemory(res);
      setActionMessage(`Retrieved Decision Rationale Memory for '#D-102'.`);
    } catch (err) {
      console.error('Failed decision memory retrieval:', err);
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
                ORGANIZATIONAL MEMORY FABRIC & KNOWLEDGE SYNTHESIS
              </span>
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center space-x-1">
                <ShieldCheck className="w-3 h-3" />
                <span>Continuous Memory Continuity</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <Brain className="w-7 h-7 text-indigo-400" />
              <span>Organizational Memory Fabric Center</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Turns connected knowledge, decisions, risks, and execution outcomes into continuous, context-aware organizational memory.
            </p>
          </div>

          {/* Navigation Mode Tabs */}
          <div className="flex items-center space-x-2 bg-slate-950 p-1.5 rounded-2xl border border-slate-800 flex-shrink-0">
            <button
              type="button"
              onClick={() => setActiveTab('PROJECT')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'PROJECT' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Project Memory
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('PACK')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'PACK' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Context Packs
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('BRIEF')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'BRIEF' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Knowledge Briefs
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('HANDOFF')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'HANDOFF' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Knowledge Handoffs
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('DECISION')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'DECISION' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Decision Rationale
            </button>
          </div>
        </div>

        {/* Digest Counters Bar */}
        {digest && (
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-2 border-t border-slate-800/60">
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Memory Objects</span>
              <span className="text-lg font-black text-indigo-400">{digest.total_memory_objects}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Active Packs</span>
              <span className="text-lg font-black text-amber-400">{digest.active_context_packs}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Knowledge Briefs</span>
              <span className="text-lg font-black text-emerald-400">{digest.synthesized_knowledge_briefs}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Handoffs Done</span>
              <span className="text-lg font-black text-purple-400">{digest.knowledge_handoffs_completed}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Lessons Reused</span>
              <span className="text-lg font-black text-cyan-400">{digest.lessons_reused}</span>
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
      {activeTab === 'PROJECT' && (
        <div className="space-y-6">
          {/* Project Memory Canvas */}
          <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
            <h3 className="text-xs font-bold text-white uppercase font-mono border-b border-slate-800 pb-3 flex items-center space-x-2">
              <BookOpen className="w-4 h-4 text-indigo-400" />
              <span>Project Memory Snapshot & Timeline</span>
            </h3>

            {projectMemory && (
              <div className="space-y-4 text-xs">
                <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-1">
                  <span className="text-[9px] font-mono text-slate-500 uppercase font-bold">Project Purpose</span>
                  <p className="text-white font-bold">{projectMemory.purpose}</p>
                  <span className="text-[9px] font-mono text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 inline-block mt-1 font-bold">State: {projectMemory.current_state}</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Decisions */}
                  <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2">
                    <span className="text-[9px] font-mono text-indigo-400 uppercase font-bold block">Key Decisions</span>
                    {projectMemory.decisions.map(d => (
                      <div key={d.id} className="p-2 bg-slate-900 rounded-xl flex items-center justify-between">
                        <span className="font-bold text-white">{d.title}</span>
                        <span className="text-[8px] font-mono text-slate-400 bg-slate-950 px-2 py-0.5 rounded uppercase">{d.status}</span>
                      </div>
                    ))}
                  </div>

                  {/* Lessons */}
                  <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2">
                    <span className="text-[9px] font-mono text-cyan-400 uppercase font-bold block">Recorded Lessons</span>
                    {projectMemory.lessons.map(l => (
                      <div key={l.id} className="p-2 bg-slate-900 rounded-xl space-y-1">
                        <span className="text-[9px] font-mono text-slate-500 uppercase block font-bold">Situation: {l.situation}</span>
                        <p className="text-white font-bold">"{l.lesson}"</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Memory Health Gaps */}
          {memoryHealth && (
            <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
              <h3 className="text-xs font-bold text-white uppercase font-mono border-b border-slate-800 pb-3 flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                <span>Memory Health & Identified Coverage Gaps</span>
              </h3>

              <div className="space-y-3">
                {memoryHealth.memory_gaps.map(g => (
                  <div key={g.gap_id} className="p-4 bg-slate-950 border border-slate-800 rounded-2xl text-xs space-y-1">
                    <span className="text-[9px] font-mono text-amber-400 bg-amber-950 px-2 py-0.5 rounded uppercase font-bold border border-amber-800/60">MEMORY GAP DETECTED</span>
                    <h4 className="font-bold text-white mt-1">{g.title}</h4>
                    <p className="text-[10px] text-slate-400">{g.description}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'PACK' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-white uppercase font-mono">Dynamic Context Pack Generator</h3>
              <p className="text-xs text-slate-400 mt-1">Assembles task-specific, meeting-specific, or decision-specific Context Packs dynamically.</p>
            </div>
            
            <button
              type="button"
              onClick={() => handleGeneratePack()}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-2xl text-white font-bold text-xs shadow-lg flex items-center space-x-1.5"
            >
              <Cpu className="w-4 h-4" />
              <span>Generate Context Pack</span>
            </button>
          </div>

          {contextPack && (
            <div className="p-5 bg-slate-950 border border-indigo-800/60 rounded-3xl space-y-4 text-xs">
              <h4 className="font-bold text-white text-sm">{contextPack.title}</h4>
              <p className="text-slate-300">{contextPack.current_state}</p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-3 bg-slate-900 rounded-2xl space-y-1">
                  <span className="text-[9px] font-mono text-indigo-400 uppercase font-bold block">Relevant Knowledge</span>
                  {contextPack.relevant_knowledge.map((rk, i) => (
                    <p key={i} className="text-slate-300">• {rk}</p>
                  ))}
                </div>

                <div className="p-3 bg-slate-900 rounded-2xl space-y-1">
                  <span className="text-[9px] font-mono text-amber-400 uppercase font-bold block">Known Risks</span>
                  {contextPack.known_risks.map((kr, i) => (
                    <p key={i} className="text-slate-300">• {kr}</p>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'BRIEF' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-white uppercase font-mono">Grounded Knowledge Brief Synthesis Engine</h3>
              <p className="text-xs text-slate-400 mt-1">Combines multi-source evidence into grounded Knowledge Briefs with source traceability.</p>
            </div>
            
            <button
              type="button"
              onClick={() => handleSynthesizeBrief()}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-2xl text-white font-bold text-xs shadow-lg flex items-center space-x-1.5"
            >
              <Sparkles className="w-4 h-4" />
              <span>Synthesize Knowledge Brief</span>
            </button>
          </div>

          {knowledgeBrief && (
            <div className="p-5 bg-slate-950 border border-emerald-800/60 rounded-3xl space-y-4 text-xs">
              <div className="flex items-center justify-between">
                <h4 className="font-bold text-white text-sm">{knowledgeBrief.brief_title}</h4>
                <span className="text-[9px] font-mono text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 font-bold">{knowledgeBrief.provenance_label}</span>
              </div>

              <p className="text-slate-300">{knowledgeBrief.overview}</p>

              <div className="space-y-3 pt-2">
                {knowledgeBrief.sections.map((sec, i) => (
                  <div key={i} className="p-3 bg-slate-900 rounded-2xl space-y-1">
                    <span className="text-[10px] font-bold text-white block">{sec.heading}</span>
                    <p className="text-slate-300">{sec.content}</p>
                    <div className="flex items-center space-x-2 pt-1">
                      <span className="text-[8px] font-mono text-slate-500 uppercase font-bold">Sources:</span>
                      {sec.sources.map((s, idx) => (
                        <span key={idx} className="text-[8px] font-mono text-indigo-400 bg-slate-950 px-2 py-0.5 rounded">{s}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'HANDOFF' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-white uppercase font-mono">Context-Rich Knowledge Handoff Manager</h3>
              <p className="text-xs text-slate-400 mt-1">Facilitates seamless context-rich handoffs between team members or project phases without context loss.</p>
            </div>
            
            <button
              type="button"
              onClick={() => handleCreateHandoff()}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-2xl text-white font-bold text-xs shadow-lg flex items-center space-x-1.5"
            >
              <Send className="w-4 h-4" />
              <span>Create Handoff</span>
            </button>
          </div>

          {handoff && (
            <div className="p-5 bg-slate-950 border border-slate-800 rounded-3xl space-y-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-[9px] font-mono text-indigo-400 bg-slate-900 px-2 py-0.5 rounded font-bold">Handoff #{handoff.handoff_id}</span>
                <span className="text-[9px] font-mono text-emerald-400 font-bold uppercase">{handoff.status}</span>
              </div>

              <p className="text-white font-bold">Current State: "{handoff.current_state}"</p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                <div className="p-3 bg-slate-900 rounded-2xl space-y-1">
                  <span className="text-[9px] font-mono text-indigo-400 uppercase font-bold block">Key Decisions</span>
                  {handoff.key_decisions.map((kd, i) => (
                    <p key={i} className="text-slate-300">• {kd}</p>
                  ))}
                </div>
                <div className="p-3 bg-slate-900 rounded-2xl space-y-1">
                  <span className="text-[9px] font-mono text-amber-400 uppercase font-bold block">Outstanding Work</span>
                  {handoff.outstanding_work.map((ow, i) => (
                    <p key={i} className="text-slate-300">• {ow}</p>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'DECISION' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-white uppercase font-mono">Decision Rationale & Execution Memory</h3>
              <p className="text-xs text-slate-400 mt-1">Preserves decision rationale ("Why did we choose this?") with evidence, alternatives, and outcomes.</p>
            </div>
            
            <button
              type="button"
              onClick={() => handleFetchDecisionMemory()}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-2xl text-white font-bold text-xs shadow-lg flex items-center space-x-1.5"
            >
              <Search className="w-4 h-4" />
              <span>Lookup Decision #D-102</span>
            </button>
          </div>

          {decisionMemory && (
            <div className="p-5 bg-slate-950 border border-indigo-800/60 rounded-3xl space-y-4 text-xs">
              <div className="p-3 bg-slate-900 rounded-2xl space-y-1">
                <span className="text-[9px] font-mono text-slate-500 uppercase font-bold block">Problem Statement</span>
                <p className="text-white font-bold">{decisionMemory.problem_statement}</p>
              </div>

              <div className="p-3 bg-indigo-950/80 border border-indigo-800/60 rounded-2xl space-y-1">
                <span className="text-[9px] font-mono text-indigo-400 uppercase font-bold block">Chosen Option & Reasoning</span>
                <p className="text-white font-bold">{decisionMemory.chosen_option}</p>
                <p className="text-[10px] text-indigo-300 mt-1">{decisionMemory.reasoning}</p>
              </div>

              <div className="p-3 bg-slate-900 rounded-2xl space-y-1">
                <span className="text-[9px] font-mono text-emerald-400 uppercase font-bold block">Execution Outcome</span>
                <p className="text-white font-bold">{decisionMemory.outcome}</p>
              </div>
            </div>
          )}
        </div>
      )}

    </div>
  );
};
