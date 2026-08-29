import React, { useState, useEffect } from 'react';
import {
  fetchEarlyWarnings, fetchDecisionImpact, performWhatIfAnalysis, fetchProjectReadiness, generateDecisionBrief, rebuildPredictions,
  EarlyWarningItem, DecisionImpactResponse, WhatIfResponse, ProjectReadinessResponse, DecisionBriefResponse
} from '../predictive-intelligence-api';
import {
  TrendingUp, AlertTriangle, GitPullRequest, HelpCircle, ShieldCheck, RefreshCw, FileText, Sparkles, ArrowRight, CornerDownRight, CheckCircle2, XCircle
} from 'lucide-react';

interface PredictiveIntelligenceDashboardProps {
  initialProjectId?: string;
  token?: string;
}

export const PredictiveIntelligenceDashboard: React.FC<PredictiveIntelligenceDashboardProps> = ({
  initialProjectId = '79ecf444-2d27-4968-a038-28ce7897be44',
  token
}) => {
  const [warnings, setWarnings] = useState<EarlyWarningItem[]>([]);
  const [impact, setImpact] = useState<DecisionImpactResponse | null>(null);
  const [whatIfScenario, setWhatIfScenario] = useState<string>('What if deployment remains blocked?');
  const [whatIfResult, setWhatIfResult] = useState<WhatIfResponse | null>(null);
  const [readiness, setReadiness] = useState<ProjectReadinessResponse | null>(null);
  const [briefTopic, setBriefTopic] = useState<string>('Database Storage Selection');
  const [decisionBrief, setDecisionBrief] = useState<DecisionBriefResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [wRes, iRes, rRes] = await Promise.all([
        fetchEarlyWarnings(initialProjectId, token).catch(() => []),
        fetchDecisionImpact('70f1236a-7280-4167-8ed3-22bbb857509c', token).catch(() => null),
        fetchProjectReadiness(initialProjectId, token).catch(() => null)
      ]);
      setWarnings(wRes);
      if (iRes) setImpact(iRes);
      if (rRes) setReadiness(rRes);
    } catch (err) {
      console.error('Failed to load predictive intelligence data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [initialProjectId, token]);

  const handleRunWhatIf = async () => {
    if (!whatIfScenario) return;
    try {
      const res = await performWhatIfAnalysis(whatIfScenario, initialProjectId, token);
      setWhatIfResult(res);
    } catch (err) {
      console.error('Failed what-if analysis:', err);
    }
  };

  const handleGenerateBrief = async () => {
    if (!briefTopic) return;
    try {
      const res = await generateDecisionBrief(briefTopic, token);
      setDecisionBrief(res);
    } catch (err) {
      console.error('Failed decision brief generation:', err);
    }
  };

  const handleRebuild = async () => {
    try {
      await rebuildPredictions(token);
      loadData();
    } catch (err) {
      console.error('Failed to rebuild predictions:', err);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6 text-slate-100 font-sans select-none">
      
      {/* Flagship Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/80 to-slate-900 border border-indigo-800/60 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-indigo-400 px-2.5 py-0.5 bg-indigo-950 rounded border border-indigo-800/60">
                PREDICTIVE PROJECT INTELLIGENCE & DECISION SUPPORT
              </span>
              <span className="text-[10px] font-mono font-bold text-amber-400 bg-amber-950 px-2 py-0.5 rounded border border-amber-800/60 flex items-center space-x-1">
                <AlertTriangle className="w-3 h-3" />
                <span>Evidence-Backed Forecasts Only</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <TrendingUp className="w-7 h-7 text-indigo-400" />
              <span>Predictive Decision Support Engine</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Anticipate project risks, forecast decision downstream impact, model what-if scenarios, and generate source-backed decision briefs.
            </p>
          </div>

          <button
            type="button"
            onClick={handleRebuild}
            className="px-4 py-2 rounded-2xl bg-slate-800 hover:bg-slate-700 text-indigo-400 font-bold text-xs shadow-md transition-all flex items-center space-x-1.5 flex-shrink-0"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Rebuild Predictions</span>
          </button>
        </div>
      </div>

      {/* Main Split Layout */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Left 2 Cols: Early Warning Alerts & Decision Impact Tracing */}
        <div className="md:col-span-2 space-y-5">
          
          {/* Early Warning Cards */}
          <div className="bg-slate-900/80 border border-indigo-800/60 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-xs font-bold text-white flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                <span>Early Warning Prediction Signals ({warnings.length})</span>
              </h3>
              <span className="text-[9px] font-mono text-slate-500">Evidence-Backed</span>
            </div>

            <div className="space-y-4">
              {warnings.map((w) => (
                <div
                  key={w.prediction_id}
                  className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2.5"
                >
                  <div className="flex items-center justify-between">
                    <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded uppercase ${
                      w.severity === 'CRITICAL'
                        ? 'bg-rose-950 text-rose-400 border border-rose-800/60'
                        : 'bg-amber-950 text-amber-400 border border-amber-800/60'
                    }`}>
                      {w.severity}: {w.type}
                    </span>
                  </div>

                  <h4 className="font-bold text-xs text-white">{w.title}</h4>
                  <p className="text-[11px] text-slate-300">{w.reason}</p>

                  <div className="p-2.5 bg-slate-900/90 rounded-xl border border-slate-800/80 space-y-1 text-[10px] font-mono text-slate-400">
                    <span className="text-indigo-400 font-bold block">Evidence Citations:</span>
                    {w.evidence.map((ev, i) => (
                      <div key={i}>• {ev}</div>
                    ))}
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t border-slate-800 text-[10px] font-mono">
                    <span className="text-slate-500">Affected: {w.affected_entities.join(', ')}</span>
                    <button
                      type="button"
                      className="text-indigo-400 hover:text-white font-bold bg-slate-900 px-2 py-0.5 rounded border border-slate-800"
                    >
                      {w.suggested_next_step}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Decision Impact Downstream Tracing */}
          {impact && (
            <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-3xl shadow-xl space-y-3 backdrop-blur-md">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <h4 className="text-xs font-bold text-white flex items-center space-x-2">
                  <GitPullRequest className="w-4 h-4 text-indigo-400" />
                  <span>Decision Downstream Impact Path: {impact.decision_title}</span>
                </h4>
              </div>

              <div className="space-y-2 text-xs">
                <span className="text-[9px] font-mono font-bold text-indigo-400 uppercase">Direct Impact Entities</span>
                {impact.direct_impact.map((di, idx) => (
                  <div key={idx} className="p-2 bg-slate-950 border border-slate-800 rounded-xl flex items-center justify-between text-[11px]">
                    <span className="font-bold text-slate-200">{di.type}: {di.name}</span>
                    <span className="text-slate-400 text-[10px]">{di.impact_summary}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* What-If Scenario Analysis */}
          <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-3xl shadow-xl space-y-3 backdrop-blur-md">
            <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
              <HelpCircle className="w-4 h-4 text-indigo-400" />
              <h4 className="text-xs font-bold text-white">What-If Scenario Simulator</h4>
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="text"
                value={whatIfScenario}
                onChange={(e) => setWhatIfScenario(e.target.value)}
                placeholder="Enter scenario (e.g. 'What if deployment remains blocked?')"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none"
              />
              <button
                type="button"
                onClick={handleRunWhatIf}
                className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-white font-bold text-xs flex-shrink-0"
              >
                Simulate
              </button>
            </div>

            {whatIfResult && (
              <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-2 text-xs">
                <div>
                  <span className="text-[9px] font-mono font-bold text-indigo-400 uppercase">Known Impacts</span>
                  {whatIfResult.known_impacts.map((k, i) => (
                    <p key={i} className="text-[11px] text-slate-300">• {k}</p>
                  ))}
                </div>
                <div>
                  <span className="text-[9px] font-mono font-bold text-amber-400 uppercase">Explicit Unknowns</span>
                  {whatIfResult.unknowns.map((u, i) => (
                    <p key={i} className="text-[10px] text-slate-400">• {u}</p>
                  ))}
                </div>
              </div>
            )}
          </div>

        </div>

        {/* Right Col: Project Release Readiness & Decision Brief Generator */}
        <div className="space-y-4">
          
          {/* Project Release Readiness Checklist */}
          {readiness && (
            <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-3xl shadow-xl space-y-3 backdrop-blur-md">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <h4 className="text-xs font-bold text-white flex items-center space-x-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span>Release Readiness: {readiness.project_name}</span>
                </h4>
                <span className="text-[9px] font-mono font-bold text-amber-400 uppercase">{readiness.overall_readiness}</span>
              </div>

              <div className="space-y-2 text-xs">
                <div className="p-2 bg-slate-950 border border-slate-800 rounded-xl space-y-1">
                  <span className="text-[9px] font-mono font-bold text-rose-400 uppercase">Blockers ({readiness.categories.blockers.length})</span>
                  {readiness.categories.blockers.map((b, i) => (
                    <div key={i} className="text-slate-300 text-[10px]">🚨 {b.title}</div>
                  ))}
                </div>

                <div className="p-2 bg-slate-950 border border-slate-800 rounded-xl space-y-1">
                  <span className="text-[9px] font-mono font-bold text-indigo-400 uppercase">Open Questions ({readiness.categories.open_questions.length})</span>
                  {readiness.categories.open_questions.map((q, i) => (
                    <div key={i} className="text-slate-300 text-[10px]">❓ {q.title}</div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Decision Brief Generator */}
          <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-3xl shadow-xl space-y-3 backdrop-blur-md">
            <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
              <FileText className="w-4 h-4 text-indigo-400" />
              <h4 className="text-xs font-bold text-white">Decision Brief Generator</h4>
            </div>

            <div className="flex items-center space-x-1.5">
              <input
                type="text"
                value={briefTopic}
                onChange={(e) => setBriefTopic(e.target.value)}
                placeholder="Topic (e.g. Database Storage Selection)"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none"
              />
              <button
                type="button"
                onClick={handleGenerateBrief}
                className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-white font-bold text-xs flex-shrink-0"
              >
                Brief
              </button>
            </div>

            {decisionBrief && (
              <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-2 text-xs">
                <h5 className="font-bold text-slate-100 text-[11px]">{decisionBrief.topic}</h5>
                <p className="text-[10px] text-slate-400">{decisionBrief.context}</p>
                <div className="space-y-1 font-mono text-[9px]">
                  {decisionBrief.option_matrix.map((op, i) => (
                    <div key={i} className="p-1.5 bg-slate-900 rounded border border-slate-800">
                      <span className="text-indigo-400 font-bold block">{op.option}</span>
                      <span className="text-slate-300">Benefits: {op.benefits.join(', ')}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

        </div>

      </div>

    </div>
  );
};
