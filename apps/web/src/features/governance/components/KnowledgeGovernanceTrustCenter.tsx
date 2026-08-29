import React, { useState, useEffect } from 'react';
import {
  fetchGovernanceReviewQueue, confirmExtraction, rejectExtraction, resolveConflict, setSourceOfTruth, fetchGovernanceAuditLog,
  GovernanceReviewQueueResponse, AuditLogItem
} from '../governance-trust-api';
import {
  ShieldCheck, AlertOctagon, CheckCircle2, XCircle, Award, History, GitCompare, ExternalLink, HelpCircle, FileText
} from 'lucide-react';

interface KnowledgeGovernanceTrustCenterProps {
  workspaceId?: string;
  projectId?: string;
  token?: string;
}

export const KnowledgeGovernanceTrustCenter: React.FC<KnowledgeGovernanceTrustCenterProps> = ({
  workspaceId,
  projectId,
  token
}) => {
  const [data, setData] = useState<GovernanceReviewQueueResponse | null>(null);
  const [auditLog, setAuditLog] = useState<AuditLogItem[]>([]);
  const [activeTab, setActiveTab] = useState<'REVIEW' | 'CONFLICTS' | 'AUDIT'>('REVIEW');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [qRes, aRes] = await Promise.all([
        fetchGovernanceReviewQueue(workspaceId, projectId, token),
        fetchGovernanceAuditLog(token)
      ]);
      setData(qRes);
      setAuditLog(aRes);
    } catch (err) {
      console.error('Failed to load governance data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [workspaceId, projectId, token]);

  const handleConfirm = async (itemId: string) => {
    try {
      await confirmExtraction(itemId, undefined, undefined, token);
      loadData();
    } catch (err) {
      console.error('Failed to confirm item:', err);
    }
  };

  const handleReject = async (itemId: string) => {
    try {
      await rejectExtraction(itemId, 'Rejected by user review.', token);
      loadData();
    } catch (err) {
      console.error('Failed to reject item:', err);
    }
  };

  const handleResolveConflict = async (conflictId: string, winningSourceId: string) => {
    try {
      await resolveConflict(conflictId, winningSourceId, 'Resolved via Governance Trust Center', token);
      loadData();
    } catch (err) {
      console.error('Failed to resolve conflict:', err);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6 text-slate-100 font-sans select-none">
      
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/70 to-slate-900 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-emerald-400 px-2 py-0.5 bg-emerald-950 rounded border border-emerald-800/60">
              KNOWLEDGE GOVERNANCE & TRUST LAYER
            </span>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <ShieldCheck className="w-7 h-7 text-emerald-400" />
              <span>Governance & Trust Center</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Ensures organizational knowledge remains trustworthy, current, reviewable, and explainable with human-in-the-loop verification and conflict resolution.
            </p>
          </div>

          {/* Key Stat Cards */}
          <div className="flex items-center space-x-3">
            <div className="bg-slate-950/80 p-3 rounded-2xl border border-slate-800 text-center min-w-[100px]">
              <span className="text-[10px] font-mono text-slate-400 block">Needs Review</span>
              <span className="text-lg font-black text-amber-400">{data?.total_review_items || 0}</span>
            </div>
            <div className="bg-slate-950/80 p-3 rounded-2xl border border-slate-800 text-center min-w-[100px]">
              <span className="text-[10px] font-mono text-slate-400 block">Conflicts</span>
              <span className="text-lg font-black text-rose-400">{data?.total_conflicts || 0}</span>
            </div>
          </div>
        </div>

        {/* Tab Selection */}
        <div className="flex gap-2 pt-2 border-t border-slate-800/80">
          <button
            type="button"
            onClick={() => setActiveTab('REVIEW')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-1.5 ${
              activeTab === 'REVIEW' ? 'bg-emerald-600 text-white shadow-md' : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
            }`}
          >
            <CheckCircle2 className="w-4 h-4" />
            <span>Needs Review Queue ({data?.total_review_items || 0})</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('CONFLICTS')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-1.5 ${
              activeTab === 'CONFLICTS' ? 'bg-rose-600 text-white shadow-md' : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
            }`}
          >
            <AlertOctagon className="w-4 h-4" />
            <span>Active Conflicts ({data?.total_conflicts || 0})</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('AUDIT')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-1.5 ${
              activeTab === 'AUDIT' ? 'bg-indigo-600 text-white shadow-md' : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
            }`}
          >
            <History className="w-4 h-4" />
            <span>Governance Audit Trail ({auditLog.length})</span>
          </button>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'REVIEW' && (
        <div className="space-y-3">
          {!data || data.review_queue.length === 0 ? (
            <div className="py-16 text-center space-y-2 bg-slate-900/40 border border-slate-800/60 rounded-3xl">
              <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto" />
              <h4 className="text-xs font-bold text-slate-300">All AI extractions have been reviewed</h4>
              <p className="text-[11px] text-slate-500">MindMesh knowledge base is 100% verified and current.</p>
            </div>
          ) : (
            data.review_queue.map((item) => (
              <div key={item.id} className="p-5 bg-slate-900/80 border border-slate-800 rounded-3xl space-y-3 shadow-lg">
                <div className="flex items-center justify-between">
                  <span className="text-[9px] font-mono font-bold text-amber-400 bg-amber-950 px-2 py-0.5 rounded border border-amber-800/60 uppercase">
                    AI Extraction ({item.entity_type})
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono">Source: {item.source_type}</span>
                </div>

                <div>
                  <h3 className="text-sm font-bold text-slate-100">{item.title}</h3>
                  <p className="text-xs text-slate-300 mt-1">{item.description}</p>
                </div>

                <div className="p-2.5 bg-slate-950/80 rounded-xl border border-slate-800 text-[11px] text-slate-400 italic">
                  <span>Why is this here? {item.reason}</span>
                </div>

                <div className="flex justify-end space-x-2 pt-2">
                  <button
                    type="button"
                    onClick={() => handleReject(item.id)}
                    className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-rose-950 text-rose-400 hover:border-rose-800/60 font-bold text-xs border border-slate-700 flex items-center space-x-1"
                  >
                    <XCircle className="w-3.5 h-3.5" />
                    <span>Reject Extraction</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleConfirm(item.id)}
                    className="px-4 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-md flex items-center space-x-1"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Confirm & Promote</span>
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {activeTab === 'CONFLICTS' && (
        <div className="space-y-3">
          {!data || data.active_conflicts.length === 0 ? (
            <div className="py-16 text-center space-y-2 bg-slate-900/40 border border-slate-800/60 rounded-3xl">
              <ShieldCheck className="w-8 h-8 text-emerald-500 mx-auto" />
              <h4 className="text-xs font-bold text-slate-300">No active knowledge conflicts</h4>
              <p className="text-[11px] text-slate-500">All current organizational documents and decisions are in agreement.</p>
            </div>
          ) : (
            data.active_conflicts.map((c) => (
              <div key={c.id} className="p-5 bg-slate-900/80 border border-rose-900/60 rounded-3xl space-y-4 shadow-xl">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <span className="text-[10px] font-mono font-bold text-rose-400 bg-rose-950 px-2.5 py-1 rounded border border-rose-800 uppercase flex items-center space-x-1">
                    <AlertOctagon className="w-3.5 h-3.5" />
                    <span>{c.severity}: {c.topic}</span>
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">Unresolved Conflict</span>
                </div>

                {/* Side-by-Side Comparison */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2">
                    <span className="text-[9px] font-mono text-indigo-400 uppercase font-bold">Source A</span>
                    <h4 className="font-bold text-xs text-white">{c.source_a.title}</h4>
                    <p className="text-[11px] text-slate-300 font-mono bg-slate-900 p-2 rounded">{c.source_a.content}</p>
                    <button
                      type="button"
                      onClick={() => handleResolveConflict(c.id, c.source_a.id)}
                      className="w-full mt-2 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-[10px]"
                    >
                      Mark Source A as Current
                    </button>
                  </div>

                  <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2">
                    <span className="text-[9px] font-mono text-indigo-400 uppercase font-bold">Source B</span>
                    <h4 className="font-bold text-xs text-white">{c.source_b.title}</h4>
                    <p className="text-[11px] text-slate-300 font-mono bg-slate-900 p-2 rounded">{c.source_b.content}</p>
                    <button
                      type="button"
                      onClick={() => handleResolveConflict(c.id, c.source_b.id)}
                      className="w-full mt-2 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-[10px]"
                    >
                      Mark Source B as Current
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {activeTab === 'AUDIT' && (
        <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-3xl shadow-xl space-y-3 backdrop-blur-md">
          <h3 className="text-sm font-bold text-white border-b border-slate-800 pb-2">Governance Audit Trail Log</h3>

          <div className="space-y-2">
            {auditLog.map((log) => (
              <div key={log.id} className="p-3 bg-slate-950 border border-slate-800 rounded-2xl flex items-center justify-between text-xs font-mono">
                <div className="space-y-0.5">
                  <div className="flex items-center space-x-2">
                    <span className="text-emerald-400 font-bold">{log.action}</span>
                    <span className="text-slate-500">by {log.performed_by}</span>
                  </div>
                  <p className="text-[10px] text-slate-400">{log.reason}</p>
                </div>
                <span className="text-[10px] text-slate-500">
                  {new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
};
