import React, { useState, useEffect } from 'react';
import {
  fetchGovernanceQueue, approveVersion, rejectVersion, resolveConflict, fetchGovernanceAuditLog,
  GovernanceQueueItem, GovernanceAuditItem
} from '../knowledge-governance-api';
import {
  ShieldCheck, CheckCircle2, XCircle, AlertTriangle, Clock, History, FileCheck, Lock, RefreshCw, UserCheck, Layers, Check, ArrowRight
} from 'lucide-react';

interface KnowledgeGovernanceDashboardProps {
  token?: string;
}

export const KnowledgeGovernanceDashboard: React.FC<KnowledgeGovernanceDashboardProps> = ({ token }) => {
  const [queue, setQueue] = useState<GovernanceQueueItem[]>([]);
  const [auditLog, setAuditLog] = useState<GovernanceAuditItem[]>([]);
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [qRes, aRes] = await Promise.all([
        fetchGovernanceQueue(filterStatus, token),
        fetchGovernanceAuditLog(undefined, token)
      ]);
      setQueue(qRes);
      setAuditLog(aRes);
    } catch (err) {
      console.error('Failed to load governance dashboard:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filterStatus, token]);

  const handleApprove = async (entityId: string, version: string) => {
    try {
      const res = await approveVersion(entityId, version, token);
      setActionMessage(res.message);
      loadData();
    } catch (err) {
      console.error('Failed approval:', err);
    }
  };

  const handleReject = async (entityId: string) => {
    try {
      const res = await rejectVersion(entityId, 'Inconsistent with governed policy', token);
      setActionMessage(res.message);
      loadData();
    } catch (err) {
      console.error('Failed rejection:', err);
    }
  };

  const handleResolveConflict = async () => {
    try {
      const res = await resolveConflict(
        'conflict-101',
        'CURRENT_DECISION_OVERRIDE',
        'dec-jwt-30m',
        'doc-auth-v1',
        token
      );
      setActionMessage(res.message);
      loadData();
    } catch (err) {
      console.error('Failed conflict resolution:', err);
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
                KNOWLEDGE GOVERNANCE & TRUST LAYER
              </span>
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center space-x-1">
                <Lock className="w-3 h-3" />
                <span>Immutable Audit & Human Approval Boundary</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <ShieldCheck className="w-7 h-7 text-indigo-400" />
              <span>Governance Review Queue</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Distinguishes trusted governed truth from derived AI information, supersedes old versions, and audits all decisions.
            </p>
          </div>

          <button
            type="button"
            onClick={() => handleResolveConflict()}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-2xl text-white font-bold text-xs shadow-lg transition-all flex items-center space-x-1.5 flex-shrink-0"
          >
            <AlertTriangle className="w-4 h-4 text-amber-300" />
            <span>Resolve Open Conflict</span>
          </button>
        </div>
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

      {/* Main Grid: Left 2 Cols Queue, Right 1 Col Audit Log */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Left 2 Cols: Queue */}
        <div className="md:col-span-2 space-y-4">
          
          <div className="flex items-center justify-between bg-slate-900/80 border border-slate-800 p-3 rounded-2xl">
            <div className="flex items-center space-x-2">
              <FileCheck className="w-4 h-4 text-indigo-400" />
              <span className="text-xs font-bold text-slate-300">Filter Queue:</span>
              {['ALL', 'UNDER_REVIEW', 'APPROVED', 'SUPERSEDED'].map((st) => (
                <button
                  key={st}
                  type="button"
                  onClick={() => setFilterStatus(st)}
                  className={`px-3 py-1 rounded-xl text-xs font-bold transition-all ${
                    filterStatus === st ? 'bg-indigo-600 text-white' : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
                  }`}
                >
                  {st}
                </button>
              ))}
            </div>
            <button type="button" onClick={() => loadData()} className="p-1.5 bg-slate-950 hover:bg-slate-800 border border-slate-800 rounded-xl text-slate-400 hover:text-white">
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>

          <div className="space-y-3">
            {queue.map((item) => (
              <div key={item.entity_id} className="bg-slate-900/80 border border-slate-800 p-4 rounded-3xl shadow-xl space-y-3 backdrop-blur-md">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-[9px] font-mono font-bold text-indigo-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">{item.entity_type}</span>
                    <span className="text-[9px] font-mono text-slate-400 bg-slate-950 px-1.5 py-0.5 rounded">{item.version}</span>
                    <h3 className="text-xs font-bold text-white">{item.title}</h3>
                  </div>

                  <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded border ${
                    item.trust_label === 'Approved' ? 'bg-emerald-950 text-emerald-400 border-emerald-800/60' :
                    item.trust_label === 'Needs Review' ? 'bg-amber-950 text-amber-400 border-amber-800/60' : 'bg-slate-950 text-slate-400 border-slate-800'
                  }`}>
                    {item.trust_label}
                  </span>
                </div>

                <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
                  <span>Owner: {item.owner}</span>
                  <span>Reviewer: {item.reviewer}</span>
                </div>

                {item.status === 'UNDER_REVIEW' && (
                  <div className="flex items-center justify-end space-x-2 pt-2 border-t border-slate-800">
                    <button
                      type="button"
                      onClick={() => handleReject(item.entity_id)}
                      className="px-3 py-1.5 bg-red-950 hover:bg-red-900 border border-red-800/60 text-red-300 font-bold text-xs rounded-xl transition-all"
                    >
                      Reject
                    </button>
                    <button
                      type="button"
                      onClick={() => handleApprove(item.entity_id, item.version)}
                      className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-md transition-all"
                    >
                      Approve Version
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>

        </div>

        {/* Right Col: Immutable Audit Log */}
        <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-3xl shadow-xl space-y-3 backdrop-blur-md">
          <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
            <History className="w-4 h-4 text-indigo-400" />
            <h4 className="text-xs font-bold text-white">Immutable Audit Trail ({auditLog.length})</h4>
          </div>

          <div className="space-y-2 text-xs font-mono max-h-[500px] overflow-y-auto pr-1">
            {auditLog.length === 0 ? (
              <p className="text-slate-500 text-center py-4">No audit logs recorded yet.</p>
            ) : (
              auditLog.map((a) => (
                <div key={a.audit_id} className="p-2.5 bg-slate-950 border border-slate-800 rounded-xl space-y-1">
                  <div className="flex items-center justify-between text-[9px] text-indigo-400">
                    <span className="font-bold">{a.action}</span>
                    <span className="text-slate-500">{new Date(a.timestamp).toLocaleTimeString()}</span>
                  </div>
                  <p className="text-[10px] text-slate-300">{a.details || `State: ${a.previous_state} -> ${a.new_state}`}</p>
                </div>
              ))
            )}
          </div>
        </div>

      </div>

    </div>
  );
};
