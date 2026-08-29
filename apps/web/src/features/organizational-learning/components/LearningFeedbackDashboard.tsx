import React, { useState, useEffect } from 'react';
import {
  submitFeedback, proposeCorrection, approveCorrection, fetchKnowledgeGaps, fetchQuestionClusters, fetchPlaybooks, createPlaybook, fetchLearningAnalytics,
  KnowledgeGapItem, QuestionClusterItem, PlaybookItem, LearningAnalyticsResponse, CorrectionProposal
} from '../organizational-learning-api';
import {
  BrainCircuit, ThumbsUp, ThumbsDown, Edit3, BookOpen, AlertCircle, HelpCircle, ShieldCheck, CheckCircle2, Check, RefreshCw, Sparkles, Plus, ArrowRight, Layers
} from 'lucide-react';

interface LearningFeedbackDashboardProps {
  token?: string;
}

export const LearningFeedbackDashboard: React.FC<LearningFeedbackDashboardProps> = ({ token }) => {
  const [activeTab, setActiveTab] = useState<'GAPS' | 'QUESTION_CLUSTERS' | 'PLAYBOOKS' | 'CORRECTIONS'>('GAPS');
  const [gaps, setGaps] = useState<KnowledgeGapItem[]>([]);
  const [questionClusters, setQuestionClusters] = useState<QuestionClusterItem[]>([]);
  const [playbooks, setPlaybooks] = useState<PlaybookItem[]>([]);
  const [analytics, setAnalytics] = useState<LearningAnalyticsResponse | null>(null);

  const [proposedContent, setProposedContent] = useState<string>('Auth Arch v2: JWT Expiry updated to 30 minutes.');
  const [correctionReason, setCorrectionReason] = useState<string>('Decision #D-102 changed JWT expiry from 15m to 30m.');
  const [activeCorrection, setActiveCorrection] = useState<CorrectionProposal | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [gapRes, qcRes, pbRes, anaRes] = await Promise.all([
        fetchKnowledgeGaps(token),
        fetchQuestionClusters(token),
        fetchPlaybooks(token),
        fetchLearningAnalytics(token)
      ]);
      setGaps(gapRes);
      setQuestionClusters(qcRes);
      setPlaybooks(pbRes);
      setAnalytics(anaRes);
    } catch (err) {
      console.error('Failed to load learning dashboard:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [token]);

  const handleSubmitFeedback = async (id: string, rating: string) => {
    try {
      const res = await submitFeedback(id, 'DOCUMENT', 'EXPLICIT', rating, 'User feedback from dashboard', token);
      setActionMessage(res.message);
      loadData();
    } catch (err) {
      console.error('Failed feedback submission:', err);
    }
  };

  const handleProposeCorrection = async () => {
    if (!proposedContent.trim()) return;
    try {
      const res = await proposeCorrection('doc-auth-v1', proposedContent, correctionReason, token);
      setActiveCorrection(res.correction);
      setActionMessage(res.message);
      loadData();
    } catch (err) {
      console.error('Failed correction proposal:', err);
    }
  };

  const handleApproveCorrection = async (correctionId: string) => {
    try {
      const res = await approveCorrection(correctionId, token);
      setActionMessage(res.message);
      loadData();
    } catch (err) {
      console.error('Failed correction approval:', err);
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
                ORGANIZATIONAL LEARNING & ADAPTIVE INTELLIGENCE
              </span>
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center space-x-1">
                <ShieldCheck className="w-3 h-3" />
                <span>Human-in-the-Loop Feedback & Governance</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <BrainCircuit className="w-7 h-7 text-indigo-400" />
              <span>Learning & Feedback Dashboard</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Learns from user feedback, corrections, and recurring questions without silently modifying authoritative governed truth.
            </p>
          </div>

          {/* Navigation Mode Tabs */}
          <div className="flex items-center space-x-2 bg-slate-950 p-1.5 rounded-2xl border border-slate-800 flex-shrink-0">
            <button
              type="button"
              onClick={() => setActiveTab('GAPS')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'GAPS' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Knowledge Gaps
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('QUESTION_CLUSTERS')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'QUESTION_CLUSTERS' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Question Clusters
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('PLAYBOOKS')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'PLAYBOOKS' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Playbooks
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('CORRECTIONS')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'CORRECTIONS' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Corrections
            </button>
          </div>
        </div>

        {/* Analytics Counters Bar */}
        {analytics && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 border-t border-slate-800/60">
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Helpful Rate</span>
              <span className="text-lg font-black text-emerald-400">{analytics.helpful_rate}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Corrections</span>
              <span className="text-lg font-black text-indigo-400">{analytics.correction_proposals_count}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Knowledge Gaps</span>
              <span className="text-lg font-black text-amber-400">{analytics.active_knowledge_gaps}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Playbooks</span>
              <span className="text-lg font-black text-white">{analytics.governed_playbooks_count}</span>
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
      {activeTab === 'GAPS' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
          <h3 className="text-xs font-bold text-white uppercase font-mono border-b border-slate-800 pb-3 flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-amber-400" />
            <span>Detected Zero-Result Searches & Knowledge Gaps</span>
          </h3>

          <div className="space-y-3">
            {gaps.map((gap) => (
              <div key={gap.gap_id} className="p-4 bg-slate-950 border border-slate-800 rounded-2xl flex items-center justify-between text-xs">
                <div>
                  <span className="text-[8px] font-mono font-bold text-amber-400 bg-amber-950 px-1.5 py-0.5 rounded uppercase">{gap.priority} PRIORITY</span>
                  <h4 className="font-bold text-white mt-1">"{gap.query}"</h4>
                  <p className="text-[10px] text-slate-400">Context: {gap.project_context} • Searched {gap.occurrences} times</p>
                  <p className="text-[10px] text-indigo-400 mt-0.5">Recommendation: {gap.recommended_action}</p>
                </div>
                <button
                  type="button"
                  onClick={() => handleSubmitFeedback('gap-pg-pooling', 'OUTDATED')}
                  className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-white font-bold text-xs"
                >
                  Create Document
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'QUESTION_CLUSTERS' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
          <h3 className="text-xs font-bold text-white uppercase font-mono border-b border-slate-800 pb-3 flex items-center space-x-2">
            <HelpCircle className="w-4 h-4 text-indigo-400" />
            <span>Recurring Question Clusters</span>
          </h3>

          <div className="space-y-4">
            {questionClusters.map((qc) => (
              <div key={qc.cluster_id} className="p-5 bg-slate-950 border border-indigo-800/60 rounded-3xl space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-white">{qc.topic}</h4>
                  <span className="text-[9px] font-mono text-indigo-400 bg-slate-900 px-2 py-0.5 rounded">{qc.question_count} questions</span>
                </div>

                <div className="space-y-1.5">
                  <span className="text-[9px] font-mono text-slate-500 uppercase block">Sample Similar Queries</span>
                  {qc.sample_questions.map((q, i) => (
                    <p key={i} className="text-xs text-slate-300">• "{q}"</p>
                  ))}
                </div>

                <div className="p-2.5 bg-slate-900 border border-slate-800 rounded-xl text-xs flex items-center justify-between">
                  <span className="text-[10px] text-slate-400">Matched Governed Decision:</span>
                  <span className="font-bold text-emerald-400">{qc.matched_decision}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'PLAYBOOKS' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
          <h3 className="text-xs font-bold text-white uppercase font-mono border-b border-slate-800 pb-3 flex items-center space-x-2">
            <BookOpen className="w-4 h-4 text-emerald-400" />
            <span>Governed Organizational Playbooks</span>
          </h3>

          <div className="space-y-4">
            {playbooks.map((pb) => (
              <div key={pb.playbook_id} className="p-5 bg-slate-950 border border-slate-800 rounded-3xl space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-[8px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 uppercase">{pb.governance_status}</span>
                    <h4 className="text-sm font-bold text-white mt-1">{pb.title} ({pb.version})</h4>
                  </div>
                  <span className="text-[10px] font-mono text-slate-400">Owner: {pb.owner}</span>
                </div>

                <div className="space-y-1.5 pt-2">
                  <span className="text-[9px] font-mono text-indigo-400 uppercase block font-bold">Governed Execution Steps</span>
                  {pb.steps.map((st, i) => (
                    <div key={i} className="p-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-200 flex items-center space-x-2">
                      <span className="text-indigo-400 font-mono font-bold">{i + 1}.</span>
                      <span>{st}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'CORRECTIONS' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Propose Content Correction (Human-in-the-Loop)</h3>
            <p className="text-xs text-slate-400 mt-1">Submit proposed knowledge corrections entering Phase 6.0 governance review without silently overwriting authoritative truth.</p>
          </div>

          <div className="space-y-4">
            <div>
              <label className="text-[10px] font-mono text-slate-400 uppercase block mb-1 font-bold">Proposed Content</label>
              <textarea
                value={proposedContent}
                onChange={(e) => setProposedContent(e.target.value)}
                rows={3}
                className="w-full bg-slate-950 border border-slate-800 rounded-2xl p-3 text-xs text-white focus:outline-none"
              />
            </div>

            <div>
              <label className="text-[10px] font-mono text-slate-400 uppercase block mb-1 font-bold">Reason for Correction</label>
              <input
                type="text"
                value={correctionReason}
                onChange={(e) => setCorrectionReason(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-2xl px-3 py-2 text-xs text-white focus:outline-none"
              />
            </div>

            <button
              type="button"
              onClick={() => handleProposeCorrection()}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-2xl text-white font-bold text-xs shadow-lg flex items-center space-x-1.5"
            >
              <Edit3 className="w-4 h-4" />
              <span>Submit Proposed Correction</span>
            </button>
          </div>

          {activeCorrection && (
            <div className="p-4 bg-slate-950 border border-indigo-800/60 rounded-2xl space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-[9px] font-mono text-amber-400 bg-amber-950 px-2 py-0.5 rounded border border-amber-800/60 uppercase">Status: {activeCorrection.status}</span>
                <span className="text-[9px] font-mono text-slate-500">{activeCorrection.correction_id}</span>
              </div>

              <p className="text-xs text-slate-300 font-medium">Proposed: "{activeCorrection.proposed_content}"</p>

              <div className="flex justify-end pt-2">
                <button
                  type="button"
                  onClick={() => handleApproveCorrection(activeCorrection.correction_id)}
                  className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 rounded-xl text-white font-bold text-xs flex items-center space-x-1"
                >
                  <Check className="w-3 h-3" />
                  <span>Approve & Publish Governed v2</span>
                </button>
              </div>
            </div>
          )}
        </div>
      )}

    </div>
  );
};
