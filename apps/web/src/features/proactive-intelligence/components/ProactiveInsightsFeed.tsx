import React, { useState, useEffect } from 'react';
import {
  fetchProactiveInsights, scanKnowledgeDrift, acknowledgeProactiveInsight, dismissProactiveInsight, fetchEmergingPatterns, reportMissedInsight, fetchProactiveProjectHealth,
  ProactiveInsightItem, EmergingPatternItem, ProjectHealthResponse
} from '../proactive-intelligence-api';
import {
  Radar, AlertTriangle, ShieldCheck, CheckCircle2, Clock, Sparkles, Layers, ArrowRight, Check, Eye, X, MessageSquare, Flame, HelpCircle
} from 'lucide-react';

interface ProactiveInsightsFeedProps {
  initialProjectId?: string;
  token?: string;
}

export const ProactiveInsightsFeed: React.FC<ProactiveInsightsFeedProps> = ({
  initialProjectId = 'bfb4530e-bc5d-4c1f-aaf3-217a55bcaba4',
  token
}) => {
  const [activeScope, setActiveScope] = useState<'PROJECT' | 'WORKSPACE' | 'ORGANIZATION'>('PROJECT');
  const [insights, setInsights] = useState<ProactiveInsightItem[]>([]);
  const [patterns, setPatterns] = useState<EmergingPatternItem[]>([]);
  const [projectHealth, setProjectHealth] = useState<ProjectHealthResponse | null>(null);

  const [missedDescription, setMissedDescription] = useState<string>('MindMesh missed the database migration timeout risk.');
  const [showReportDialog, setShowReportDialog] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [ins, pat, ph] = await Promise.all([
        fetchProactiveInsights(activeScope, initialProjectId, token),
        fetchEmergingPatterns(token),
        fetchProactiveProjectHealth(initialProjectId, token)
      ]);
      setInsights(ins);
      setPatterns(pat);
      setProjectHealth(ph);
    } catch (err) {
      console.error('Failed to load proactive feed data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeScope, initialProjectId, token]);

  const handleScanDrift = async () => {
    setIsLoading(true);
    try {
      const res = await scanKnowledgeDrift(initialProjectId, token);
      setInsights(res);
      setActionMessage(`Scanned project for Knowledge Drift & Decision Drift.`);
    } catch (err) {
      console.error('Failed drift scan:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAcknowledge = async (insightId: string) => {
    try {
      const res = await acknowledgeProactiveInsight(insightId, token);
      setActionMessage(res.message);
      setInsights(prev => prev.map(i => i.insight_id === insightId ? res.insight : i));
    } catch (err) {
      console.error('Failed acknowledge:', err);
    }
  };

  const handleDismiss = async (insightId: string) => {
    try {
      const res = await dismissProactiveInsight(insightId, 'Dismissed by user from UI feed', token);
      setActionMessage(res.message);
      setInsights(prev => prev.map(i => i.insight_id === insightId ? res.insight : i));
    } catch (err) {
      console.error('Failed dismiss:', err);
    }
  };

  const handleReportMissed = async () => {
    if (!missedDescription.trim()) return;
    try {
      const res = await reportMissedInsight(missedDescription, initialProjectId, token);
      setActionMessage(res.message);
      setShowReportDialog(false);
    } catch (err) {
      console.error('Failed to report missed insight:', err);
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
                PROACTIVE INTELLIGENCE & EARLY WARNING
              </span>
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center space-x-1">
                <ShieldCheck className="w-3 h-3" />
                <span>Zero Surveillance • Evidence-Backed</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <Radar className="w-7 h-7 text-indigo-400" />
              <span>MindMesh Proactive Insights Feed</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Notices important changes, risks, knowledge drift, and emerging patterns before users have to search for them.
            </p>
          </div>

          {/* Scope Controls */}
          <div className="flex items-center space-x-2 bg-slate-950 p-1.5 rounded-2xl border border-slate-800 flex-shrink-0">
            <button
              type="button"
              onClick={() => setActiveScope('PROJECT')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeScope === 'PROJECT' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Project Scope
            </button>
            <button
              type="button"
              onClick={() => setActiveScope('WORKSPACE')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeScope === 'WORKSPACE' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Workspace Scope
            </button>
            <button
              type="button"
              onClick={() => setActiveScope('ORGANIZATION')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeScope === 'ORGANIZATION' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Org Patterns
            </button>
          </div>
        </div>

        {/* Project Health Status Bar */}
        {projectHealth && (
          <div className="p-3 bg-slate-950/80 border border-slate-800 rounded-2xl flex items-center justify-between text-xs pt-2">
            <div className="flex items-center space-x-2">
              <span className="text-[9px] font-mono text-slate-400 uppercase">Project Health:</span>
              <span className="font-bold text-amber-400 bg-amber-950 px-2 py-0.5 rounded border border-amber-800/60 font-mono text-[10px]">{projectHealth.health_state}</span>
              <span className="text-slate-300 text-[11px]">• {projectHealth.health_explanation}</span>
            </div>

            <button
              type="button"
              onClick={() => handleScanDrift()}
              className="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-white font-bold text-xs flex items-center space-x-1"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Scan Drift Now</span>
            </button>
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

      {/* Main Feed List */}
      <div className="space-y-4">
        
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold text-white uppercase font-mono">Surfaced Proactive Insights ({insights.length})</h3>
          <button
            type="button"
            onClick={() => setShowReportDialog(true)}
            className="text-[10px] font-mono text-slate-400 hover:text-indigo-300 underline"
          >
            + Report Missed Issue
          </button>
        </div>

        {insights.map((ins) => (
          <div key={ins.insight_id} className="p-5 bg-slate-900/80 border border-slate-800 rounded-3xl space-y-4 shadow-xl backdrop-blur-md">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className={`text-[8px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${
                  ins.priority === 'CRITICAL' ? 'bg-red-950 text-red-400 border-red-800/60' : 'bg-amber-950 text-amber-400 border-amber-800/60'
                }`}>{ins.priority}</span>
                <span className="text-[9px] font-mono text-indigo-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">{ins.insight_type}</span>
              </div>
              <span className="text-[9px] font-mono text-slate-500">State: {ins.lifecycle_state}</span>
            </div>

            <div>
              <h4 className="text-sm font-bold text-white">{ins.title}</h4>
              <p className="text-xs text-slate-300 mt-1">{ins.what_changed}</p>
              <p className="text-xs text-amber-300 font-medium mt-1">Why it matters: {ins.why_it_matters}</p>
            </div>

            <div className="p-3 bg-slate-950 border border-slate-800 rounded-2xl text-xs space-y-1">
              <span className="text-[9px] font-mono text-slate-500 uppercase block">Affected Entities</span>
              {ins.affected_entities.map((e, i) => (
                <p key={i} className="text-[11px] text-slate-300">• {e}</p>
              ))}
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-slate-800/60">
              <span className="text-[11px] font-mono text-indigo-400 font-bold">Suggested: {ins.suggested_next_action}</span>

              <div className="flex items-center space-x-2">
                {ins.lifecycle_state !== 'ACKNOWLEDGED' && (
                  <button
                    type="button"
                    onClick={() => handleAcknowledge(ins.insight_id)}
                    className="px-3 py-1 bg-slate-950 hover:bg-slate-800 border border-slate-800 rounded-xl text-xs text-slate-300 font-bold flex items-center space-x-1"
                  >
                    <Eye className="w-3 h-3" />
                    <span>Acknowledge</span>
                  </button>
                )}

                {ins.lifecycle_state !== 'DISMISSED' && (
                  <button
                    type="button"
                    onClick={() => handleDismiss(ins.insight_id)}
                    className="px-3 py-1 bg-slate-950 hover:bg-slate-800 border border-slate-800 rounded-xl text-xs text-slate-400 hover:text-white font-bold flex items-center space-x-1"
                  >
                    <X className="w-3 h-3" />
                    <span>Dismiss</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}

        {/* Emerging Patterns Section */}
        {patterns.length > 0 && (
          <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md mt-6">
            <h3 className="text-xs font-bold text-white uppercase font-mono border-b border-slate-800 pb-3 flex items-center space-x-2">
              <Flame className="w-4 h-4 text-amber-400" />
              <span>Emerging Cross-Project Organizational Patterns</span>
            </h3>

            <div className="space-y-3">
              {patterns.map((pat) => (
                <div key={pat.pattern_id} className="p-4 bg-slate-950 border border-amber-800/60 rounded-2xl space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-[8px] font-mono font-bold text-amber-400 bg-amber-950 px-2 py-0.5 rounded border border-amber-800/60 uppercase">MATURITY: {pat.maturity}</span>
                    <span className="text-[9px] font-mono text-slate-500">{pat.occurrences} occurrences</span>
                  </div>
                  <h4 className="font-bold text-white">{pat.title}</h4>
                  <p className="text-[10px] text-slate-400">{pat.evidence}</p>
                  <p className="text-[10px] text-indigo-400 font-medium">Recommendation: {pat.recommended_consolidation}</p>
                </div>
              ))}
            </div>
          </div>
        )}

      </div>

      {/* Missed Insight Report Modal */}
      {showReportDialog && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-3xl max-w-md w-full space-y-4 shadow-2xl">
            <h3 className="text-sm font-bold text-white uppercase font-mono">Report Missed Organizational Issue</h3>
            <p className="text-xs text-slate-400">Feedback helps MindMesh improve proactive pattern detection without self-reinforcing noise.</p>
            
            <textarea
              value={missedDescription}
              onChange={(e) => setMissedDescription(e.target.value)}
              rows={3}
              className="w-full bg-slate-950 border border-slate-800 rounded-2xl p-3 text-xs text-white focus:outline-none"
            />

            <div className="flex justify-end space-x-2 pt-2">
              <button
                type="button"
                onClick={() => setShowReportDialog(false)}
                className="px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-400"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => handleReportMissed()}
                className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-white font-bold text-xs"
              >
                Submit Feedback
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
