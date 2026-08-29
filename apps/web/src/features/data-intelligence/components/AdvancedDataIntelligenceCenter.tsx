import React, { useState, useEffect } from 'react';
import {
  fetchPortfolioAnalytics, fetchProjectIntelligence, fetchKnowledgeHealthAnalytics,
  fetchBottlenecksAndDependencies, fetchTrendsAnomalies, fetchDrilldownEvidence,
  PortfolioAnalyticsResponse, ProjectIntelligenceResponse, KnowledgeHealthResponse,
  BottlenecksResponse, TrendsAnomaliesResponse, DrilldownEvidenceResponse
} from '../data-intelligence-api';
import {
  BarChart3, PieChart, TrendingUp, AlertTriangle, Search, ShieldCheck, Layers,
  ArrowRight, FileText, CheckCircle2, ChevronRight, Activity, Filter, Info, Eye
} from 'lucide-react';

interface AdvancedDataIntelligenceCenterProps {
  initialProjectId?: string;
  token?: string;
}

export const AdvancedDataIntelligenceCenter: React.FC<AdvancedDataIntelligenceCenterProps> = ({
  initialProjectId = 'p-101',
  token
}) => {
  const [activeTab, setActiveTab] = useState<'PORTFOLIO' | 'PROJECT_HEALTH' | 'KNOWLEDGE_GAPS' | 'BOTTLENECKS' | 'TRENDS'>('PORTFOLIO');
  const [portfolio, setPortfolio] = useState<PortfolioAnalyticsResponse | null>(null);
  const [projectIntel, setProjectIntel] = useState<ProjectIntelligenceResponse | null>(null);
  const [knowledgeHealth, setKnowledgeHealth] = useState<KnowledgeHealthResponse | null>(null);
  const [bottlenecks, setBottlenecks] = useState<BottlenecksResponse | null>(null);
  const [trendsAnomalies, setTrendsAnomalies] = useState<TrendsAnomaliesResponse | null>(null);
  
  const [selectedInsightId, setSelectedInsightId] = useState<string | null>(null);
  const [drilldown, setDrilldown] = useState<DrilldownEvidenceResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [portRes, projRes, knowRes, botRes, fontRes] = await Promise.all([
        fetchPortfolioAnalytics(token),
        fetchProjectIntelligence(initialProjectId, token),
        fetchKnowledgeHealthAnalytics(token),
        fetchBottlenecksAndDependencies(token),
        fetchTrendsAnomalies(token)
      ]);
      setPortfolio(portRes);
      setProjectIntel(projRes);
      setKnowledgeHealth(knowRes);
      setBottlenecks(botRes);
      setTrendsAnomalies(fontRes);
    } catch (err) {
      console.error('Failed to load data intelligence center:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [token, initialProjectId]);

  const handleDrilldown = async (insightId: string) => {
    setSelectedInsightId(insightId);
    try {
      const res = await fetchDrilldownEvidence(insightId, token);
      setDrilldown(res);
    } catch (err) {
      console.error('Failed to load drilldown evidence:', err);
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
                ADVANCED DATA INTELLIGENCE & ORGANIZATIONAL INSIGHT
              </span>
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center space-x-1">
                <ShieldCheck className="w-3 h-3" />
                <span>RBAC & Evidence Provenance Verified</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <BarChart3 className="w-7 h-7 text-indigo-400" />
              <span>Organizational Intelligence Center</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Cross-entity analytics, project health signals, zero-result search gaps, bottlenecks, and evidence-backed explanations.
            </p>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center space-x-2 bg-slate-950 p-1.5 rounded-2xl border border-slate-800 flex-shrink-0">
            <button
              type="button"
              onClick={() => setActiveTab('PORTFOLIO')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'PORTFOLIO' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Portfolio
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('PROJECT_HEALTH')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'PROJECT_HEALTH' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Project Health
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('KNOWLEDGE_GAPS')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'KNOWLEDGE_GAPS' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Knowledge Gaps
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('BOTTLENECKS')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'BOTTLENECKS' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Bottlenecks
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('TRENDS')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'TRENDS' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Trends & Anomalies
            </button>
          </div>
        </div>

        {/* Telemetry Metrics Bar */}
        {portfolio && knowledgeHealth && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 border-t border-slate-800/60">
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Portfolio Health</span>
              <span className="text-lg font-black text-emerald-400">{portfolio.portfolio_summary.overall_portfolio_health}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Knowledge Freshness</span>
              <span className="text-lg font-black text-indigo-400">{knowledgeHealth.health_summary.freshness_score}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Zero-Result Searches</span>
              <span className="text-lg font-black text-amber-400">{knowledgeHealth.zero_result_searches.length}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Active Bottlenecks</span>
              <span className="text-lg font-black text-red-400">{bottlenecks?.bottlenecks.length || 0}</span>
            </div>
          </div>
        )}
      </div>

      {/* Tab Views */}
      {activeTab === 'PORTFOLIO' && portfolio && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-white uppercase font-mono">Executive Organization Portfolio Matrix</h3>
              <p className="text-xs text-slate-400 mt-1">Cross-project health, task progress, and top risk signals.</p>
            </div>
            <span className="text-[9px] font-mono text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 font-bold">LIVE AGGREGATE</span>
          </div>

          <div className="space-y-3">
            {portfolio.projects_matrix.map(proj => (
              <div key={proj.id} className="p-4 bg-slate-950 border border-slate-800 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-white text-sm">{proj.name}</span>
                    <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${
                      proj.status === 'HEALTHY' ? 'bg-emerald-950 text-emerald-400 border-emerald-800/60' : 'bg-amber-950 text-amber-400 border-amber-800/60'
                    }`}>
                      {proj.status}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">Open Tasks: {proj.open_tasks} | Blocked Tasks: <strong className="text-red-400">{proj.blocked_tasks}</strong></p>
                </div>

                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    <span className="text-[10px] text-slate-400 uppercase font-mono block">Progress</span>
                    <span className="text-sm font-black text-indigo-400">{proj.progress_percentage}%</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleDrilldown(`proj-${proj.id}`)}
                    className="px-3 py-1.5 bg-indigo-950 hover:bg-indigo-900 border border-indigo-800/60 rounded-xl text-xs font-bold text-indigo-300 flex items-center space-x-1"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>Evidence</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'PROJECT_HEALTH' && projectIntel && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-white uppercase font-mono">Project Intelligence & Health Signals</h3>
              <p className="text-xs text-slate-400 mt-1">{projectIntel.project_name}</p>
            </div>
            <span className="text-[9px] font-mono text-amber-400 bg-amber-950 px-2 py-0.5 rounded border border-amber-800/60 font-bold">
              TREND: {projectIntel.trend.direction}
            </span>
          </div>

          <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-3">
            <h4 className="text-xs font-bold text-amber-400 font-mono uppercase">Contributing Health Signals</h4>
            <div className="space-y-2">
              {projectIntel.health_assessment.contributing_signals.map((sig, idx) => (
                <div key={idx} className="p-3 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white text-xs">{sig.signal}</span>
                    <span className="text-[9px] font-mono text-red-400 uppercase font-bold">{sig.severity}</span>
                  </div>
                  <p className="text-xs text-slate-300">{sig.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'KNOWLEDGE_GAPS' && knowledgeHealth && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Zero-Result Search & Knowledge Gap Detector</h3>
            <p className="text-xs text-slate-400 mt-1">Identifies search terms producing zero results and automatically correlates missing documentation.</p>
          </div>

          <div className="space-y-4">
            {knowledgeHealth.zero_result_searches.map((zero, idx) => (
              <div key={idx} className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-amber-400 text-xs font-mono">Search Query: "{zero.query}"</span>
                  <span className="text-[9px] font-mono text-red-400 bg-red-950 px-2 py-0.5 rounded border border-red-800/60 font-bold">{zero.search_count} Searches (100% Zero Results)</span>
                </div>
                <p className="text-xs text-slate-300">• <strong className="text-white">Detected Gap:</strong> {zero.potential_knowledge_gap}</p>
                <p className="text-xs text-slate-400">• <strong className="text-slate-200">Evidence:</strong> {zero.evidence}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'BOTTLENECKS' && bottlenecks && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Bottleneck & Shared Dependency Risk Map</h3>
            <p className="text-xs text-slate-400 mt-1">Work accumulation points and multi-project dependency risks.</p>
          </div>

          <div className="space-y-3">
            {bottlenecks.bottlenecks.map(bot => (
              <div key={bot.id} className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white text-xs">{bot.target}</span>
                  <span className="text-[9px] font-mono text-red-400 bg-red-950 px-2 py-0.5 rounded border border-red-800/60 font-bold">{bot.type}</span>
                </div>
                <p className="text-xs text-slate-300">{bot.description}</p>
                <div className="text-[10px] font-mono text-indigo-300 bg-indigo-950/60 p-2 rounded-xl border border-indigo-800/40">
                  Chain: {bot.evidence_chain.join(' → ')}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'TRENDS' && trendsAnomalies && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Trend, Anomaly & Recurring Pattern Detection</h3>
            <p className="text-xs text-slate-400 mt-1">Statistical anomalies and recurring organizational patterns with evidence.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2">
              <span className="font-bold text-red-400 block font-mono uppercase">Detected Anomalies</span>
              {trendsAnomalies.anomalies.map(anom => (
                <div key={anom.id} className="p-3 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
                  <span className="font-bold text-white text-xs block">{anom.event_type}</span>
                  <p className="text-slate-300">{anom.observed_anomaly}</p>
                  <p className="text-slate-400 text-[10px]">• Explanation: {anom.possible_explanation}</p>
                </div>
              ))}
            </div>

            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2">
              <span className="font-bold text-amber-400 block font-mono uppercase">Recurring Patterns</span>
              {trendsAnomalies.recurring_patterns.map(pat => (
                <div key={pat.id} className="p-3 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
                  <span className="font-bold text-white text-xs block">{pat.pattern_name}</span>
                  <p className="text-slate-300">Occurrences: {pat.occurrences} across {pat.affected_scope}</p>
                  <p className="text-slate-400 text-[10px]">• Explanation: {pat.potential_explanation}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Drill-Down Evidence Drawer */}
      {selectedInsightId && drilldown && (
        <div className="p-5 bg-slate-900 border border-indigo-800/60 rounded-3xl space-y-3 text-xs shadow-2xl">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <span className="font-bold text-indigo-400 font-mono uppercase">Insight Drill-Down Evidence Chain</span>
            <button type="button" onClick={() => setSelectedInsightId(null)} className="text-[10px] text-slate-400 hover:text-white font-mono">Close</button>
          </div>

          <div className="p-3 bg-slate-950 rounded-2xl space-y-1 font-mono text-[11px]">
            <p className="text-slate-300">• <strong className="text-white">WHAT:</strong> {drilldown.explanation.what}</p>
            <p className="text-slate-300">• <strong className="text-white">WHY:</strong> {drilldown.explanation.why}</p>
            <p className="text-slate-300">• <strong className="text-white">IMPACT:</strong> {drilldown.explanation.impact}</p>
            <p className="text-slate-300">• <strong className="text-white">ACTION:</strong> {drilldown.explanation.recommended_action}</p>
          </div>

          <div className="space-y-1">
            <span className="text-[10px] font-mono text-slate-400 uppercase font-bold">Authorized Evidence Chain</span>
            {drilldown.evidence_chain.map((item, idx) => (
              <div key={idx} className="flex items-center justify-between p-2 bg-slate-950/60 border border-slate-800 rounded-xl text-slate-300">
                <span>{item.entity_type}: <strong>{item.title}</strong></span>
                <span className="text-[9px] font-mono text-emerald-400 uppercase font-bold">{item.status}</span>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
};
