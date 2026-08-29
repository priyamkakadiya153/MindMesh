import React, { useState, useEffect, useCallback } from 'react';
import {
  fetchReviewQueue, fetchGovernanceAuditTrail, verifyKnowledge, archiveKnowledge,
  restoreKnowledge, ReviewQueueItem, AuditLogItem
} from '../governance-api';
import {
  ShieldCheck, CheckCircle2, AlertTriangle, Clock, Archive, RefreshCw,
  Loader2, History, AlertCircle, Sparkles, User, FileText, CheckSquare
} from 'lucide-react';

interface KnowledgeGovernanceCenterProps {
  workspaceId?: string;
  token?: string;
}

export const KnowledgeGovernanceCenter: React.FC<KnowledgeGovernanceCenterProps> = ({
  workspaceId,
  token
}) => {
  const [reviewItems, setReviewItems] = useState<ReviewQueueItem[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'review' | 'audit'>('review');

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [items, logs] = await Promise.all([
        fetchReviewQueue(workspaceId, token),
        fetchGovernanceAuditTrail(token)
      ]);
      setReviewItems(items);
      setAuditLogs(logs);
    } catch (err) {
      console.error('Failed to load governance data:', err);
    } finally {
      setIsLoading(false);
    }
  }, [workspaceId, token]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleVerify = async (item: ReviewQueueItem) => {
    try {
      await verifyKnowledge(item.entity_type, item.entity_id, token);
      setReviewItems((prev) => prev.filter((i) => i.id !== item.id));
      loadData();
    } catch (err) {
      console.error('Failed to verify item:', err);
    }
  };

  const handleArchive = async (item: ReviewQueueItem) => {
    try {
      await archiveKnowledge(item.entity_type, item.entity_id, token);
      setReviewItems((prev) => prev.filter((i) => i.id !== item.id));
      loadData();
    } catch (err) {
      console.error('Failed to archive item:', err);
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-slate-400 space-y-3">
        <Loader2 className="w-7 h-7 animate-spin text-indigo-400" />
        <span className="text-xs font-medium">Scanning knowledge governance state...</span>
      </div>
    );
  }

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6 text-slate-100 select-none">
      
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/60 to-slate-900 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-indigo-400 px-2 py-0.5 bg-indigo-950 rounded border border-indigo-800/60">
              KNOWLEDGE GOVERNANCE & TRUST
            </span>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <ShieldCheck className="w-7 h-7 text-indigo-400" />
              <span>Knowledge Governance Center</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Control knowledge lifecycle states, verify AI-extracted decisions, inspect immutable audit trails, and maintain organizational memory integrity.
            </p>
          </div>

          <button
            type="button"
            onClick={loadData}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors shrink-0 self-start md:self-auto"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        {/* Governance Metrics */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
          <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-2xl">
            <span className="text-[10px] text-slate-500 font-medium block">Needs Review</span>
            <h4 className="text-lg font-bold text-amber-400">{reviewItems.length}</h4>
          </div>

          <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-2xl">
            <span className="text-[10px] text-slate-500 font-medium block">Audit Trail Actions</span>
            <h4 className="text-lg font-bold text-indigo-400">{auditLogs.length}</h4>
          </div>

          <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-2xl">
            <span className="text-[10px] text-slate-500 font-medium block">Human Verified</span>
            <h4 className="text-lg font-bold text-emerald-400">
              {auditLogs.filter((l) => l.action === 'VERIFY').length}
            </h4>
          </div>

          <div className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-2xl">
            <span className="text-[10px] text-slate-500 font-medium block">Superseded</span>
            <h4 className="text-lg font-bold text-slate-400">
              {auditLogs.filter((l) => l.action === 'SUPERSEDE').length}
            </h4>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
        <button
          type="button"
          onClick={() => setActiveTab('review')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-2 ${
            activeTab === 'review'
              ? 'bg-indigo-600 text-white shadow-md'
              : 'bg-slate-900/60 text-slate-400 hover:text-white border border-slate-800'
          }`}
        >
          <AlertCircle className="w-4 h-4" />
          <span>Review Queue ({reviewItems.length})</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('audit')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-2 ${
            activeTab === 'audit'
              ? 'bg-indigo-600 text-white shadow-md'
              : 'bg-slate-900/60 text-slate-400 hover:text-white border border-slate-800'
          }`}
        >
          <History className="w-4 h-4" />
          <span>Audit History ({auditLogs.length})</span>
        </button>
      </div>

      {/* Review Queue Tab Content */}
      {activeTab === 'review' && (
        <div className="space-y-3">
          {reviewItems.length === 0 ? (
            <div className="bg-slate-900/40 border border-slate-800/80 p-8 rounded-3xl text-center space-y-1">
              <CheckCircle2 className="w-6 h-6 text-emerald-400 mx-auto" />
              <h4 className="text-xs font-bold text-slate-300">All knowledge verified</h4>
              <p className="text-[11px] text-slate-500">No items currently require human review.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {reviewItems.map((item) => (
                <div key={item.id} className="bg-slate-900/70 border border-slate-800 p-5 rounded-3xl space-y-3 shadow-md">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className="text-[9px] font-mono font-bold uppercase text-amber-400 px-2 py-0.5 bg-amber-950/60 rounded border border-amber-800/60">
                        {item.entity_type}
                      </span>
                      <h4 className="text-xs font-bold text-slate-100 mt-1">{item.title}</h4>
                    </div>

                    <span className="text-[9px] font-mono font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 uppercase">
                      {item.verification_state}
                    </span>
                  </div>

                  <p className="text-xs text-slate-200 bg-slate-950/70 p-3 rounded-2xl border border-slate-800 font-medium">
                    "{item.summary}"
                  </p>

                  <div className="text-[10px] text-slate-400 bg-amber-950/20 border border-amber-500/20 p-2.5 rounded-xl flex items-start space-x-1.5">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                    <span>{item.reason}</span>
                  </div>

                  <div className="flex items-center justify-end space-x-2 pt-1">
                    <button
                      type="button"
                      onClick={() => handleArchive(item)}
                      className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-xs font-semibold transition-all"
                    >
                      Archive
                    </button>

                    <button
                      type="button"
                      onClick={() => handleVerify(item)}
                      className="px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-md transition-all flex items-center space-x-1"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Human Verify</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Audit History Tab Content */}
      {activeTab === 'audit' && (
        <div className="bg-slate-900/70 border border-slate-800 p-5 rounded-3xl space-y-3 shadow-md">
          {auditLogs.length === 0 ? (
            <p className="text-xs text-slate-500 py-6 text-center">No governance audit records logged yet.</p>
          ) : (
            <div className="space-y-2.5 max-h-[450px] overflow-y-auto pr-1">
              {auditLogs.map((log) => (
                <div key={log.id} className="p-3.5 bg-slate-950/70 border border-slate-800/80 rounded-2xl flex items-center justify-between text-xs">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="text-[9px] font-mono font-bold uppercase px-2 py-0.5 bg-indigo-950 text-indigo-300 rounded border border-indigo-800/60">
                        {log.action}
                      </span>
                      <span className="text-xs font-bold text-slate-200">{log.entity_type}</span>
                    </div>
                    <p className="text-[11px] text-slate-400">{log.details}</p>
                  </div>

                  <div className="text-right">
                    <span className="text-[10px] text-slate-500 font-mono block">{log.created_at ? log.created_at.slice(0, 10) : ''}</span>
                    <span className="text-[9px] font-mono text-emerald-400 font-bold">{log.new_state}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

    </div>
  );
};
