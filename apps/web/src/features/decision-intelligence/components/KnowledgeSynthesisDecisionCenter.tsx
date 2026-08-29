import React, { useState, useEffect } from 'react';
import {
  synthesizeKnowledge, evaluateDecisionCandidate, compareDecisionOptions, recordDecision,
  SynthesisResponse, CandidateResponse, CompareOptionsResponse, RecordDecisionResponse, ClaimItem
} from '../knowledge-synthesis-decision-api';
import {
  Brain, FileText, CheckCircle2, AlertTriangle, Layers, Scales, ArrowRight, ShieldCheck, Activity, Award, HelpCircle
} from 'lucide-react';

interface KnowledgeSynthesisDecisionCenterProps {
  initialProjectId?: string;
  token?: string;
}

export const KnowledgeSynthesisDecisionCenter: React.FC<KnowledgeSynthesisDecisionCenterProps> = ({
  initialProjectId,
  token
}) => {
  const [activeTab, setActiveTab] = useState<'EVIDENCE_SYNTHESIS' | 'DECISION_READINESS' | 'OPTION_MATRIX' | 'DECISION_REGISTER'>('EVIDENCE_SYNTHESIS');
  const [synthesisRes, setSynthesisRes] = useState<SynthesisResponse | null>(null);
  const [candidateRes, setCandidateRes] = useState<CandidateResponse | null>(null);
  const [compareRes, setCompareRes] = useState<CompareOptionsResponse | null>(null);
  const [recordRes, setRecordRes] = useState<RecordDecisionResponse | null>(null);

  const [decisionQuestionInput, setDecisionQuestionInput] = useState<string>('Should Project Alpha migrate to OAuth 2.0 before release?');
  const [rationaleInput, setRationaleInput] = useState<string>('Approved Option A to ensure SOC2 compliance without delaying release schedule.');
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const syn = await synthesizeKnowledge(initialProjectId, token);
      setSynthesisRes(syn);
      const cand = await evaluateDecisionCandidate('OAuth 2.0 Migration Strategy', initialProjectId, token);
      setCandidateRes(cand);
    } catch (err) {
      console.error('Failed to load decision intelligence center:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [initialProjectId, token]);

  const handleCompareOptions = async () => {
    if (!candidateRes) return;
    setIsLoading(true);
    try {
      const res = await compareDecisionOptions(candidateRes.candidate_id, [], token);
      setCompareRes(res);
      setActionMessage(`Multi-Option Comparison Completed: Recommended Option '${res.recommended_option}'`);
    } catch (err) {
      console.error('Option comparison failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRecordDecision = async () => {
    if (!compareRes) return;
    setIsLoading(true);
    try {
      const res = await recordDecision(decisionQuestionInput, compareRes.recommended_option, rationaleInput, undefined, token);
      setRecordRes(res);
      setActionMessage(`Decision Recorded Successfully (ID: ${res.decision_id}, Version: v${res.version}). Draft briefs generated.`);
    } catch (err) {
      console.error('Record decision failed:', err);
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
                KNOWLEDGE SYNTHESIS & DECISION INTELLIGENCE
              </span>
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center space-x-1">
                <ShieldCheck className="w-3 h-3" />
                <span>Human Decision Governance</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <Brain className="w-7 h-7 text-indigo-400" />
              <span>Decision Support & Synthesis Center</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Combines multi-source evidence, evaluates trade-offs, surfaces contradictions, and records immutable decision rationale.
            </p>
          </div>

          {synthesisRes && (
            <div className="flex items-center space-x-4 bg-slate-950 p-3 rounded-2xl border border-slate-800 flex-shrink-0">
              <div className="text-center">
                <span className="text-[10px] font-mono text-slate-400 uppercase font-bold block">Synthesized Claims</span>
                <span className="text-lg font-black text-indigo-400">{synthesisRes.total_claims}</span>
              </div>
              <div className="h-8 w-px bg-slate-800" />
              <div className="text-center">
                <span className="text-[10px] font-mono text-slate-400 uppercase font-bold block">Conflicts Surfaced</span>
                <span className="text-lg font-black text-amber-400">{synthesisRes.conflicts_surfaced}</span>
              </div>
            </div>
          )}
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center space-x-2 bg-slate-950 p-1.5 rounded-2xl border border-slate-800 w-fit">
          <button
            type="button"
            onClick={() => setActiveTab('EVIDENCE_SYNTHESIS')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
              activeTab === 'EVIDENCE_SYNTHESIS' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Evidence Synthesis
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('DECISION_READINESS')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
              activeTab === 'DECISION_READINESS' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Decision Readiness
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('OPTION_MATRIX')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
              activeTab === 'OPTION_MATRIX' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Option & Trade-Off Matrix
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('DECISION_REGISTER')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
              activeTab === 'DECISION_REGISTER' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Decision Register & Briefs
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

      {/* Tab Views */}
      {activeTab === 'EVIDENCE_SYNTHESIS' && synthesisRes && (
        <div className="space-y-4">
          {synthesisRes.evidence_bundle.map((c: ClaimItem) => (
            <div key={c.claim_id} className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center space-x-2">
                  <span className="text-[9px] font-mono font-bold text-indigo-400 bg-indigo-950 px-2 py-0.5 rounded border border-indigo-800/60 uppercase">{c.claim_type}</span>
                  <span className="text-[9px] font-mono text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 font-bold uppercase">{c.confidence} CONFIDENCE</span>
                </div>
                {c.conflict_detected && (
                  <span className="text-[9px] font-mono text-amber-400 bg-amber-950 px-2 py-0.5 rounded border border-amber-800/60 font-bold flex items-center space-x-1">
                    <AlertTriangle className="w-3 h-3" />
                    <span>Source Conflict Surfaced</span>
                  </span>
                )}
              </div>

              <div>
                <h3 className="text-sm font-bold text-white leading-relaxed">{c.claim_text}</h3>
                <div className="mt-2 space-y-1 text-xs text-slate-300">
                  <p>• Supporting Sources: <strong>{c.supporting_sources.join(', ')}</strong></p>
                  {c.contradicting_sources.length > 0 && (
                    <p className="text-amber-300">• Contradicting Sources: <strong>{c.contradicting_sources.join(', ')}</strong></p>
                  )}
                </div>
              </div>

              {c.conflict_detected && c.conflict_explanation && (
                <div className="p-3 bg-amber-950/80 border border-amber-800/60 rounded-2xl text-xs text-amber-200">
                  <strong>Conflict Explanation:</strong> {c.conflict_explanation}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {activeTab === 'DECISION_READINESS' && candidateRes && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-white uppercase font-mono">Decision Candidate Evaluation</h3>
              <p className="text-xs text-slate-400 mt-1">{candidateRes.decision_question}</p>
            </div>
            <span className="text-xs font-mono font-bold text-amber-400 bg-amber-950 px-3 py-1 rounded-xl border border-amber-800/60 uppercase">
              Status: {candidateRes.readiness_status}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2">
              <span className="font-bold text-white font-mono uppercase block">Hard Constraints</span>
              {candidateRes.constraints.hard_constraints.map((hc, idx) => (
                <div key={idx} className="p-2 bg-slate-900 border border-slate-800 rounded-xl text-slate-200">• {hc}</div>
              ))}
            </div>

            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2">
              <span className="font-bold text-white font-mono uppercase block">Missing Evidence Gaps</span>
              {candidateRes.evidence_gaps.map((eg) => (
                <div key={eg.gap_id} className="p-2 bg-slate-900 border border-slate-800 rounded-xl text-amber-300">
                  • <strong>{eg.missing_information}</strong> ({eg.why_it_matters})
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'OPTION_MATRIX' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Multi-Option Feasibility & Trade-Off Matrix</h3>
            <p className="text-xs text-slate-400 mt-1">Weighted decision criteria comparison and sensitivity stability analysis.</p>
          </div>

          <button
            type="button"
            onClick={handleCompareOptions}
            disabled={isLoading}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-white font-bold text-xs"
          >
            Compare Options & Run Sensitivity
          </button>

          {compareRes && (
            <div className="space-y-4">
              <div className="space-y-3">
                {compareRes.evaluated_options.map(opt => (
                  <div key={opt.option_id} className={`p-4 bg-slate-950 border rounded-2xl space-y-2 text-xs ${
                    opt.feasibility === 'INFEASIBLE' ? 'border-red-800/60 opacity-60' : 'border-slate-800'
                  }`}>
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-white text-sm">{opt.option_name}</span>
                      <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${
                        opt.feasibility === 'FEASIBLE' ? 'bg-emerald-950 text-emerald-400 border-emerald-800/60' : 'bg-red-950 text-red-400 border-red-800/60'
                      }`}>
                        {opt.feasibility}
                      </span>
                    </div>
                    {opt.feasibility_reason && <p className="text-red-400 font-mono text-[10px]">• {opt.feasibility_reason}</p>}
                    <p className="text-slate-300">• Trade-off: {opt.tradeoff_summary}</p>
                    <p className="text-indigo-300 font-mono">• Score: {opt.weighted_score}/10</p>
                  </div>
                ))}
              </div>

              <div className="p-4 bg-slate-950 border border-indigo-800/60 rounded-2xl space-y-2 text-xs">
                <span className="font-bold text-indigo-400 block font-mono text-sm">Sensitivity Stability Analysis</span>
                <p className="text-slate-300">• Test Case: {compareRes.sensitivity_analysis.test_case}</p>
                <p className="text-slate-300">• Stability: <strong className="text-emerald-400">{compareRes.sensitivity_analysis.stability}</strong></p>
                <p className="text-slate-400 text-[11px]">• Reasoning: {compareRes.sensitivity_analysis.explanation}</p>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'DECISION_REGISTER' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Record Decision & Generate Briefs</h3>
            <p className="text-xs text-slate-400 mt-1">Preserve immutable decision rationale and generate Executive & Technical Brief drafts.</p>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <label className="text-slate-300 font-bold block mb-1">Decision Question:</label>
              <input
                type="text"
                value={decisionQuestionInput}
                onChange={(e) => setDecisionQuestionInput(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-2xl p-3 text-white focus:outline-none"
              />
            </div>
            <div>
              <label className="text-slate-300 font-bold block mb-1">Rationale:</label>
              <textarea
                rows={2}
                value={rationaleInput}
                onChange={(e) => setRationaleInput(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-2xl p-3 text-white focus:outline-none"
              />
            </div>
            <button
              type="button"
              onClick={handleRecordDecision}
              disabled={isLoading || !compareRes}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-white font-bold text-xs"
            >
              Record Decision & Generate Briefs
            </button>
          </div>

          {recordRes && (
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-3 text-xs">
              <span className="font-bold text-emerald-400 font-mono text-sm block">Decision Recorded (ID: {recordRes.decision_id}, Version: v{recordRes.version})</span>
              <div className="space-y-2">
                <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl">
                  <span className="font-bold text-white font-mono block">Executive Brief Draft</span>
                  <p className="text-slate-300 mt-1">{recordRes.decision_brief_drafts.executive_brief}</p>
                </div>
                <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl">
                  <span className="font-bold text-white font-mono block">Technical Brief Draft</span>
                  <p className="text-slate-300 mt-1">{recordRes.decision_brief_drafts.technical_brief}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

    </div>
  );
};
