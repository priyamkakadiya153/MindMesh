import React, { useState, useEffect } from 'react';
import {
  fetchDeepHealth, executeCircuitBreakerTest, manageBackgroundJob, replayDeadLetterJob, rebuildIndexes, fetchOperationsDashboard,
  DeepHealthResponse, OperationsDashboardResponse
} from '../production-operations-api';
import {
  Activity, Server, Database, Cpu, Zap, RefreshCw, AlertTriangle, ShieldCheck, Play, Layers, Radio, CheckCircle, Flame
} from 'lucide-react';

interface ProductionOperationsCenterProps {
  token?: string;
}

export const ProductionOperationsCenter: React.FC<ProductionOperationsCenterProps> = ({ token }) => {
  const [activeTab, setActiveTab] = useState<'SERVICES' | 'DEAD_LETTER' | 'CIRCUIT' | 'RECOVERY'>('SERVICES');
  const [deepHealth, setDeepHealth] = useState<DeepHealthResponse | null>(null);
  const [dashboard, setDashboard] = useState<OperationsDashboardResponse | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [healthRes, dashRes] = await Promise.all([
        fetchDeepHealth(token),
        fetchOperationsDashboard(token)
      ]);
      setDeepHealth(healthRes);
      setDashboard(dashRes);
    } catch (err) {
      console.error('Failed to load production operations center:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [token]);

  const handleSimulateFailure = async () => {
    try {
      const res = await executeCircuitBreakerTest('Gemini AI Provider', true, token);
      setActionMessage(res.message);
      loadData();
    } catch (err) {
      console.error('Failed CB failure test:', err);
    }
  };

  const handleSimulateDeadLetter = async () => {
    try {
      const res = await manageBackgroundJob('Vector Index Sync', `idemp-${Date.now()}`, true, token);
      setActionMessage(res.message);
      loadData();
    } catch (err) {
      console.error('Failed DLQ simulation:', err);
    }
  };

  const handleReplayJob = async (jobId: string) => {
    try {
      const res = await replayDeadLetterJob(jobId, token);
      setActionMessage(res.message);
      loadData();
    } catch (err) {
      console.error('Failed DLQ replay:', err);
    }
  };

  const handleRebuildIndexes = async () => {
    try {
      const res = await rebuildIndexes(token);
      setActionMessage(`${res.message} Reindexed ${res.documents_reindexed} documents & ${res.embeddings_reconstructed} vector embeddings.`);
      loadData();
    } catch (err) {
      console.error('Failed index rebuild:', err);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6 text-slate-100 font-sans select-none">
      
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-cyan-950/80 to-slate-900 border border-cyan-800/60 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-cyan-400 px-2.5 py-0.5 bg-cyan-950 rounded border border-cyan-800/60">
                RELIABILITY, OBSERVABILITY & PRODUCTION OPERATIONS
              </span>
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center space-x-1">
                <Activity className="w-3 h-3" />
                <span>Operational Health Engine</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <Server className="w-7 h-7 text-cyan-400" />
              <span>MindMesh Production Operations Center</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Real-time telemetry, deep health monitoring, circuit breaker recovery, dead-letter job replays, and index reconciliation.
            </p>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center space-x-2 bg-slate-950 p-1.5 rounded-2xl border border-slate-800 flex-shrink-0">
            <button
              type="button"
              onClick={() => setActiveTab('SERVICES')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'SERVICES' ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Services Grid
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('DEAD_LETTER')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'DEAD_LETTER' ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Dead-Letter Queue
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('CIRCUIT')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'CIRCUIT' ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Circuit Breakers
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('RECOVERY')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'RECOVERY' ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Index Recovery
            </button>
          </div>
        </div>

        {/* Operational Metrics Bar */}
        {dashboard && deepHealth && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 border-t border-slate-800/60">
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Overall Status</span>
              <span className="text-sm font-black text-emerald-400">{deepHealth.overall_status}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Circuit Breaker</span>
              <span className="text-sm font-black text-indigo-400">{dashboard.circuit_breaker.status}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">DLQ Jobs</span>
              <span className="text-sm font-black text-amber-400">{dashboard.dead_letter_queue_count}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Active Incidents</span>
              <span className="text-sm font-black text-rose-400">{dashboard.active_incidents.length}</span>
            </div>
          </div>
        )}
      </div>

      {actionMessage && (
        <div className="p-3 bg-cyan-950/80 border border-cyan-800/60 rounded-2xl text-xs text-cyan-200 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <CheckCircle className="w-4 h-4 text-cyan-400" />
            <span>{actionMessage}</span>
          </div>
          <button type="button" onClick={() => setActionMessage(null)} className="text-[10px] text-slate-400 hover:text-white font-mono">Dismiss</button>
        </div>
      )}

      {/* Tab Views */}
      {activeTab === 'SERVICES' && deepHealth && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Deep Dependency Health Grid</h3>
            <p className="text-xs text-slate-400 mt-1">Real-time status, latency metrics, and pool usage across all core MindMesh infrastructure services.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2 text-xs">
              <span className="font-bold text-cyan-400 block font-mono">PostgreSQL Primary</span>
              <span className="text-[10px] font-mono bg-emerald-950 text-emerald-400 px-2 py-0.5 rounded border border-emerald-800/60 font-bold">{deepHealth.services.postgresql.status}</span>
              <p className="text-slate-400">Latency: <strong className="text-slate-200">{deepHealth.services.postgresql.latency_ms} ms</strong></p>
              <p className="text-slate-400">Pool Usage: <strong className="text-slate-200">{deepHealth.services.postgresql.pool_usage}</strong></p>
            </div>

            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2 text-xs">
              <span className="font-bold text-red-400 block font-mono">Redis Memory Cache</span>
              <span className="text-[10px] font-mono bg-emerald-950 text-emerald-400 px-2 py-0.5 rounded border border-emerald-800/60 font-bold">{deepHealth.services.redis.status}</span>
              <p className="text-slate-400">Latency: <strong className="text-slate-200">{deepHealth.services.redis.latency_ms} ms</strong></p>
              <p className="text-slate-400">Memory: <strong className="text-slate-200">{deepHealth.services.redis.memory_usage}</strong></p>
            </div>

            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2 text-xs">
              <span className="font-bold text-indigo-400 block font-mono">ChromaDB Vector DB</span>
              <span className="text-[10px] font-mono bg-emerald-950 text-emerald-400 px-2 py-0.5 rounded border border-emerald-800/60 font-bold">{deepHealth.services.chromadb.status}</span>
              <p className="text-slate-400">Latency: <strong className="text-slate-200">{deepHealth.services.chromadb.latency_ms} ms</strong></p>
              <p className="text-slate-400">Vectors: <strong className="text-slate-200">{deepHealth.services.chromadb.vector_count}</strong></p>
            </div>

            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2 text-xs">
              <span className="font-bold text-amber-400 block font-mono">AI Provider Engine</span>
              <span className="text-[10px] font-mono bg-emerald-950 text-emerald-400 px-2 py-0.5 rounded border border-emerald-800/60 font-bold">{deepHealth.services.ai_providers.status}</span>
              <p className="text-slate-400">Circuit Breaker: <strong className="text-slate-200">{deepHealth.services.ai_providers.circuit_breaker}</strong></p>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'DEAD_LETTER' && dashboard && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-white uppercase font-mono">Dead-Letter Queue Inspector & Idempotent Replay</h3>
              <p className="text-xs text-slate-400 mt-1">Failed background jobs that exceeded maximum retries. Supports safe replay.</p>
            </div>
            <button
              type="button"
              onClick={handleSimulateDeadLetter}
              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-xl text-slate-300 font-bold text-xs font-mono"
            >
              Simulate DLQ Failure
            </button>
          </div>

          <div className="space-y-3">
            {dashboard.dead_letter_jobs.map(job => (
              <div key={job.job_id} className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2 text-xs flex items-center justify-between">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-white">{job.job_type}</span>
                    <span className="text-[9px] font-mono bg-red-950 text-red-400 px-2 py-0.5 rounded border border-red-800/60 font-bold">{job.status}</span>
                  </div>
                  <p className="text-slate-400 mt-1">• <strong className="text-slate-200">Job ID:</strong> {job.job_id} | <strong className="text-slate-200">Attempts:</strong> {job.attempts}/{job.max_attempts}</p>
                  <p className="text-rose-300 font-mono text-[10px] mt-0.5">Error: {job.last_error}</p>
                </div>
                {job.status === 'DEAD_LETTER' && (
                  <button
                    type="button"
                    onClick={() => handleReplayJob(job.job_id)}
                    className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 rounded-xl text-white font-bold text-xs flex items-center space-x-1"
                  >
                    <Play className="w-3 h-3" />
                    <span>Replay Job</span>
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'CIRCUIT' && dashboard && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-white uppercase font-mono">Circuit Breaker & Exponential Backoff Monitor</h3>
              <p className="text-xs text-slate-400 mt-1">Prevents cascading failures by opening circuit breaker during consecutive dependency failures.</p>
            </div>
            <button
              type="button"
              onClick={handleSimulateFailure}
              className="px-4 py-2 bg-amber-600 hover:bg-amber-500 rounded-2xl text-white font-bold text-xs shadow-lg"
            >
              Simulate AI Failure
            </button>
          </div>

          <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2 text-xs">
            <span className="font-bold text-white block font-mono">Circuit Breaker Status: {dashboard.circuit_breaker.status}</span>
            <p className="text-slate-300">• <strong className="text-slate-100">Consecutive Failures:</strong> {dashboard.circuit_breaker.failure_count}</p>
            <p className="text-slate-300">• <strong className="text-slate-100">Cooldown Period:</strong> {dashboard.circuit_breaker.cooldown_seconds} seconds</p>
          </div>
        </div>
      )}

      {activeTab === 'RECOVERY' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-white uppercase font-mono">Authoritative Index Rebuild & Data Reconciliation</h3>
              <p className="text-xs text-slate-400 mt-1">PostgreSQL remains the authoritative source of truth. Reconstruct vector embeddings & search indices post-outage.</p>
            </div>
            <button
              type="button"
              onClick={handleRebuildIndexes}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-2xl text-white font-bold text-xs shadow-lg flex items-center space-x-1.5"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Rebuild Authoritative Indexes</span>
            </button>
          </div>
        </div>
      )}

    </div>
  );
};
