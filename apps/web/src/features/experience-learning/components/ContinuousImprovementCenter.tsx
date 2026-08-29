import React, { useState, useEffect } from 'react';
import {
  captureExperience, analyzeOutcomeAttribution, fetchLessonsAndPatterns, generatePlaybookAndRetro, manageContinuousImprovement,
  ExperienceRecordResponse, OutcomeAttributionResponse, LessonsPatternsResponse, PlaybookRetroResponse, ImprovementResponse
} from '../experience-learning-api';
import {
  BookOpen, Sparkles, CheckCircle2, AlertOctagon, TrendingUp, Layers, FileText, ArrowRight, ShieldCheck, Activity, RefreshCw
} from 'lucide-react';

interface ContinuousImprovementCenterProps {
  initialProjectId?: string;
  token?: string;
}

export const ContinuousImprovementCenter: React.FC<ContinuousImprovementCenterProps> = ({
  initialProjectId,
  token
}) => {
  const [activeTab, setActiveTab] = useState<'EXPERIENCES_LESSONS' | 'OUTCOMES_ATTRIBUTION' | 'PLAYBOOKS_RETROS' | 'CONTINUOUS_IMPROVEMENT'>('EXPERIENCES_LESSONS');
  const [lessonsRes, setLessonsRes] = useState<LessonsPatternsResponse | null>(null);
  const [playbookRes, setPlaybookRes] = useState<PlaybookRetroResponse | null>(null);
  const [capturedRecord, setCapturedRecord] = useState<ExperienceRecordResponse | null>(null);
  const [outcomeRes, setOutcomeRes] = useState<OutcomeAttributionResponse | null>(null);
  const [improvementRes, setImprovementRes] = useState<ImprovementResponse | null>(null);

  const [expTitleInput, setExpTitleInput] = useState<string>('Auth0 Identity Provider Rollout');
  const [expSituationInput, setExpSituationInput] = useState<string>('Legacy custom token service had 14-day unresolved decision block.');
  const [expActionInput, setExpActionInput] = useState<string>('Adopted Auth0 SaaS SDK and configured 15-min token refresh.');
  const [expOutcomeInput, setExpOutcomeInput] = useState<string>('Achieved SOC2 compliance with 0 milestone delay.');

  const [problemInput, setProblemInput] = useState<string>('Manual microservice Auth setup takes 4 hours.');
  const [proposalInput, setProposalInput] = useState<string>('Automate OAuth setup via standardized Playbook CLI script.');

  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const lp = await fetchLessonsAndPatterns(token);
      setLessonsRes(lp);
      const pr = await generatePlaybookAndRetro(initialProjectId, token);
      setPlaybookRes(pr);
    } catch (err) {
      console.error('Failed to load experience learning center:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [initialProjectId, token]);

  const handleCaptureExperience = async () => {
    setIsLoading(true);
    try {
      const res = await captureExperience(expTitleInput, expSituationInput, expActionInput, expOutcomeInput, initialProjectId, token);
      setCapturedRecord(res);
      setActionMessage(`Experience Record '${res.title}' captured successfully (Status: ${res.validation_status}).`);
    } catch (err) {
      console.error('Capture experience failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnalyzeOutcome = async () => {
    setIsLoading(true);
    try {
      const res = await analyzeOutcomeAttribution('SOC2 compliance with 0 delay', 'SOC2 compliance achieved with 0 delay', initialProjectId, token);
      setOutcomeRes(res);
      setActionMessage(`Outcome Attribution Analyzed: ${res.outcome_classification}`);
    } catch (err) {
      console.error('Outcome attribution failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleManageImprovement = async () => {
    setIsLoading(true);
    try {
      const res = await manageContinuousImprovement(problemInput, proposalInput, token);
      setImprovementRes(res);
      setActionMessage(`Improvement Opportunity '${res.opportunity_id}' logged into backlog (Phase 6.21 plan prepared).`);
    } catch (err) {
      console.error('Improvement management failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6 text-slate-100 font-sans select-none">
      
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-teal-950/80 to-slate-900 border border-teal-800/60 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-teal-400 px-2.5 py-0.5 bg-teal-950 rounded border border-teal-800/60">
                ORGANIZATIONAL MEMORY & CONTINUOUS IMPROVEMENT
              </span>
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center space-x-1">
                <ShieldCheck className="w-3 h-3" />
                <span>Context-Preserved Experience Learning</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <BookOpen className="w-7 h-7 text-teal-400" />
              <span>Continuous Improvement & Memory Center</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Transforms past work, decisions, outcomes, and retrospectives into validated organizational learning that improves future work.
            </p>
          </div>

          {lessonsRes && (
            <div className="flex items-center space-x-4 bg-slate-950 p-3 rounded-2xl border border-slate-800 flex-shrink-0">
              <div className="text-center">
                <span className="text-[10px] font-mono text-slate-400 uppercase font-bold block">Validated Lessons</span>
                <span className="text-lg font-black text-teal-400">{lessonsRes.extracted_lessons.length}</span>
              </div>
              <div className="h-8 w-px bg-slate-800" />
              <div className="text-center">
                <span className="text-[10px] font-mono text-slate-400 uppercase font-bold block">Detected Patterns</span>
                <span className="text-lg font-black text-emerald-400">{lessonsRes.detected_patterns.length}</span>
              </div>
            </div>
          )}
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center space-x-2 bg-slate-950 p-1.5 rounded-2xl border border-slate-800 w-fit">
          <button
            type="button"
            onClick={() => setActiveTab('EXPERIENCES_LESSONS')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
              activeTab === 'EXPERIENCES_LESSONS' ? 'bg-teal-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Experience & Lessons
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('OUTCOMES_ATTRIBUTION')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
              activeTab === 'OUTCOMES_ATTRIBUTION' ? 'bg-teal-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Outcomes & Attribution
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('PLAYBOOKS_RETROS')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
              activeTab === 'PLAYBOOKS_RETROS' ? 'bg-teal-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Playbooks & Retrospectives
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('CONTINUOUS_IMPROVEMENT')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
              activeTab === 'CONTINUOUS_IMPROVEMENT' ? 'bg-teal-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Improvement Backlog
          </button>
        </div>
      </div>

      {actionMessage && (
        <div className="p-3 bg-teal-950/80 border border-teal-800/60 rounded-2xl text-xs text-teal-200 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Activity className="w-4 h-4 text-teal-400" />
            <span>{actionMessage}</span>
          </div>
          <button type="button" onClick={() => setActionMessage(null)} className="text-[10px] text-slate-400 hover:text-white font-mono">Dismiss</button>
        </div>
      )}

      {/* Tab Views */}
      {activeTab === 'EXPERIENCES_LESSONS' && (
        <div className="space-y-6">
          <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
            <h3 className="text-xs font-bold text-white uppercase font-mono border-b border-slate-800 pb-2">Capture New Experience Record</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              <input
                type="text"
                value={expTitleInput}
                onChange={(e) => setExpTitleInput(e.target.value)}
                placeholder="Title..."
                className="bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white focus:outline-none"
              />
              <input
                type="text"
                value={expSituationInput}
                onChange={(e) => setExpSituationInput(e.target.value)}
                placeholder="Situation..."
                className="bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white focus:outline-none"
              />
              <input
                type="text"
                value={expActionInput}
                onChange={(e) => setExpActionInput(e.target.value)}
                placeholder="Action taken..."
                className="bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white focus:outline-none"
              />
              <input
                type="text"
                value={expOutcomeInput}
                onChange={(e) => setExpOutcomeInput(e.target.value)}
                placeholder="Outcome..."
                className="bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white focus:outline-none"
              />
            </div>
            <button
              type="button"
              onClick={handleCaptureExperience}
              disabled={isLoading}
              className="px-4 py-2 bg-teal-600 hover:bg-teal-500 rounded-xl text-white font-bold text-xs"
            >
              Capture Experience
            </button>

            {capturedRecord && (
              <div className="p-3 bg-slate-950 border border-teal-800/60 rounded-2xl text-xs space-y-1">
                <span className="font-bold text-teal-400 block font-mono">Record Captured: {capturedRecord.record_id}</span>
                <p className="text-slate-300">• Lessons Extracted: {capturedRecord.lessons_extracted.join(' | ')}</p>
              </div>
            )}
          </div>

          {lessonsRes && (
            <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
              <h3 className="text-xs font-bold text-white uppercase font-mono border-b border-slate-800 pb-2">Validated Lessons & Success Patterns</h3>
              <div className="space-y-3 text-xs">
                {lessonsRes.extracted_lessons.map(l => (
                  <div key={l.lesson_id} className="p-3 bg-slate-950 border border-slate-800 rounded-2xl space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-[9px] font-mono text-teal-400 bg-teal-950 px-2 py-0.5 rounded border border-teal-800/60 uppercase">{l.lesson_type}</span>
                      <span className="text-[9px] font-mono text-emerald-400 font-bold uppercase">{l.confidence} CONFIDENCE</span>
                    </div>
                    <p className="text-white font-bold mt-1">{l.claim}</p>
                    <p className="text-slate-400 text-[11px]">• Generalization: {l.generalization_level}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'OUTCOMES_ATTRIBUTION' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Expected vs Actual Outcome Attribution</h3>
            <p className="text-xs text-slate-400 mt-1">Evidence-aware contributing factor attribution without simplistic decision credit.</p>
          </div>

          <button
            type="button"
            onClick={handleAnalyzeOutcome}
            disabled={isLoading}
            className="px-4 py-2 bg-teal-600 hover:bg-teal-500 rounded-xl text-white font-bold text-xs"
          >
            Analyze Outcome Attribution
          </button>

          {outcomeRes && (
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-3 text-xs">
              <span className="font-bold text-teal-400 text-sm font-mono block">Outcome Classification: {outcomeRes.outcome_classification}</span>
              <p className="text-slate-300 font-mono">• Expected: {outcomeRes.expected_outcome}</p>
              <p className="text-slate-300 font-mono">• Actual: {outcomeRes.actual_outcome}</p>
              <div className="space-y-1 pt-1">
                <span className="font-bold text-white font-mono block uppercase">Contributing Factors</span>
                {outcomeRes.contributing_factors.map((cf, idx) => (
                  <div key={idx} className="p-2 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-between">
                    <span className="text-slate-200">{cf.factor}</span>
                    <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${
                      cf.impact === 'POSITIVE' ? 'bg-emerald-950 text-emerald-400 border-emerald-800/60' : 'bg-red-950 text-red-400 border-red-800/60'
                    }`}>{cf.impact}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'PLAYBOOKS_RETROS' && playbookRes && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Retrospective Draft & Reusable Playbooks</h3>
            <p className="text-xs text-slate-400 mt-1">Fact/Opinion separation in retrospectives and drift-monitored playbooks.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-3">
              <span className="font-bold text-teal-400 font-mono uppercase block">Retrospective Draft</span>
              <div className="space-y-2">
                <p className="text-slate-300">• <strong>Observed Events:</strong> {playbookRes.retrospective_draft.observed_events.join(', ')}</p>
                <p className="text-slate-300">• <strong>Interpretations:</strong> {playbookRes.retrospective_draft.interpretations.join(', ')}</p>
                <p className="text-slate-400">• <strong>Opinions:</strong> {playbookRes.retrospective_draft.opinions.join(', ')}</p>
              </div>
            </div>

            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-bold text-teal-400 font-mono uppercase block">Playbook Candidate</span>
                <span className="text-[9px] font-mono text-emerald-400 font-bold uppercase bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60">{playbookRes.playbook_candidate.status}</span>
              </div>
              <h4 className="text-white font-bold">{playbookRes.playbook_candidate.title}</h4>
              <p className="text-slate-300">• Steps: {playbookRes.playbook_candidate.recommended_steps.join(' | ')}</p>
              <span className="text-[10px] font-mono text-slate-400 block">• Drift Status: {playbookRes.playbook_candidate.drift_status}</span>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'CONTINUOUS_IMPROVEMENT' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Continuous Improvement Backlog & Measurement</h3>
            <p className="text-xs text-slate-400 mt-1">Log improvement opportunities and track empirical Baseline vs Target vs Actual metrics.</p>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <label className="text-slate-300 font-bold block mb-1">Problem Description:</label>
              <input
                type="text"
                value={problemInput}
                onChange={(e) => setProblemInput(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-2xl p-3 text-white focus:outline-none"
              />
            </div>
            <div>
              <label className="text-slate-300 font-bold block mb-1">Proposed Solution:</label>
              <input
                type="text"
                value={proposalInput}
                onChange={(e) => setProposalInput(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-2xl p-3 text-white focus:outline-none"
              />
            </div>
            <button
              type="button"
              onClick={handleManageImprovement}
              disabled={isLoading}
              className="px-4 py-2 bg-teal-600 hover:bg-teal-500 rounded-xl text-white font-bold text-xs"
            >
              Add to Improvement Backlog
            </button>
          </div>

          {improvementRes && (
            <div className="p-4 bg-slate-950 border border-teal-800/60 rounded-2xl space-y-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-bold text-teal-400 font-mono text-sm">Improvement Logged: {improvementRes.opportunity_id}</span>
                <span className="text-[9px] font-mono text-emerald-400 font-bold uppercase bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60">{improvementRes.classification}</span>
              </div>
              <p className="text-slate-300">• Baseline: {improvementRes.metrics.baseline}</p>
              <p className="text-slate-300">• Target: {improvementRes.metrics.target}</p>
              <p className="text-emerald-400 font-bold">• Actual: {improvementRes.metrics.actual}</p>
            </div>
          )}
        </div>
      )}

    </div>
  );
};
