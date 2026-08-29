import React, { useState, useEffect } from 'react';
import {
  fetchProvenanceDetail, updateVerificationState, fetchConflicts, resolveConflict, confirmAISuggestion,
  fetchReviewQueue, revalidateAIResult, fetchQualityAuditLog, ProvenanceResponse, ConflictItem, ReviewQueueResponse, AuditLogEntry
} from '../trust-quality-api';
import {
  ShieldCheck, AlertOctagon, CheckCircle2, XCircle, RefreshCw, FileText, Layers, History, ShieldAlert, Bot, Check, ArrowRight
} from 'lucide-react';

interface KnowledgeTrustQualityCenterProps {
  initialEntityId?: string;
  token?: string;
}

export const KnowledgeTrustQualityCenter: React.FC<KnowledgeTrustQualityCenterProps> = ({
  initialEntityId = 'doc-105',
  token
}) => {
  const [activeTab, setActiveTab] = useState<'QUEUE' | 'CONFLICTS' | 'PROVENANCE' | 'AUDIT'>('QUEUE');
  const [provenance, setProvenance] = useState<ProvenanceResponse | null>(null);
  const [conflicts, setConflicts] = useState<ConflictItem[]>([]);
  const [reviewQueue, setReviewQueue] = useState<ReviewQueueResponse | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [provRes, cnfRes, qRes, audRes] = await Promise.all([
        fetchProvenanceDetail(initialEntityId, token),
        fetchConflicts(token),
        fetchReviewQueue(token),
        fetchQualityAuditLog(token)
      ]);
      setProvenance(provRes);
      setConflicts(cnfRes);
      setReviewQueue(qRes);
      setAuditLogs(audRes);
    } catch (err) {
      console.error('Failed to load knowledge trust quality center:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [initialEntityId, token]);

  const handleVerify = async (statusVal: string) => {
    try {
      const res = await updateVerificationState(initialEntityId, statusVal, 'Verified via Governance Quality Gate', token);
      setActionMessage(res.message);
      loadData();
    } catch (err) {
      console.error('Failed verification update:', err);
    }
  };

  const handleResolveConflict = async (conflictId: string, strategy: string) => {
    try {
      const res = await resolveConflict(conflictId, strategy, 'Confirmed source V2 supersedes V1', token);
      setActionMessage(res.message);
      loadData();
    } catch (err) {
      console.error('Failed conflict resolution:', err);
    }
  };

  const handleConfirmAI = async () => {
    try {
      const res = await confirmAISuggestion(initialEntityId, token);
      setActionMessage(res.message);
      loadData();
    } catch (err) {
      console.error('Failed AI confirmation:', err);
    }
  };

  const handleRevalidate = async () => {
    try {
      const res = await revalidateAIResult(initialEntityId, token);
      setActionMessage(res.message);
      loadData();
    } catch (err) {
      console.error('Failed revalidation:', err);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6 text-slate-100 font-sans select-none">
      
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-emerald-950/80 to-slate-900 border border-emerald-800/60 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-emerald-400 px-2.5 py-0.5 bg-emerald-950 rounded border border-emerald-800/60">
                TRUST, GOVERNANCE & INTELLIGENCE QUALITY SYSTEM
              </span>
              <span className="text-[10px] font-mono font-bold text-indigo-400 bg-indigo-950 px-2 py-0.5 rounded border border-indigo-800/60 flex items-center space-x-1">
                <ShieldCheck className="w-3 h-3" />
                <span>Grounding & Provenance Layer</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <ShieldCheck className="w-7 h-7 text-emerald-400" />
              <span>Knowledge Governance & Trust Center</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Know what information can be trusted, what has become outdated, and how much confidence users can place in AI-generated insights.
            </p>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center space-x-2 bg-slate-950 p-1.5 rounded-2xl border border-slate-800 flex-shrink-0">
            <button
              type="button"
              onClick={() => setActiveTab('QUEUE')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'QUEUE' ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Review Queue
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('CONFLICTS')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'CONFLICTS' ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Conflicts
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('PROVENANCE')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'PROVENANCE' ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Provenance
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('AUDIT')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'AUDIT' ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Audit Log
            </button>
          </div>
        </div>

        {/* Metrics Counters Bar */}
        {reviewQueue && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 border-t border-slate-800/60">
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Total Review Queue</span>
              <span className="text-lg font-black text-emerald-400">{reviewQueue.total_review_items}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Needs Verification</span>
              <span className="text-lg font-black text-amber-400">{reviewQueue.needs_verification.length}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Active Conflicts</span>
              <span className="text-lg font-black text-red-400">{conflicts.filter(c => c.status === 'DETECTED').length}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">AI Generated Items</span>
              <span className="text-lg font-black text-indigo-400">{reviewQueue.ai_generated.length}</span>
            </div>
          </div>
        )}
      </div>

      {actionMessage && (
        <div className="p-3 bg-emerald-950/80 border border-emerald-800/60 rounded-2xl text-xs text-emerald-200 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Check className="w-4 h-4 text-emerald-400" />
            <span>{actionMessage}</span>
          </div>
          <button type="button" onClick={() => setActionMessage(null)} className="text-[10px] text-slate-400 hover:text-white font-mono">Dismiss</button>
        </div>
      )}

      {/* Tab Views */}
      {activeTab === 'QUEUE' && reviewQueue && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Knowledge Review Queue</h3>
            <p className="text-xs text-slate-400 mt-1">Prioritized review items requiring human verification or revalidation.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-3">
              <span className="text-[10px] font-mono font-bold text-amber-400 uppercase block">Needs Verification</span>
              {reviewQueue.needs_verification.map(item => (
                <div key={item.id} className="p-3 bg-slate-900 rounded-xl space-y-2 text-xs border border-slate-800">
                  <span className="font-bold text-white block">{item.title}</span>
                  <div className="flex items-center justify-between">
                    <span className="text-[9px] font-mono text-slate-400">Source: {item.source}</span>
                    <button
                      type="button"
                      onClick={() => handleVerify('VERIFIED')}
                      className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 rounded-lg text-white font-bold text-[10px]"
                    >
                      Verify
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-3">
              <span className="text-[10px] font-mono font-bold text-indigo-400 uppercase block">AI Generated Content</span>
              {reviewQueue.ai_generated.map(item => (
                <div key={item.id} className="p-3 bg-slate-900 rounded-xl space-y-2 text-xs border border-slate-800">
                  <span className="font-bold text-white block">{item.title}</span>
                  <div className="flex items-center justify-between">
                    <span className="text-[9px] font-mono text-indigo-300">Tag: AI_GENERATED</span>
                    <button
                      type="button"
                      onClick={() => handleConfirmAI()}
                      className="px-2.5 py-1 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-white font-bold text-[10px]"
                    >
                      Confirm Human Verified
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'CONFLICTS' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono flex items-center space-x-2">
              <ShieldAlert className="w-4 h-4 text-red-400" />
              <span>Conflict Detection & Human Resolution Panel</span>
            </h3>
            <p className="text-xs text-slate-400 mt-1">Preserves conflicting evidence explicitly without silent automated overrides.</p>
          </div>

          <div className="space-y-4">
            {conflicts.map(cnf => (
              <div key={cnf.conflict_id} className="p-5 bg-slate-950 border border-red-800/60 rounded-3xl space-y-4 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-[9px] font-mono text-red-400 bg-red-950 px-2.5 py-0.5 rounded border border-red-800/60 font-bold uppercase">{cnf.status}</span>
                  <span className="text-[9px] font-mono text-slate-400">{cnf.detected_at}</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-3 bg-slate-900 rounded-2xl space-y-1">
                    <span className="text-[9px] font-mono text-indigo-400 font-bold uppercase block">Source A: {cnf.source_a}</span>
                    <p className="text-slate-200">{cnf.claim_a}</p>
                  </div>
                  <div className="p-3 bg-slate-900 rounded-2xl space-y-1">
                    <span className="text-[9px] font-mono text-amber-400 font-bold uppercase block">Source B: {cnf.source_b}</span>
                    <p className="text-slate-200">{cnf.claim_b}</p>
                  </div>
                </div>

                {cnf.status === 'DETECTED' && (
                  <div className="flex items-center space-x-2 pt-2 border-t border-slate-800">
                    <button
                      type="button"
                      onClick={() => handleResolveConflict(cnf.conflict_id, 'CONFIRM_SOURCE_B')}
                      className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 rounded-xl text-white font-bold text-xs"
                    >
                      Confirm Source B (Spec V2)
                    </button>
                    <button
                      type="button"
                      onClick={() => handleResolveConflict(cnf.conflict_id, 'SUPERSEDE_BOTH')}
                      className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-xl text-slate-300 font-bold text-xs"
                    >
                      Supersede Both
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'PROVENANCE' && provenance && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-white uppercase font-mono">Source Provenance & Lineage Inspector</h3>
              <p className="text-xs text-slate-400 mt-1">Grounding trace for entity '{provenance.entity_id}'.</p>
            </div>
            <span className="text-[9px] font-mono text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 font-bold">{provenance.provenance_label}</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2">
              <span className="font-bold text-emerald-400 block uppercase font-mono">Origin & Authority</span>
              <p className="text-slate-300">• <strong className="text-slate-100">Source:</strong> {provenance.origin.source_name} ({provenance.origin.source_type})</p>
              <p className="text-slate-300">• <strong className="text-slate-100">Authority Level:</strong> {provenance.authority.level}</p>
              <p className="text-slate-300">• <strong className="text-slate-100">Verification Status:</strong> {provenance.verification.status}</p>
            </div>

            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2">
              <span className="font-bold text-indigo-400 block uppercase font-mono">AI Origin & Confirmation</span>
              <p className="text-slate-300">• <strong className="text-slate-100">Tag:</strong> {provenance.ai_provenance.tag}</p>
              <p className="text-slate-300">• <strong className="text-slate-100">Provider:</strong> {provenance.ai_provenance.model_provider}</p>
              <p className="text-slate-300">• <strong className="text-slate-100">Human Confirmed:</strong> {provenance.ai_provenance.human_confirmation ? 'YES' : 'NO'}</p>
            </div>
          </div>

          <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2 text-xs">
            <span className="font-bold text-white block font-mono uppercase">Source Lineage Chain</span>
            {provenance.lineage.map((lin, idx) => (
              <p key={idx} className="text-slate-300">{lin.step}. <strong className="text-indigo-300">{lin.type}:</strong> {lin.label}</p>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'AUDIT' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
          <h3 className="text-xs font-bold text-white uppercase font-mono">Immutable Governance Audit Log</h3>
          <div className="space-y-2">
            {auditLogs.map(aud => (
              <div key={aud.audit_id} className="p-3 bg-slate-950 border border-slate-800 rounded-2xl text-xs flex items-center justify-between">
                <div>
                  <span className="font-bold text-white">{aud.action}</span>
                  <span className="text-slate-400 ml-2">by {aud.actor}</span>
                  <p className="text-[10px] text-slate-400 mt-0.5">{aud.rationale}</p>
                </div>
                <span className="text-[9px] font-mono text-slate-500">{aud.timestamp}</span>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
};
