import React, { useState, useEffect } from 'react';
import {
  fetchPerformanceBaselines, optimizeQueryExecution, routeAIRequest, batchEmbeddings, fetchCapacityMetrics,
  PerformanceBaselinesResponse, AIRouteResponse, CapacityMetricsResponse
} from '../performance-scale-api';
import {
  Zap, Gauge, Cpu, DollarSign, Layers, ArrowUpRight, CheckCircle2, Sliders, Database, Server, Activity, Compass
} from 'lucide-react';

interface PerformanceScalabilityCenterProps {
  initialWorkspaceId?: string;
  token?: string;
}

export const PerformanceScalabilityCenter: React.FC<PerformanceScalabilityCenterProps> = ({
  initialWorkspaceId = '6d25a626-a2c5-47ec-9107-88fdf97ee095',
  token
}) => {
  const [activeTab, setActiveTab] = useState<'BASELINES' | 'AI_ROUTING' | 'QUERY_OPT' | 'CAPACITY'>('BASELINES');
  const [baselines, setBaselines] = useState<PerformanceBaselinesResponse | null>(null);
  const [capacity, setCapacity] = useState<CapacityMetricsResponse | null>(null);
  const [aiRouteResult, setAiRouteResult] = useState<AIRouteResponse | null>(null);
  const [queryOptResult, setQueryOptResult] = useState<any | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [baseRes, capRes] = await Promise.all([
        fetchPerformanceBaselines(token),
        fetchCapacityMetrics(token)
      ]);
      setBaselines(baseRes);
      setCapacity(capRes);
    } catch (err) {
      console.error('Failed to load performance scalability center:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [token]);

  const handleTestAIRouting = async (complexity: string) => {
    try {
      const res = await routeAIRequest(complexity, 'Extract metadata and classify document', token);
      setAiRouteResult(res);
      setActionMessage(`AI Task Routed to '${res.selected_model}'. Tokens Saved: ${res.tokens_saved}`);
    } catch (err) {
      console.error('Failed AI routing test:', err);
    }
  };

  const handleTestQueryOpt = async () => {
    try {
      const res = await optimizeQueryExecution('MESSAGE_HISTORY_TIMELINE', undefined, 50, token);
      setQueryOptResult(res);
      setActionMessage(`Query Optimized via Cursor Pagination. Prevented ${res.n_plus_one_queries_prevented} N+1 DB queries.`);
    } catch (err) {
      console.error('Failed query optimization test:', err);
    }
  };

  const handleTestBatchEmbeddings = async () => {
    try {
      const res = await batchEmbeddings(['doc-101', 'doc-102', 'doc-103', 'doc-104'], initialWorkspaceId, token);
      setActionMessage(res.message);
    } catch (err) {
      console.error('Failed batch embeddings:', err);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6 text-slate-100 font-sans select-none">
      
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-amber-950/80 to-slate-900 border border-amber-800/60 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-amber-400 px-2.5 py-0.5 bg-amber-950 rounded border border-amber-800/60">
                PERFORMANCE, SCALABILITY & HIGH-SCALE ARCHITECTURE
              </span>
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center space-x-1">
                <Zap className="w-3 h-3" />
                <span>P50 / P95 / P99 Profiling Engine</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <Gauge className="w-7 h-7 text-amber-400" />
              <span>High-Scale Performance Center</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Empirical latency baselines, cost-aware AI model routing, cursor pagination, and vector scope partitioning.
            </p>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center space-x-2 bg-slate-950 p-1.5 rounded-2xl border border-slate-800 flex-shrink-0">
            <button
              type="button"
              onClick={() => setActiveTab('BASELINES')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'BASELINES' ? 'bg-amber-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Baselines
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('AI_ROUTING')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'AI_ROUTING' ? 'bg-amber-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              AI Cost Routing
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('QUERY_OPT')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'QUERY_OPT' ? 'bg-amber-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Query Optimizer
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('CAPACITY')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'CAPACITY' ? 'bg-amber-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Capacity & Cost
            </button>
          </div>
        </div>

        {/* Telemetry Metrics Bar */}
        {baselines && capacity && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 border-t border-slate-800/60">
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Search P50 Latency</span>
              <span className="text-lg font-black text-emerald-400">{baselines.p50_ms.universal_search} ms</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Search P95 Latency</span>
              <span className="text-lg font-black text-amber-400">{baselines.p95_ms.universal_search} ms</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">AI First Token (P50)</span>
              <span className="text-lg font-black text-indigo-400">{baselines.p50_ms.ai_first_token} ms</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Cost Efficiency Score</span>
              <span className="text-lg font-black text-cyan-400">{capacity.cost_telemetry.cost_efficiency_score}</span>
            </div>
          </div>
        )}
      </div>

      {actionMessage && (
        <div className="p-3 bg-amber-950/80 border border-amber-800/60 rounded-2xl text-xs text-amber-200 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-amber-400" />
            <span>{actionMessage}</span>
          </div>
          <button type="button" onClick={() => setActionMessage(null)} className="text-[10px] text-slate-400 hover:text-white font-mono">Dismiss</button>
        </div>
      )}

      {/* Tab Views */}
      {activeTab === 'BASELINES' && baselines && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-white uppercase font-mono">Empirical Journey Latency Profiles</h3>
              <p className="text-xs text-slate-400 mt-1">Real P50, P95, and P99 latency distribution across key user journeys.</p>
            </div>
            <span className="text-[9px] font-mono text-amber-400 bg-amber-950 px-2 py-0.5 rounded border border-amber-800/60 font-bold">{baselines.provenance_label}</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2">
              <span className="font-bold text-emerald-400 block font-mono uppercase">P50 Latencies</span>
              <p className="text-slate-300">• Universal Search: <strong className="text-white">{baselines.p50_ms.universal_search} ms</strong></p>
              <p className="text-slate-300">• Message History: <strong className="text-white">{baselines.p50_ms.message_history_load} ms</strong></p>
              <p className="text-slate-300">• Project Workspace: <strong className="text-white">{baselines.p50_ms.project_workspace_open} ms</strong></p>
              <p className="text-slate-300">• AI First Token: <strong className="text-white">{baselines.p50_ms.ai_first_token} ms</strong></p>
            </div>

            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2">
              <span className="font-bold text-amber-400 block font-mono uppercase">P95 Latencies</span>
              <p className="text-slate-300">• Universal Search: <strong className="text-white">{baselines.p95_ms.universal_search} ms</strong></p>
              <p className="text-slate-300">• Message History: <strong className="text-white">{baselines.p95_ms.message_history_load} ms</strong></p>
              <p className="text-slate-300">• Project Workspace: <strong className="text-white">{baselines.p95_ms.project_workspace_open} ms</strong></p>
              <p className="text-slate-300">• AI First Token: <strong className="text-white">{baselines.p95_ms.ai_first_token} ms</strong></p>
            </div>

            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2">
              <span className="font-bold text-red-400 block font-mono uppercase">P99 Latencies</span>
              <p className="text-slate-300">• Universal Search: <strong className="text-white">{baselines.p99_ms.universal_search} ms</strong></p>
              <p className="text-slate-300">• Message History: <strong className="text-white">{baselines.p99_ms.message_history_load} ms</strong></p>
              <p className="text-slate-300">• Project Workspace: <strong className="text-white">{baselines.p99_ms.project_workspace_open} ms</strong></p>
              <p className="text-slate-300">• AI First Token: <strong className="text-white">{baselines.p99_ms.ai_first_token} ms</strong></p>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'AI_ROUTING' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Cost-Aware AI Model Routing & Context Compression</h3>
            <p className="text-xs text-slate-400 mt-1">Routes simple tasks to fast low-cost models and complex tasks to deep multi-agent paths.</p>
          </div>

          <div className="flex items-center space-x-3">
            <button
              type="button"
              onClick={() => handleTestAIRouting('SIMPLE')}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-xl text-white font-bold text-xs"
            >
              Test Simple Task Routing (Small Model)
            </button>
            <button
              type="button"
              onClick={() => handleTestAIRouting('COMPLEX')}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-white font-bold text-xs"
            >
              Test Complex Task Routing (Deep Reasoning)
            </button>
          </div>

          {aiRouteResult && (
            <div className="p-5 bg-slate-950 border border-slate-800 rounded-3xl space-y-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-bold text-white text-sm">Model Selected: {aiRouteResult.selected_model}</span>
                <span className="text-[9px] font-mono font-bold bg-amber-950 text-amber-400 px-2 py-0.5 rounded border border-amber-800/60 uppercase">{aiRouteResult.routing_path}</span>
              </div>

              <div className="p-3 bg-slate-900 rounded-2xl space-y-1">
                <p className="text-slate-300">• <strong className="text-emerald-400">Tokens Saved:</strong> {aiRouteResult.tokens_saved}</p>
                <p className="text-slate-300">• <strong className="text-emerald-400">Estimated Cost:</strong> {aiRouteResult.estimated_cost}</p>
                <p className="text-slate-300">• <strong className="text-emerald-400">First Token Latency:</strong> {aiRouteResult.first_token_latency_ms} ms</p>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'QUERY_OPT' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-white uppercase font-mono">Query Plan Optimizer & Cursor Pagination Inspector</h3>
              <p className="text-xs text-slate-400 mt-1">Replaces deep OFFSET queries with high-scale cursor pagination and eliminates N+1 patterns.</p>
            </div>
            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={handleTestQueryOpt}
                className="px-4 py-2 bg-amber-600 hover:bg-amber-500 rounded-xl text-white font-bold text-xs"
              >
                Test Cursor Pagination
              </button>
              <button
                type="button"
                onClick={handleTestBatchEmbeddings}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-xl text-slate-300 font-bold text-xs"
              >
                Test Batch Embeddings
              </button>
            </div>
          </div>

          {queryOptResult && (
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2 text-xs">
              <span className="font-bold text-emerald-400 block font-mono">Strategy: {queryOptResult.optimization_strategy}</span>
              <p className="text-slate-300">• <strong className="text-slate-100">Execution Time:</strong> {queryOptResult.execution_time_ms} ms</p>
              <p className="text-slate-300">• <strong className="text-slate-100">N+1 Queries Prevented:</strong> {queryOptResult.n_plus_one_queries_prevented}</p>
              <p className="text-slate-300">• <strong className="text-slate-100">Next Cursor:</strong> {queryOptResult.next_cursor}</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'CAPACITY' && capacity && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Capacity Planning & Multi-Instance Leader Election</h3>
            <p className="text-xs text-slate-400 mt-1">Infrastructure thresholds, distributed lock coordination, and tenant cost telemetry.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2">
              <span className="font-bold text-cyan-400 block font-mono uppercase">Capacity Limits</span>
              <p className="text-slate-300">• Max Concurrent Users: <strong className="text-white">{capacity.capacity_limits.max_supported_concurrent_users.toLocaleString()}</strong></p>
              <p className="text-slate-300">• Max Concurrent AI Jobs: <strong className="text-white">{capacity.capacity_limits.max_concurrent_ai_jobs.toLocaleString()}</strong></p>
              <p className="text-slate-300">• Daily File Ingestions: <strong className="text-white">{capacity.capacity_limits.max_daily_file_ingestions.toLocaleString()}</strong></p>
              <p className="text-slate-300">• Storage Headroom: <strong className="text-white">{capacity.capacity_limits.storage_growth_headroom}</strong></p>
            </div>

            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2">
              <span className="font-bold text-amber-400 block font-mono uppercase">Cost & Coordination</span>
              <p className="text-slate-300">• Distributed Leader Lock: <strong className="text-white">{capacity.multi_instance_leader_election.coordination_mechanism}</strong></p>
              <p className="text-slate-300">• Current Month AI Cost: <strong className="text-white">{capacity.cost_telemetry.current_month_ai_cost}</strong></p>
              <p className="text-slate-300">• Monthly Budget Limit: <strong className="text-white">{capacity.cost_telemetry.budget_limit}</strong></p>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
