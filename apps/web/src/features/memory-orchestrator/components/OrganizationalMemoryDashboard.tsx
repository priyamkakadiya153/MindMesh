import React, { useState, useEffect } from 'react';
import {
  fetchEventImpactAnalysis, fetchDependencyMap, fetchKnowledgeClusters, fetchOrganizationalPatterns, simulateImpact,
  ImpactAnalysisResponse, DependencyMapResponse, KnowledgeClusterItem, PatternItem, ImpactSimulationResponse
} from '../memory-orchestrator-api';
import {
  GitFork, Cpu, ShieldAlert, Sparkles, Layers, ArrowRight, CornerDownRight, CheckCircle2, Play, RefreshCw, FileText, AlertTriangle, Activity
} from 'lucide-react';

interface OrganizationalMemoryDashboardProps {
  token?: string;
}

export const OrganizationalMemoryDashboard: React.FC<OrganizationalMemoryDashboardProps> = ({ token }) => {
  const [activeTab, setActiveTab] = useState<'IMPACT' | 'DEPENDENCIES' | 'CLUSTERS' | 'PATTERNS' | 'SIMULATOR'>('IMPACT');
  const [impactData, setImpactData] = useState<ImpactAnalysisResponse | null>(null);
  const [depData, setDepData] = useState<DependencyMapResponse | null>(null);
  const [clusters, setClusters] = useState<KnowledgeClusterItem[]>([]);
  const [patterns, setPatterns] = useState<PatternItem[]>([]);
  const [simulationChange, setSimulationChange] = useState<string>('JWT expiry changed to 60 minutes');
  const [simResult, setSimResult] = useState<ImpactSimulationResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [impRes, depRes, clsRes, patRes] = await Promise.all([
        fetchEventImpactAnalysis('DECISION_CHANGED', 'dec-jwt-30m', token),
        fetchDependencyMap('task-deploy-cfg', token),
        fetchKnowledgeClusters(token),
        fetchOrganizationalPatterns(token)
      ]);
      setImpactData(impRes);
      setDepData(depRes);
      setClusters(clsRes);
      setPatterns(patRes);
    } catch (err) {
      console.error('Failed to load orchestration dashboard:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [token]);

  const handleSimulate = async () => {
    if (!simulationChange.trim()) return;
    try {
      const sim = await simulateImpact(simulationChange, 'dec-jwt-30m', token);
      setSimResult(sim);
    } catch (err) {
      console.error('Failed simulation:', err);
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
                ORGANIZATIONAL MEMORY ORCHESTRATION & GRAPH INTELLIGENCE
              </span>
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center space-x-1">
                <CheckCircle2 className="w-3 h-3" />
                <span>Deterministic Graph & Cross-Entity Memory</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <Cpu className="w-7 h-7 text-indigo-400" />
              <span>Organizational Memory Dashboard</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Orchestrates cross-entity relationships between projects, decisions, documents, tasks, and risks without destructive auto-edits.
            </p>
          </div>

          {/* Navigation Mode Tabs */}
          <div className="flex items-center space-x-2 bg-slate-950 p-1.5 rounded-2xl border border-slate-800 flex-shrink-0">
            <button
              type="button"
              onClick={() => setActiveTab('IMPACT')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'IMPACT' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Impact Analysis
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('DEPENDENCIES')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'DEPENDENCIES' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Dependencies & Flow
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('CLUSTERS')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'CLUSTERS' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Clusters
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('SIMULATOR')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'SIMULATOR' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Simulator
            </button>
          </div>
        </div>
      </div>

      {/* Tab Views */}
      {activeTab === 'IMPACT' && impactData && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Event Impact Analysis & Change Propagation</h3>
            <p className="text-xs text-slate-400 mt-1">{impactData.impact_summary}</p>
          </div>

          <div className="space-y-4">
            {/* Direct Impact */}
            <div className="p-4 bg-slate-950 border border-red-800/60 rounded-2xl space-y-2">
              <span className="text-[9px] font-mono font-bold text-red-400 uppercase">DIRECT IMPACT</span>
              {impactData.direct_impact.map((item) => (
                <div key={item.entity_id} className="p-3 bg-slate-900 border border-slate-800 rounded-xl text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white">{item.title}</span>
                    <span className="text-[8px] font-mono text-slate-400">{item.entity_type}</span>
                  </div>
                  <p className="text-[10px] text-slate-300">{item.explanation}</p>
                </div>
              ))}
            </div>

            {/* Related Impact */}
            <div className="p-4 bg-slate-950 border border-amber-800/60 rounded-2xl space-y-2">
              <span className="text-[9px] font-mono font-bold text-amber-400 uppercase">RELATED IMPACT</span>
              {impactData.related_impact.map((item) => (
                <div key={item.entity_id} className="p-3 bg-slate-900 border border-slate-800 rounded-xl text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white">{item.title}</span>
                    <span className="text-[8px] font-mono text-slate-400">{item.entity_type}</span>
                  </div>
                  <p className="text-[10px] text-slate-300">{item.explanation}</p>
                </div>
              ))}
            </div>

            {/* Potential Impact */}
            <div className="p-4 bg-slate-950 border border-indigo-800/60 rounded-2xl space-y-2">
              <span className="text-[9px] font-mono font-bold text-indigo-400 uppercase">POTENTIAL INFERRED IMPACT</span>
              {impactData.potential_impact.map((item) => (
                <div key={item.entity_id} className="p-3 bg-slate-900 border border-slate-800 rounded-xl text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-white">{item.title}</span>
                    <span className="text-[8px] font-mono text-slate-400">{item.entity_type}</span>
                  </div>
                  <p className="text-[10px] text-slate-300">{item.explanation}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'DEPENDENCIES' && depData && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Upstream & Downstream Dependency Engine</h3>
            <span className="text-[9px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60">
              Health: {depData.dependency_health}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-3">
              <h4 className="text-xs font-bold text-indigo-400 uppercase font-mono">Upstream Dependencies (What this relies on)</h4>
              {depData.upstream_dependencies.map((up) => (
                <div key={up.id} className="p-2.5 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-between text-xs">
                  <span className="font-bold text-white">{up.title}</span>
                  <span className="text-[8px] font-mono text-indigo-400">{up.relation}</span>
                </div>
              ))}
            </div>

            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-3">
              <h4 className="text-xs font-bold text-indigo-400 uppercase font-mono">Downstream Impacts (What relies on this)</h4>
              {depData.downstream_impacts.map((down) => (
                <div key={down.id} className="p-2.5 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-between text-xs">
                  <span className="font-bold text-white">{down.title}</span>
                  <span className="text-[8px] font-mono text-indigo-400">{down.relation}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'CLUSTERS' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <h3 className="text-xs font-bold text-white uppercase font-mono border-b border-slate-800 pb-3">Conceptual Knowledge Clusters</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {clusters.map((cls) => (
              <div key={cls.cluster_id} className="p-5 bg-slate-950 border border-indigo-800/60 rounded-3xl space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-white">{cls.concept_name}</h4>
                  <span className="text-[9px] font-mono text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60">{cls.health}</span>
                </div>

                <div className="space-y-1.5 pt-2">
                  <span className="text-[9px] font-mono text-slate-500 uppercase block">Supporting Sources ({cls.source_count})</span>
                  {cls.sources.map((src, i) => (
                    <div key={i} className="p-2 bg-slate-900 border border-slate-800 rounded-xl text-xs flex items-center justify-between">
                      <span className="text-slate-300 font-medium">{src.title}</span>
                      <span className="text-[8px] font-mono text-indigo-400">{src.type}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'SIMULATOR' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Impact Simulator ("What if this decision changes?")</h3>
            <p className="text-xs text-slate-400 mt-1">Runs graph-based change simulations without modifying database records.</p>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-3">
            <input
              type="text"
              value={simulationChange}
              onChange={(e) => setSimulationChange(e.target.value)}
              className="flex-1 bg-slate-950 border border-slate-800 rounded-2xl px-4 py-2 text-xs text-white focus:outline-none"
            />
            <button
              type="button"
              onClick={() => handleSimulate()}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-2xl text-white font-bold text-xs shadow-lg flex items-center space-x-1.5 flex-shrink-0"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>Run Simulation</span>
            </button>
          </div>

          {simResult && (
            <div className="p-5 bg-slate-950 border border-indigo-800/60 rounded-3xl space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="text-[9px] font-mono text-emerald-400 font-bold uppercase">Simulation Complete (Read-Only)</span>
                <span className="text-[9px] font-mono text-slate-500">DB Modified: False</span>
              </div>

              <div className="space-y-2">
                <span className="text-[9px] font-mono text-indigo-400 uppercase font-bold">Simulated Change Cascade</span>
                {simResult.simulated_cascade.map((cas, i) => (
                  <p key={i} className="text-xs text-slate-200 font-mono">• {cas}</p>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

    </div>
  );
};
