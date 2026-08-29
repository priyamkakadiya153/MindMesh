import React, { useState, useEffect } from 'react';
import {
  fetchKnowledgeReviewQueue, scanCanonicalCandidates, generateMergePreview, revalidateKnowledge, triggerSelfHealIndex, performContextSearch, fetchMaintenanceDigest,
  ReviewQueueItem, CanonicalCandidateItem, MergePreviewResponse, ContextSearchResponse, MaintenanceDigestResponse
} from '../knowledge-maintenance-api';
import {
  Wrench, ShieldCheck, CheckCircle2, AlertTriangle, Layers, ArrowRight, Check, RefreshCw, GitMerge, FileCheck, Search, Database, Sparkles
} from 'lucide-react';

interface KnowledgeMaintenanceCenterProps {
  initialProjectId?: string;
  token?: string;
}

export const KnowledgeMaintenanceCenter: React.FC<KnowledgeMaintenanceCenterProps> = ({
  initialProjectId = 'bfb4530e-bc5d-4c1f-aaf3-217a55bcaba4',
  token
}) => {
  const [activeTab, setActiveTab] = useState<'QUEUE' | 'CANONICAL' | 'CONTEXT' | 'HEAL'>('QUEUE');
  const [reviewQueue, setReviewQueue] = useState<ReviewQueueItem[]>([]);
  const [canonicalCandidates, setCanonicalCandidates] = useState<CanonicalCandidateItem[]>([]);
  const [digest, setDigest] = useState<MaintenanceDigestResponse | null>(null);

  const [mergePreview, setMergePreview] = useState<MergePreviewResponse | null>(null);
  const [contextQuery, setContextQuery] = useState<string>('What is our authentication spec?');
  const [activeScopeContext, setActiveScopeContext] = useState<string>('PROJECT_A');
  const [contextResult, setContextResult] = useState<ContextSearchResponse | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [rq, cc, dig] = await Promise.all([
        fetchKnowledgeReviewQueue(token),
        scanCanonicalCandidates(initialProjectId, token),
        fetchMaintenanceDigest(token)
      ]);
      setReviewQueue(rq);
      setCanonicalCandidates(cc);
      setDigest(dig);
    } catch (err) {
      console.error('Failed to load maintenance center data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [initialProjectId, token]);

  const handleGenerateMergePreview = async () => {
    try {
      const res = await generateMergePreview('doc-auth-v1', 'doc-auth-v2', token);
      setMergePreview(res);
      setActionMessage(`Generated side-by-side merge preview for '${res.source_a_title}' vs '${res.source_b_title}'.`);
    } catch (err) {
      console.error('Failed merge preview:', err);
    }
  };

  const handleRevalidate = async (entityId: string) => {
    try {
      const res = await revalidateKnowledge(entityId, 'STILL_VALID', token);
      setActionMessage(res.message);
      setReviewQueue(prev => prev.filter(q => q.entity_id !== entityId));
    } catch (err) {
      console.error('Failed revalidation:', err);
    }
  };

  const handleSelfHeal = async () => {
    setIsLoading(true);
    try {
      const res = await triggerSelfHealIndex(token);
      setActionMessage(res.message);
      loadData();
    } catch (err) {
      console.error('Failed index self-heal:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleContextSearch = async () => {
    try {
      const res = await performContextSearch(contextQuery, activeScopeContext, token);
      setContextResult(res);
    } catch (err) {
      console.error('Failed context search:', err);
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
                AUTONOMOUS KNOWLEDGE MAINTENANCE & CONTEXTUAL MEMORY
              </span>
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center space-x-1">
                <ShieldCheck className="w-3 h-3" />
                <span>Human-Governed Truth Preservation</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <Wrench className="w-7 h-7 text-indigo-400" />
              <span>Knowledge Maintenance Center</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Continuously maintains health, canonical sources, contextual memory, and self-healing search indices without overwriting governed truth.
            </p>
          </div>

          {/* Navigation Mode Tabs */}
          <div className="flex items-center space-x-2 bg-slate-950 p-1.5 rounded-2xl border border-slate-800 flex-shrink-0">
            <button
              type="button"
              onClick={() => setActiveTab('QUEUE')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'QUEUE' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Review Queue
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('CANONICAL')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'CANONICAL' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Canonical & Merge
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('CONTEXT')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'CONTEXT' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Contextual Memory
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('HEAL')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'HEAL' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Index Self-Healing
            </button>
          </div>
        </div>

        {/* Digest Counters Bar */}
        {digest && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 border-t border-slate-800/60">
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Review Queue Items</span>
              <span className="text-lg font-black text-amber-400">{digest.total_review_items}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">High Impact Stale</span>
              <span className="text-lg font-black text-red-400">{digest.high_impact_stale_count}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Canonical Candidates</span>
              <span className="text-lg font-black text-indigo-400">{digest.canonical_candidates_count}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Self-Healed Indices</span>
              <span className="text-lg font-black text-emerald-400">{digest.self_healed_indices_count}</span>
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
      {activeTab === 'QUEUE' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
          <h3 className="text-xs font-bold text-white uppercase font-mono border-b border-slate-800 pb-3 flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" />
            <span>Impact-Aware Knowledge Review Queue</span>
          </h3>

          <div className="space-y-3">
            {reviewQueue.map((rq) => (
              <div key={rq.queue_item_id} className="p-4 bg-slate-950 border border-slate-800 rounded-2xl flex items-center justify-between text-xs">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className={`text-[8px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${
                      rq.priority === 'HIGH' ? 'bg-red-950 text-red-400 border-red-800/60' : 'bg-slate-900 text-slate-400 border-slate-800'
                    }`}>{rq.priority} PRIORITY</span>
                    <span className="text-[9px] font-mono text-indigo-400 bg-slate-900 px-2 py-0.5 rounded">{rq.issue_type}</span>
                  </div>
                  <h4 className="font-bold text-white mt-1">{rq.title}</h4>
                  <p className="text-[10px] text-slate-400 mt-0.5">{rq.reason}</p>
                </div>

                <button
                  type="button"
                  onClick={() => handleRevalidate(rq.entity_id)}
                  className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 rounded-xl text-white font-bold text-xs flex items-center space-x-1"
                >
                  <FileCheck className="w-3 h-3" />
                  <span>Revalidate Freshness</span>
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'CANONICAL' && (
        <div className="space-y-6">
          {/* Canonical Candidates */}
          <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
            <h3 className="text-xs font-bold text-white uppercase font-mono border-b border-slate-800 pb-3 flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-indigo-400" />
              <span>Suggested Canonical Knowledge Candidates</span>
            </h3>

            <div className="space-y-3">
              {canonicalCandidates.map((cc) => (
                <div key={cc.candidate_id} className="p-4 bg-slate-950 border border-indigo-800/60 rounded-2xl space-y-3 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-[9px] font-mono text-indigo-400 bg-slate-900 px-2 py-0.5 rounded font-bold">{cc.concept}</span>
                    <span className="text-[8px] font-mono font-bold text-amber-400 bg-amber-950 px-2 py-0.5 rounded uppercase">{cc.status}</span>
                  </div>

                  <p className="text-white font-bold">Recommended Canonical: "{cc.recommended_canonical_doc}"</p>
                  <p className="text-[10px] text-slate-400">{cc.recommendation_reason}</p>

                  <div className="flex justify-end pt-1">
                    <button
                      type="button"
                      onClick={() => handleGenerateMergePreview()}
                      className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-white font-bold text-xs flex items-center space-x-1"
                    >
                      <GitMerge className="w-3.5 h-3.5" />
                      <span>Generate Side-by-Side Merge Preview</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Merge Preview Drawer */}
          {mergePreview && (
            <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
              <h3 className="text-xs font-bold text-white uppercase font-mono border-b border-slate-800 pb-3 flex items-center space-x-2">
                <GitMerge className="w-4 h-4 text-emerald-400" />
                <span>Side-by-Side Merge Preview</span>
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl">
                  <span className="text-[9px] font-mono text-slate-500 uppercase block font-bold">Source A</span>
                  <h4 className="font-bold text-white mt-1">{mergePreview.source_a_title}</h4>
                </div>
                <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl">
                  <span className="text-[9px] font-mono text-slate-500 uppercase block font-bold">Source B</span>
                  <h4 className="font-bold text-white mt-1">{mergePreview.source_b_title}</h4>
                </div>
              </div>

              <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl text-xs space-y-2">
                <span className="text-[9px] font-mono text-amber-400 uppercase font-bold">Differences Identified</span>
                {mergePreview.differences.map((d, i) => (
                  <p key={i} className="text-slate-300">• {d}</p>
                ))}
              </div>

              <div className="p-4 bg-indigo-950/80 border border-indigo-800/60 rounded-2xl text-xs">
                <span className="text-[9px] font-mono text-indigo-400 uppercase font-bold block">Proposed Governed Result</span>
                <p className="text-white font-bold mt-1">"{mergePreview.proposed_result}"</p>
                <p className="text-[10px] text-indigo-300 mt-1">{mergePreview.governance_requirement}</p>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'CONTEXT' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Context-Aware Memory Search</h3>
            <p className="text-xs text-slate-400 mt-1">Resolves scope-specific memory without carrying Project A assumptions into Project B.</p>
          </div>

          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono text-slate-400 uppercase font-bold">Scope Context:</span>
              <button
                type="button"
                onClick={() => setActiveScopeContext('PROJECT_A')}
                className={`px-3 py-1 rounded-xl text-xs font-bold ${
                  activeScopeContext === 'PROJECT_A' ? 'bg-indigo-600 text-white' : 'bg-slate-950 text-slate-400 border border-slate-800'
                }`}
              >
                Project A (OAuth)
              </button>
              <button
                type="button"
                onClick={() => setActiveScopeContext('PROJECT_B')}
                className={`px-3 py-1 rounded-xl text-xs font-bold ${
                  activeScopeContext === 'PROJECT_B' ? 'bg-indigo-600 text-white' : 'bg-slate-950 text-slate-400 border border-slate-800'
                }`}
              >
                Project B (JWT 30m)
              </button>
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="text"
                value={contextQuery}
                onChange={(e) => setContextQuery(e.target.value)}
                className="flex-1 bg-slate-950 border border-slate-800 rounded-2xl px-4 py-2 text-xs text-white focus:outline-none"
              />
              <button
                type="button"
                onClick={() => handleContextSearch()}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-2xl text-white font-bold text-xs shadow-md flex items-center space-x-1"
              >
                <Search className="w-3.5 h-3.5" />
                <span>Search Memory</span>
              </button>
            </div>
          </div>

          {contextResult && (
            <div className="p-5 bg-slate-950 border border-indigo-800/60 rounded-3xl space-y-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-[9px] font-mono text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 font-bold">Scope: {contextResult.resolved_scope}</span>
                <span className="text-[9px] font-mono text-slate-500">Confidence: {contextResult.confidence}</span>
              </div>

              <p className="text-white font-bold">"{contextResult.answer}"</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'HEAL' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-white uppercase font-mono">Derived Index Self-Healing Engine</h3>
              <p className="text-xs text-slate-400 mt-1">Automatically repairs broken search chunks, missing embeddings, and stale cache representations.</p>
            </div>
            
            <button
              type="button"
              onClick={() => handleSelfHeal()}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-2xl text-white font-bold text-xs shadow-lg flex items-center space-x-1.5"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Trigger Self-Heal Now</span>
            </button>
          </div>

          <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2 text-xs">
            <span className="text-[9px] font-mono text-emerald-400 uppercase font-bold">Self-Healing Safeguards</span>
            <p className="text-slate-300">• Repairs derived embeddings and vector chunks automatically.</p>
            <p className="text-slate-300">• NEVER alters original source markdown document text.</p>
            <p className="text-slate-300">• Preserves strict human governance over authoritative truth.</p>
          </div>
        </div>
      )}

    </div>
  );
};
