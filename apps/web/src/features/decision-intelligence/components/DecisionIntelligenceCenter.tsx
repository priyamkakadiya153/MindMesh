import React, { useState, useEffect } from 'react';
import {
  createDecisionWorkspace, fetchDecisionWorkspace, addDecisionEvidence, generateDecisionRecommendation, finalizeDecision, createDecisionRetrospective,
  DecisionWorkspaceResponse, GroundedRecommendationResponse
} from '../decision-intelligence-api';
import {
  Scale, ShieldAlert, Sparkles, CheckCircle2, AlertTriangle, Layers, ArrowRight, Check, HelpCircle, FileText, Lock, UserCheck, RefreshCw
} from 'lucide-react';

interface DecisionIntelligenceCenterProps {
  initialWorkspaceId?: string;
  token?: string;
}

export const DecisionIntelligenceCenter: React.FC<DecisionIntelligenceCenterProps> = ({
  initialWorkspaceId = 'dec-ws-default',
  token
}) => {
  const [workspace, setWorkspace] = useState<DecisionWorkspaceResponse | null>(null);
  const [recommendation, setRecommendation] = useState<GroundedRecommendationResponse | null>(null);
  const [overrideReason, setOverrideReason] = useState<string>('Option A aligns with team operational experience.');
  const [selectedOptionId, setSelectedOptionId] = useState<string>('opt-a');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadWorkspace = async () => {
    setIsLoading(true);
    try {
      const ws = await fetchDecisionWorkspace(initialWorkspaceId, token);
      setWorkspace(ws);
      if (ws.recommendation) setRecommendation(ws.recommendation);
    } catch (err) {
      console.error('Failed to load decision workspace:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadWorkspace();
  }, [initialWorkspaceId, token]);

  const handleAddEvidence = async () => {
    if (!workspace) return;
    try {
      const res = await addDecisionEvidence(
        workspace.workspace_id,
        'doc-auth-v2',
        'DOCUMENT',
        'Authentication Architecture v2',
        'CURRENT',
        'APPROVED',
        'Specifies PostgreSQL 16 session storage with JWT 30m timeout.',
        token
      );
      setWorkspace(res.workspace);
      setActionMessage(res.message);
    } catch (err) {
      console.error('Failed to add evidence:', err);
    }
  };

  const handleGetRecommendation = async () => {
    if (!workspace) return;
    try {
      const rec = await generateDecisionRecommendation(workspace.workspace_id, token);
      setRecommendation(rec);
      setActionMessage(`Evaluated evidence-grounded recommendation for '${rec.recommended_option_title}'.`);
    } catch (err) {
      console.error('Failed recommendation:', err);
    }
  };

  const handleFinalize = async () => {
    if (!workspace) return;
    try {
      const res = await finalizeDecision(
        workspace.workspace_id,
        selectedOptionId,
        selectedOptionId === 'opt-a' ? 'Option A: Keep Current JWT 30m Spec' : 'Option B: Migrate to OAuth 2.0 Provider',
        'Operational simplicity and zero downtime risk.',
        selectedOptionId === 'opt-a' ? overrideReason : undefined,
        token
      );
      setWorkspace(res.workspace);
      setActionMessage(res.message);
    } catch (err) {
      console.error('Failed finalization:', err);
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
                DECISION INTELLIGENCE & HUMAN-IN-THE-LOOP REASONING
              </span>
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center space-x-1">
                <UserCheck className="w-3 h-3" />
                <span>Human Final Authority Preserved</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <Scale className="w-7 h-7 text-indigo-400" />
              <span>Decision Workspace</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Synthesizes authorized evidence, compares alternatives, analyzes trade-offs, and provides grounded recommendations while human authority remains final.
            </p>
          </div>

          {workspace && (
            <div className="flex items-center space-x-2 bg-slate-950 p-2.5 rounded-2xl border border-slate-800 flex-shrink-0">
              <span className="text-[9px] font-mono text-slate-400 uppercase">State:</span>
              <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${
                workspace.readiness_state === 'DECIDED' ? 'bg-emerald-950 text-emerald-400 border-emerald-800/60' : 'bg-amber-950 text-amber-400 border-amber-800/60'
              }`}>
                {workspace.readiness_state}
              </span>
            </div>
          )}
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

      {workspace && (
        <div className="space-y-6">
          
          {/* Decision Question Card */}
          <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-3 backdrop-blur-md">
            <span className="text-[9px] font-mono text-indigo-400 uppercase font-bold">Decision Question</span>
            <h2 className="text-lg font-black text-white">"{workspace.question}"</h2>
            <div className="flex items-center space-x-4 text-xs text-slate-400 pt-1">
              <span>Scope: {workspace.scope}</span>
              <span>•</span>
              <span>Constraints: {workspace.constraints.join(', ')}</span>
            </div>
          </div>

          {/* Evidence Conflicts Banner */}
          {workspace.evidence_conflicts.length > 0 && (
            <div className="bg-amber-950/80 border border-amber-800/60 p-4 rounded-3xl space-y-2">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                <span className="text-xs font-bold text-amber-200 uppercase font-mono">Evidence Conflict Detected</span>
              </div>
              {workspace.evidence_conflicts.map((cnf) => (
                <p key={cnf.conflict_id} className="text-xs text-amber-300 font-medium">• {cnf.description}</p>
              ))}
            </div>
          )}

          {/* Alternatives & Comparison Matrix */}
          <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-xs font-bold text-white uppercase font-mono">Alternatives Comparison Matrix</h3>
              <button
                type="button"
                onClick={() => handleAddEvidence()}
                className="px-3 py-1 bg-slate-950 hover:bg-slate-800 border border-slate-800 rounded-xl text-xs text-slate-300 font-bold"
              >
                + Add Evidence
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-800 text-[10px] font-mono uppercase text-slate-400">
                    <th className="p-3">Option Title</th>
                    <th className="p-3">Security</th>
                    <th className="p-3">Cost</th>
                    <th className="p-3">Complexity</th>
                    <th className="p-3">Timeline</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-200">
                  {workspace.alternatives.map((alt) => (
                    <tr key={alt.alternative_id} className="hover:bg-slate-950/50">
                      <td className="p-3 font-bold text-white">{alt.title}</td>
                      <td className="p-3 font-mono text-emerald-400">{alt.security_score}</td>
                      <td className="p-3 font-mono text-slate-300">{alt.cost}</td>
                      <td className="p-3 font-mono text-slate-300">{alt.complexity}</td>
                      <td className="p-3 font-mono text-slate-300">{alt.timeline}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Evidence-Grounded Recommendation Drawer */}
          <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-xs font-bold text-white uppercase font-mono flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-indigo-400" />
                <span>Evidence-Grounded AI Recommendation</span>
              </h3>

              <button
                type="button"
                onClick={() => handleGetRecommendation()}
                className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-white font-bold text-xs shadow-md"
              >
                Evaluate Recommendation
              </button>
            </div>

            {recommendation && (
              <div className="p-5 bg-slate-950 border border-indigo-800/60 rounded-3xl space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-white">{recommendation.recommended_option_title}</h4>
                  <span className="text-[9px] font-mono text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 font-bold">{recommendation.confidence}</span>
                </div>

                <p className="text-xs text-slate-300">{recommendation.reasoning}</p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                  <div className="p-3 bg-slate-900 border border-slate-800 rounded-2xl text-xs space-y-1">
                    <span className="text-[9px] font-mono text-emerald-400 font-bold uppercase">Supporting Evidence</span>
                    {recommendation.supporting_evidence.map((s, i) => (
                      <p key={i} className="text-[11px] text-slate-300">• {s}</p>
                    ))}
                  </div>

                  <div className="p-3 bg-slate-900 border border-slate-800 rounded-2xl text-xs space-y-1">
                    <span className="text-[9px] font-mono text-amber-400 font-bold uppercase">Counter-Evidence & Limitations</span>
                    {recommendation.counter_evidence.map((c, i) => (
                      <p key={i} className="text-[11px] text-slate-300">• {c}</p>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Human Finalize Decision Controls */}
          {workspace.readiness_state !== 'DECIDED' && (
            <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
              <h3 className="text-xs font-bold text-white uppercase font-mono border-b border-slate-800 pb-3">Human Final Decision & Rationale Recording</h3>
              
              <div className="space-y-3">
                <div className="flex items-center space-x-4 text-xs">
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="radio"
                      name="optSelect"
                      value="opt-a"
                      checked={selectedOptionId === 'opt-a'}
                      onChange={() => setSelectedOptionId('opt-a')}
                      className="accent-indigo-500"
                    />
                    <span className="font-bold text-white">Select Option A (Override AI Recommendation)</span>
                  </label>

                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="radio"
                      name="optSelect"
                      value="opt-b"
                      checked={selectedOptionId === 'opt-b'}
                      onChange={() => setSelectedOptionId('opt-b')}
                      className="accent-indigo-500"
                    />
                    <span className="font-bold text-white">Select Option B (Accept AI Recommendation)</span>
                  </label>
                </div>

                {selectedOptionId === 'opt-a' && (
                  <div>
                    <label className="text-[10px] font-mono text-slate-400 uppercase block mb-1 font-bold">User Override Rationale</label>
                    <input
                      type="text"
                      value={overrideReason}
                      onChange={(e) => setOverrideReason(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-2xl px-3 py-2 text-xs text-white focus:outline-none"
                    />
                  </div>
                )}

                <div className="flex justify-end pt-2">
                  <button
                    type="button"
                    onClick={() => handleFinalize()}
                    className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-2xl text-white font-bold text-xs shadow-lg flex items-center space-x-1.5"
                  >
                    <Check className="w-4 h-4" />
                    <span>Finalize Decision & Publish Governed v2</span>
                  </button>
                </div>
              </div>
            </div>
          )}

        </div>
      )}

    </div>
  );
};
