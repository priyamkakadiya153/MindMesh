import React, { useState, useEffect } from 'react';
import {
  fetchProactiveDashboard, fetchDailyBrief, scanSystemSignals, handleInsightAction, dismissInsight, fetchProactiveDigest,
  ProactiveInsightItem, DailyBriefResponse, ProactiveDigestResponse
} from '../proactive-organizational-api';
import {
  Radio, ShieldCheck, CheckCircle2, AlertTriangle, Layers, Bell, Check, X, Sparkles, BookOpen, Activity, ArrowRight, ShieldAlert
} from 'lucide-react';

interface ProactiveOrganizationalIntelligenceCenterProps {
  initialProjectId?: string;
  token?: string;
}

export const ProactiveOrganizationalIntelligenceCenter: React.FC<ProactiveOrganizationalIntelligenceCenterProps> = ({
  initialProjectId = 'bfb4530e-bc5d-4c1f-aaf3-217a55bcaba4',
  token
}) => {
  const [activeTab, setActiveTab] = useState<'STREAM' | 'BRIEF' | 'BLAST' | 'DIGEST'>('STREAM');
  const [insights, setInsights] = useState<ProactiveInsightItem[]>([]);
  const [selectedInsight, setSelectedInsight] = useState<ProactiveInsightItem | null>(null);
  const [dailyBrief, setDailyBrief] = useState<DailyBriefResponse | null>(null);
  const [digest, setDigest] = useState<ProactiveDigestResponse | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [dashRes, briefRes, digRes] = await Promise.all([
        fetchProactiveDashboard(token),
        fetchDailyBrief(token),
        fetchProactiveDigest(token)
      ]);
      setInsights(dashRes.insights);
      if (dashRes.insights.length > 0) {
        setSelectedInsight(dashRes.insights[0]);
      }
      setDailyBrief(briefRes);
      setDigest(digRes);
    } catch (err) {
      console.error('Failed to load proactive organizational intelligence center:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [initialProjectId, token]);

  const handleScan = async () => {
    try {
      const res = await scanSystemSignals(initialProjectId, token);
      setInsights(res);
      if (res.length > 0) setSelectedInsight(res[0]);
      setActionMessage(`System Signal Scan completed. Surfaced ${res.length} meaningful, deduplicated insights.`);
    } catch (err) {
      console.error('Failed signal scan:', err);
    }
  };

  const handleAction = async (insightId: string, actionType: string) => {
    try {
      const res = await handleInsightAction(insightId, actionType, token);
      setActionMessage(res.message);
      loadData();
    } catch (err) {
      console.error('Failed insight action:', err);
    }
  };

  const handleDismiss = async (insightId: string) => {
    try {
      const res = await dismissInsight(insightId, 'Not Relevant to current sprint', token);
      setActionMessage(res.message);
      loadData();
    } catch (err) {
      console.error('Failed insight dismissal:', err);
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
                PROACTIVE ORGANIZATIONAL INTELLIGENCE & EARLY WARNING
              </span>
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center space-x-1">
                <ShieldCheck className="w-3 h-3" />
                <span>Zero Notification Spam</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <Radio className="w-7 h-7 text-indigo-400 animate-pulse" />
              <span>Proactive Intelligence Center</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Proactively notices important changes, risks, opportunities, knowledge gaps, and decision points before you ask.
            </p>
          </div>

          {/* Navigation Mode Tabs */}
          <div className="flex items-center space-x-2 bg-slate-950 p-1.5 rounded-2xl border border-slate-800 flex-shrink-0">
            <button
              type="button"
              onClick={() => setActiveTab('STREAM')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'STREAM' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Intelligence Stream
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('BRIEF')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'BRIEF' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              MindMesh Brief
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('BLAST')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'BLAST' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Blast Radius
            </button>
          </div>
        </div>

        {/* Digest Counters Bar */}
        {digest && (
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-2 border-t border-slate-800/60">
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Signals Scanned</span>
              <span className="text-lg font-black text-indigo-400">{digest.total_signals_scanned}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Insights Surfaced</span>
              <span className="text-lg font-black text-emerald-400">{digest.meaningful_insights_surfaced}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Alerts Deduplicated</span>
              <span className="text-lg font-black text-purple-400">{digest.alert_clusters_deduplicated}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Decisions Prepared</span>
              <span className="text-lg font-black text-amber-400">{digest.decisions_prepared_proactively}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Dismissed (False Positives)</span>
              <span className="text-lg font-black text-cyan-400">{digest.dismissed_false_positives}</span>
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
      {activeTab === 'STREAM' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono flex items-center space-x-2">
              <Bell className="w-4 h-4 text-indigo-400" />
              <span>Prioritized Proactive Intelligence Stream</span>
            </h3>

            <button
              type="button"
              onClick={() => handleScan()}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-2xl text-white font-bold text-xs shadow-lg flex items-center space-x-1.5"
            >
              <Sparkles className="w-4 h-4" />
              <span>Scan System Signals</span>
            </button>
          </div>

          <div className="space-y-3">
            {insights.map(ins => (
              <div key={ins.insight_id} className={`p-4 bg-slate-950 border rounded-2xl space-y-2 text-xs transition-all ${
                selectedInsight?.insight_id === ins.insight_id ? 'border-indigo-600 ring-1 ring-indigo-500/50' : 'border-slate-800'
              }`} onClick={() => setSelectedInsight(ins)}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className={`text-[8px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${
                      ins.severity === 'HIGH' ? 'bg-red-950 text-red-400 border-red-800/60' :
                      ins.severity === 'MEDIUM' ? 'bg-amber-950 text-amber-400 border-amber-800/60' : 'bg-indigo-950 text-indigo-400 border-indigo-800/60'
                    }`}>{ins.severity}</span>
                    <span className="text-[9px] font-mono text-slate-500 bg-slate-900 px-2 py-0.5 rounded">{ins.insight_type}</span>
                  </div>
                  
                  <div className="flex items-center space-x-1">
                    <button
                      type="button"
                      onClick={(e) => { e.stopPropagation(); handleAction(ins.insight_id, 'ACKNOWLEDGE'); }}
                      className="px-2.5 py-1 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-white font-bold text-[10px]"
                    >
                      Acknowledge
                    </button>
                    <button
                      type="button"
                      onClick={(e) => { e.stopPropagation(); handleDismiss(ins.insight_id); }}
                      className="px-2 py-1 bg-slate-800 hover:bg-slate-700 rounded-lg text-slate-400 hover:text-white font-bold text-[10px]"
                    >
                      Dismiss
                    </button>
                  </div>
                </div>

                <h4 className="font-bold text-white text-sm">{ins.title}</h4>
                <p className="text-slate-300">{ins.summary}</p>
                <div className="p-2.5 bg-slate-900 rounded-xl space-y-1">
                  <p className="text-[10px] text-slate-400"><strong className="text-indigo-300">What Changed:</strong> {ins.what_changed}</p>
                  <p className="text-[10px] text-slate-400"><strong className="text-indigo-300">Why It Matters:</strong> {ins.why_it_matters}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'BRIEF' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Your Daily MindMesh Brief</h3>
            <p className="text-xs text-slate-400 mt-1">Role-aware intelligence brief summarizing important changes, risks, and decisions needed.</p>
          </div>

          {dailyBrief && (
            <div className="p-5 bg-slate-950 border border-indigo-800/60 rounded-3xl space-y-4 text-xs">
              <div className="flex items-center justify-between">
                <h4 className="font-bold text-white text-sm">{dailyBrief.brief_title}</h4>
                <span className="text-[9px] font-mono text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 font-bold">{dailyBrief.provenance_label}</span>
              </div>

              <div className="space-y-3">
                {dailyBrief.sections.map((sec, i) => (
                  <div key={i} className="p-3 bg-slate-900 rounded-2xl space-y-1">
                    <span className="text-[10px] font-bold text-indigo-400 block uppercase font-mono">{sec.heading}</span>
                    {sec.items.map((it, idx) => (
                      <p key={idx} className="text-slate-300">• {it}</p>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'BLAST' && selectedInsight && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono flex items-center space-x-2">
              <ShieldAlert className="w-4 h-4 text-amber-400" />
              <span>Blast Radius & Knowledge Graph Trace</span>
            </h3>
            <p className="text-xs text-slate-400 mt-1">Impact analysis for selected insight '{selectedInsight.insight_id}'.</p>
          </div>

          <div className="p-5 bg-slate-950 border border-slate-800 rounded-3xl space-y-4 text-xs">
            <h4 className="font-bold text-white text-sm">{selectedInsight.title}</h4>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-3 bg-slate-900 rounded-2xl space-y-1">
                <span className="text-[9px] font-mono text-red-400 uppercase font-bold block">Direct Impact</span>
                {selectedInsight.blast_radius.direct_impact.map((di, i) => (
                  <p key={i} className="text-slate-300">• {di}</p>
                ))}
              </div>

              <div className="p-3 bg-slate-900 rounded-2xl space-y-1">
                <span className="text-[9px] font-mono text-amber-400 uppercase font-bold block">Indirect Downstream Impact</span>
                {selectedInsight.blast_radius.indirect_impact.map((ii, i) => (
                  <p key={i} className="text-slate-300">• {ii}</p>
                ))}
              </div>
            </div>

            <div className="p-3 bg-slate-900 rounded-2xl space-y-1">
              <span className="text-[9px] font-mono text-indigo-400 uppercase font-bold block">Evidence Trace</span>
              {selectedInsight.evidence.map((ev, i) => (
                <p key={i} className="text-slate-300">• {ev}</p>
              ))}
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
