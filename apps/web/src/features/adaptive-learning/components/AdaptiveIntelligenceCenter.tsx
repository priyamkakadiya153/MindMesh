import React, { useState, useEffect } from 'react';
import {
  fetchReviewQueue, submitReviewAction, revalidateDocument, fetchDownstreamImpact,
  fetchShadowAutomation, promoteAutomationRule, fetchAdaptiveDashboard,
  ReviewQueueResponse, DownstreamImpactResponse, ShadowAutomationResponse, AdaptiveDashboardResponse
} from '../adaptive-learning-api';
import {
  Brain, ShieldCheck, CheckCircle2, XCircle, RefreshCw, GitBranch, Play, RotateCcw, Activity, Layers, ArrowRight, Eye
} from 'lucide-react';

interface AdaptiveIntelligenceCenterProps {
  initialKnowledgeId?: string;
  token?: string;
}

export const AdaptiveIntelligenceCenter: React.FC<AdaptiveIntelligenceCenterProps> = ({
  initialKnowledgeId = 'kn-301',
  token
}) => {
  const [activeTab, setActiveTab] = useState<'REVIEW_QUEUE' | 'REVALIDATION' | 'SHADOW_AUTO' | 'TELEMETRY'>('REVIEW_QUEUE');
  const [queue, setQueue] = useState<ReviewQueueResponse | null>(null);
  const [dashboard, setDashboard] = useState<AdaptiveDashboardResponse | null>(null);
  const [impact, setImpact] = useState<DownstreamImpactResponse | null>(null);
  const [shadowAuto, setShadowAuto] = useState<ShadowAutomationResponse | null>(null);

  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [queueRes, dashRes, impactRes, shadowRes] = await Promise.all([
        fetchReviewQueue(token),
        fetchAdaptiveDashboard(token),
        fetchDownstreamImpact(initialKnowledgeId, token),
        fetchShadowAutomation('Auto-Tag OAuth Security Tasks', token)
      ]);
      setQueue(queueRes);
      setDashboard(dashRes);
      setImpact(impactRes);
      setShadowAuto(shadowRes);
    } catch (err) {
      console.error('Failed to load adaptive intelligence center:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [token, initialKnowledgeId]);

  const handleReviewAction = async (itemId: string, action: string) => {
    try {
      const res = await submitReviewAction(itemId, action, token);
      setActionMessage(`Signal '${itemId}' reviewed with action '${action}'.`);
      loadData();
    } catch (err) {
      console.error('Review action failed:', err);
    }
  };

  const handlePromoteAutomation = async (ruleName: string) => {
    try {
      const res = await promoteAutomationRule(ruleName, token);
      setActionMessage(res.message);
      loadData();
    } catch (err) {
      console.error('Promotion failed:', err);
    }
  };

  const handleRevalidateDoc = async () => {
    try {
      const res = await revalidateDocument('doc-501', token);
      setActionMessage(res.message);
      loadData();
    } catch (err) {
      console.error('Revalidation failed:', err);
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
                KNOWLEDGE AUTOMATION & ADAPTIVE INTELLIGENCE
              </span>
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center space-x-1">
                <Brain className="w-3 h-3" />
                <span>Human-in-the-Loop & Shadow Mode Guardrails</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <Brain className="w-7 h-7 text-teal-400" />
              <span>Adaptive Intelligence & Safe Automation Center</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Continuous learning from validated signals, human corrections, knowledge revalidation, shadow automations, and drift protection.
            </p>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center space-x-2 bg-slate-950 p-1.5 rounded-2xl border border-slate-800 flex-shrink-0">
            <button
              type="button"
              onClick={() => setActiveTab('REVIEW_QUEUE')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'REVIEW_QUEUE' ? 'bg-teal-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Review Queue
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('REVALIDATION')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'REVALIDATION' ? 'bg-teal-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Revalidation
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('SHADOW_AUTO')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'SHADOW_AUTO' ? 'bg-teal-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Shadow Automations
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('TELEMETRY')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'TELEMETRY' ? 'bg-teal-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Adaptive Telemetry
            </button>
          </div>
        </div>

        {/* Telemetry Metrics Bar */}
        {dashboard && queue && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 border-t border-slate-800/60">
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Pending Signals</span>
              <span className="text-lg font-black text-amber-400">{queue.pending_items.length}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Signal Accuracy</span>
              <span className="text-lg font-black text-emerald-400">{dashboard.signal_quality_metrics.signal_accuracy}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Shadow Automations</span>
              <span className="text-lg font-black text-teal-400">{dashboard.shadow_automations_count}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Drift Status</span>
              <span className="text-lg font-black text-cyan-400">{dashboard.drift_detection.concept_drift_status}</span>
            </div>
          </div>
        )}
      </div>

      {actionMessage && (
        <div className="p-3 bg-teal-950/80 border border-teal-800/60 rounded-2xl text-xs text-teal-200 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-teal-400" />
            <span>{actionMessage}</span>
          </div>
          <button type="button" onClick={() => setActionMessage(null)} className="text-[10px] text-slate-400 hover:text-white font-mono">Dismiss</button>
        </div>
      )}

      {/* Tab Views */}
      {activeTab === 'REVIEW_QUEUE' && queue && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-white uppercase font-mono">Human Learning Review Queue</h3>
              <p className="text-xs text-slate-400 mt-1">Review human corrections and AI error patterns before organization-wide promotion.</p>
            </div>
            <span className="text-[9px] font-mono text-teal-400 bg-teal-950 px-2 py-0.5 rounded border border-teal-800/60 font-bold">{queue.pending_items.length} PENDING</span>
          </div>

          <div className="space-y-3">
            {queue.pending_items.map(item => (
              <div key={item.id} className="p-4 bg-slate-950 border border-slate-800 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-white text-sm">{item.title}</span>
                    <span className="text-[9px] font-mono text-teal-400 bg-teal-950 px-2 py-0.5 rounded border border-teal-800/60 font-bold uppercase">{item.event_type}</span>
                  </div>
                  <p className="text-xs text-slate-300">{item.description}</p>
                  <p className="text-[10px] font-mono text-slate-500">Submitted by: {item.submitted_by} • Scope: {item.scope}</p>
                </div>

                <div className="flex items-center space-x-2 flex-shrink-0">
                  <button
                    type="button"
                    onClick={() => handleReviewAction(item.id, 'ACCEPT')}
                    className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 rounded-xl text-xs font-bold text-white flex items-center space-x-1"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Promote</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => handleReviewAction(item.id, 'REJECT')}
                    className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-bold flex items-center space-x-1"
                  >
                    <XCircle className="w-3.5 h-3.5" />
                    <span>Reject</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'REVALIDATION' && impact && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-white uppercase font-mono">Knowledge Revalidation & Downstream Impact Graph</h3>
              <p className="text-xs text-slate-400 mt-1">Preview downstream objects affected when source documents change.</p>
            </div>
            <button
              type="button"
              onClick={handleRevalidateDoc}
              className="px-4 py-2 bg-teal-600 hover:bg-teal-500 rounded-xl text-white font-bold text-xs flex items-center space-x-1"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Revalidate Doc #501</span>
            </button>
          </div>

          <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-3">
            <span className="font-bold text-teal-400 block font-mono uppercase">Downstream Graph Preview</span>
            <p className="text-xs text-slate-300">{impact.preview_summary}</p>

            <div className="space-y-2 pt-2">
              {impact.impact_graph.nodes.map(node => (
                <div key={node.id} className="p-3 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-between">
                  <span className="font-bold text-white text-xs font-mono">{node.label}</span>
                  <span className="text-[9px] font-mono text-indigo-400 bg-indigo-950 px-2 py-0.5 rounded border border-indigo-800/60 uppercase">{node.type}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'SHADOW_AUTO' && shadowAuto && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-white uppercase font-mono">Shadow Mode Automation Simulator & Promotion Control</h3>
              <p className="text-xs text-slate-400 mt-1">Rule: {shadowAuto.rule_name}</p>
            </div>
            <button
              type="button"
              onClick={() => handlePromoteAutomation(shadowAuto.rule_name)}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-xl text-white font-bold text-xs flex items-center space-x-1"
            >
              <Play className="w-3.5 h-3.5" />
              <span>Promote to Active Execution</span>
            </button>
          </div>

          <div className="p-5 bg-slate-950 border border-slate-800 rounded-3xl space-y-3 text-xs">
            <div className="flex items-center justify-between">
              <span className="font-bold text-white text-sm">Mode: {shadowAuto.mode}</span>
              <span className="text-[9px] font-mono font-bold bg-teal-950 text-teal-400 px-2 py-0.5 rounded border border-teal-800/60 uppercase">{shadowAuto.status}</span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-2">
              <div className="p-3 bg-slate-900 rounded-2xl">
                <span className="text-[10px] text-slate-400 block font-mono">Total Predictions</span>
                <span className="text-lg font-black text-white">{shadowAuto.total_predictions}</span>
              </div>
              <div className="p-3 bg-slate-900 rounded-2xl">
                <span className="text-[10px] text-slate-400 block font-mono">Human Alignment</span>
                <span className="text-lg font-black text-emerald-400">{shadowAuto.human_alignment_rate}</span>
              </div>
              <div className="p-3 bg-slate-900 rounded-2xl">
                <span className="text-[10px] text-slate-400 block font-mono">Matched Actions</span>
                <span className="text-lg font-black text-indigo-400">{shadowAuto.predicted_actions_matched}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'TELEMETRY' && dashboard && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Adaptive Intelligence Telemetry & Audit History</h3>
            <p className="text-xs text-slate-400 mt-1">Signal metrics, drift alerts, and complete traceable audit logs.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2">
              <span className="font-bold text-teal-400 block font-mono uppercase">Signal Telemetry</span>
              <p className="text-slate-300">• Total Signals: <strong className="text-white">{dashboard.signal_quality_metrics.total_learning_signals}</strong></p>
              <p className="text-slate-300">• Validated Signals: <strong className="text-white">{dashboard.signal_quality_metrics.validated_signals}</strong></p>
              <p className="text-slate-300">• Signal Accuracy: <strong className="text-emerald-400">{dashboard.signal_quality_metrics.signal_accuracy}</strong></p>
            </div>

            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2">
              <span className="font-bold text-amber-400 block font-mono uppercase">Drift Telemetry</span>
              <p className="text-slate-300">• Concept Drift: <strong className="text-white">{dashboard.drift_detection.concept_drift_status}</strong></p>
              <p className="text-slate-300">• Vocab Drift: <strong className="text-white">{dashboard.drift_detection.vocabulary_drift_status}</strong></p>
              <p className="text-slate-300">• Detected Drift: <strong className="text-cyan-400">{dashboard.drift_detection.detected_drift}</strong></p>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
