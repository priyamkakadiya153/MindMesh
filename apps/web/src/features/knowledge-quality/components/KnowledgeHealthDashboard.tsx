import React, { useState, useEffect } from 'react';
import {
  fetchQualityIssues, runQualityScan, resolveQualityIssue, assignOwner, keepSeparate, fetchKnowledgeHealth,
  QualityIssueItem, KnowledgeHealthResponse
} from '../knowledge-quality-api';
import {
  HeartPulse, ShieldAlert, AlertTriangle, CheckCircle2, UserPlus, Layers, RefreshCw, Filter, Check, ArrowRight, Sparkles, CopyX, Link2Off
} from 'lucide-react';

interface KnowledgeHealthDashboardProps {
  token?: string;
}

export const KnowledgeHealthDashboard: React.FC<KnowledgeHealthDashboardProps> = ({ token }) => {
  const [issues, setIssues] = useState<QualityIssueItem[]>([]);
  const [health, setHealth] = useState<KnowledgeHealthResponse | null>(null);
  const [filterType, setFilterType] = useState<string>('ALL');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [issRes, hlthRes] = await Promise.all([
        fetchQualityIssues(filterType, token),
        fetchKnowledgeHealth(token)
      ]);
      setIssues(issRes);
      setHealth(hlthRes);
    } catch (err) {
      console.error('Failed to load quality dashboard:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filterType, token]);

  const handleScan = async () => {
    setIsLoading(true);
    try {
      const res = await runQualityScan(undefined, token);
      setActionMessage(`Read-only quality scan complete. Checked ${res.items_checked} items.`);
      loadData();
    } catch (err) {
      console.error('Failed scan:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResolve = async (issueId: string) => {
    try {
      const res = await resolveQualityIssue(issueId, token);
      setActionMessage(res.message);
      loadData();
    } catch (err) {
      console.error('Failed resolve:', err);
    }
  };

  const handleAssignOwner = async (entityId: string) => {
    try {
      const res = await assignOwner(entityId, 'Priyam User', token);
      setActionMessage(res.message);
      loadData();
    } catch (err) {
      console.error('Failed assign owner:', err);
    }
  };

  const handleKeepSeparate = async (issueId: string) => {
    try {
      const res = await keepSeparate(issueId, token);
      setActionMessage(res.message);
      loadData();
    } catch (err) {
      console.error('Failed keep separate:', err);
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
                KNOWLEDGE STEWARDSHIP & HEALTH
              </span>
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center space-x-1">
                <CheckCircle2 className="w-3 h-3" />
                <span>Observable Signals & Non-Destructive Maintenance</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <HeartPulse className="w-7 h-7 text-indigo-400" />
              <span>Knowledge Health Dashboard</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Continuously evaluates organizational knowledge freshness, missing ownership, duplicate candidates, and orphans without destructive auto-deletion.
            </p>
          </div>

          <button
            type="button"
            onClick={() => handleScan()}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-2xl text-white font-bold text-xs shadow-lg transition-all flex items-center space-x-1.5 flex-shrink-0"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Run Quality Scan</span>
          </button>
        </div>

        {/* Health Counters Bar */}
        {health && (
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-2 border-t border-slate-800/60">
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Attention Needed</span>
              <span className="text-lg font-black text-white">{health.needs_attention_count}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Stale Knowledge</span>
              <span className="text-lg font-black text-amber-400">{health.stale_count}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Duplicates</span>
              <span className="text-lg font-black text-indigo-400">{health.duplicate_count}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Missing Owner</span>
              <span className="text-lg font-black text-red-400">{health.missing_owner_count}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Orphans</span>
              <span className="text-lg font-black text-slate-400">{health.orphan_count}</span>
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

      {/* Filter Toolbar */}
      <div className="flex items-center justify-between bg-slate-900/80 border border-slate-800 p-3 rounded-2xl backdrop-blur-md">
        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-indigo-400" />
          <span className="text-xs font-bold text-slate-300">Filter Issues:</span>
          {['ALL', 'STALE', 'MISSING_OWNER', 'DUPLICATE_CANDIDATE', 'ORPHAN'].map((st) => (
            <button
              key={st}
              type="button"
              onClick={() => setFilterType(st)}
              className={`px-3 py-1 rounded-xl text-xs font-bold transition-all ${
                filterType === st ? 'bg-indigo-600 text-white' : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Issue Cards */}
      <div className="space-y-4">
        {issues.map((iss) => (
          <div key={iss.issue_id} className="bg-slate-900/80 border border-slate-800 p-5 rounded-3xl shadow-xl space-y-3 backdrop-blur-md">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${
                  iss.severity === 'IMPORTANT' ? 'bg-amber-950 text-amber-400 border-amber-800/60' :
                  iss.severity === 'ATTENTION' ? 'bg-red-950 text-red-400 border-red-800/60' : 'bg-indigo-950 text-indigo-400 border-indigo-800/60'
                }`}>
                  {iss.severity} • {iss.type}
                </span>
                <h3 className="text-xs font-bold text-white">{iss.title}</h3>
              </div>

              <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded border ${
                iss.status === 'RESOLVED' ? 'bg-emerald-950 text-emerald-400 border-emerald-800/60' : 'bg-slate-950 text-slate-400 border-slate-800'
              }`}>
                {iss.status}
              </span>
            </div>

            <p className="text-xs text-slate-300 font-medium">{iss.reason}</p>

            {/* Evidence List */}
            <div className="p-3 bg-slate-950 border border-slate-800 rounded-2xl space-y-1 text-xs">
              <span className="text-[9px] font-mono text-indigo-400 uppercase font-bold">Observable Evidence</span>
              {iss.evidence.map((ev, i) => (
                <p key={i} className="text-[11px] text-slate-300">• {ev}</p>
              ))}
            </div>

            {/* Maintenance Action Buttons */}
            {iss.status === 'OPEN' && (
              <div className="flex items-center justify-end space-x-2 pt-2 border-t border-slate-800">
                {iss.type === 'MISSING_OWNER' && (
                  <button
                    type="button"
                    onClick={() => handleAssignOwner(iss.entity_id)}
                    className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-white font-bold text-xs flex items-center space-x-1"
                  >
                    <UserPlus className="w-3 h-3" />
                    <span>Assign Owner</span>
                  </button>
                )}

                {iss.type === 'DUPLICATE_CANDIDATE' && (
                  <button
                    type="button"
                    onClick={() => handleKeepSeparate(iss.issue_id)}
                    className="px-3 py-1.5 bg-slate-950 hover:bg-slate-800 border border-slate-800 rounded-xl text-slate-300 font-bold text-xs flex items-center space-x-1"
                  >
                    <CopyX className="w-3 h-3" />
                    <span>Keep Separate</span>
                  </button>
                )}

                <button
                  type="button"
                  onClick={() => handleResolve(iss.issue_id)}
                  className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 rounded-xl text-white font-bold text-xs flex items-center space-x-1"
                >
                  <Check className="w-3 h-3" />
                  <span>Resolve Issue</span>
                </button>
              </div>
            )}
          </div>
        ))}
      </div>

    </div>
  );
};
