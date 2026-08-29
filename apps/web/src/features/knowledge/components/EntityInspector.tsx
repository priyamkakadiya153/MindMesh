import React from 'react';
import { EntityProvenanceInspectorResponse, RelatedItem, ProvenanceChainStep } from '../connections-api';
import {
  FileText, Briefcase, CheckSquare, Brain, MessageSquare, AlertCircle,
  ArrowRight, ExternalLink, ShieldCheck, Sparkles, User, GitBranch, Layers, ChevronRight
} from 'lucide-react';

interface EntityInspectorProps {
  data: EntityProvenanceInspectorResponse | null;
  isLoading: boolean;
  onSelectRelatedItem?: (type: string, id: string) => void;
  onAskMindMesh?: (prompt: string) => void;
}

export const EntityInspector: React.FC<EntityInspectorProps> = ({
  data,
  isLoading,
  onSelectRelatedItem,
  onAskMindMesh
}) => {
  if (isLoading) {
    return (
      <div className="p-6 bg-slate-900/60 border border-slate-800 rounded-3xl flex flex-col items-center justify-center min-h-[420px] space-y-3 text-slate-400">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        <span className="text-sm font-medium">Assembling 360° Provenance Inspector...</span>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-6 bg-slate-900/40 border border-slate-800/80 rounded-3xl flex flex-col items-center justify-center min-h-[420px] text-center space-y-3 text-slate-400">
        <Brain className="w-12 h-12 text-slate-600 stroke-[1.5]" />
        <h3 className="text-base font-semibold text-slate-300">Select an entity to inspect relationships</h3>
        <p className="text-xs text-slate-500 max-w-xs">
          Click any project, task, document, decision, or conversation to explore why it exists, supporting evidence, and downstream impacts.
        </p>
      </div>
    );
  }

  const getTypeIcon = (type: string) => {
    switch (type.toUpperCase()) {
      case 'TASK': return <CheckSquare className="w-4 h-4 text-emerald-400" />;
      case 'PROJECT': return <Briefcase className="w-4 h-4 text-indigo-400" />;
      case 'DOCUMENT': case 'FILE': return <FileText className="w-4 h-4 text-blue-400" />;
      case 'DECISION': return <Brain className="w-4 h-4 text-amber-400" />;
      case 'CONVERSATION': case 'MESSAGE': return <MessageSquare className="w-4 h-4 text-purple-400" />;
      default: return <GitBranch className="w-4 h-4 text-slate-400" />;
    }
  };

  const handleAskHandoff = () => {
    const prompt = data.status === 'blocked'
      ? `Why is the task "${data.title}" blocked and what documents or decisions support it?`
      : `What decisions and documents are connected to "${data.title}"?`;
    onAskMindMesh?.(prompt);
  };

  const isDocument = data.entity_type === 'DOCUMENT' || data.entity_type === 'FILE';
  const hasVerified = data.has_verified_connections ?? (
    (data.supporting_evidence && data.supporting_evidence.length > 0) ||
    (data.related_decisions && data.related_decisions.length > 0) ||
    (data.resulting_tasks && data.resulting_tasks.length > 0) ||
    (data.connected_project !== undefined)
  );

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-5 md:p-6 space-y-6 shadow-2xl backdrop-blur-md select-text">
      
      {/* Interactive Step-by-Step Provenance Chain Bar */}
      {data.provenance_chain && data.provenance_chain.length > 1 && (
        <div className="p-3 bg-slate-950/80 border border-indigo-900/50 rounded-2xl space-y-1.5">
          <div className="flex items-center space-x-1 text-[10px] font-mono uppercase font-bold text-indigo-400">
            <GitBranch className="w-3 h-3 text-indigo-400" />
            <span>PROVENANCE CHAIN (CLICK TO PIVOT)</span>
          </div>
          <div className="flex items-center flex-wrap gap-1.5 text-xs">
            {data.provenance_chain.map((step, idx) => (
              <React.Fragment key={idx}>
                {idx > 0 && <ChevronRight className="w-3.5 h-3.5 text-slate-600 shrink-0" />}
                <button
                  onClick={() => onSelectRelatedItem?.(step.type, step.id)}
                  className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-xl font-medium transition-all ${
                    step.id === data.entity_id
                      ? 'bg-indigo-600 text-white shadow-sm'
                      : 'bg-slate-900 text-slate-300 hover:bg-slate-800 border border-slate-700/60'
                  }`}
                >
                  <span className="text-[10px] font-mono uppercase opacity-75">{step.type}:</span>
                  <span className="truncate max-w-[120px]">{step.title}</span>
                </button>
              </React.Fragment>
            ))}
          </div>
        </div>
      )}

      {/* Header Badge & Title */}
      <div className="space-y-3 pb-4 border-b border-slate-800/80">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center space-x-2">
            <span className="p-2 bg-slate-800/80 rounded-xl border border-slate-700/60">
              {getTypeIcon(data.entity_type)}
            </span>
            <div>
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-indigo-400 px-2 py-0.5 bg-indigo-950/80 rounded border border-indigo-800/60">
                {data.entity_type} RELATIONSHIP INSPECTOR
              </span>
              <h2 className="text-lg font-bold text-white leading-snug mt-1">
                {data.title}
              </h2>
            </div>
          </div>
          
          {data.status && (
            <span className={`px-2.5 py-1 rounded-full text-xs font-semibold uppercase tracking-wider border ${
              data.status.toLowerCase() === 'blocked'
                ? 'bg-rose-950/60 text-rose-300 border-rose-800/60'
                : 'bg-emerald-950/60 text-emerald-300 border-emerald-800/60'
            }`}>
              {data.status}
            </span>
          )}
        </div>

        {/* Document Contextual Purpose vs File Metadata */}
        {isDocument && (
          <div className="p-3 bg-blue-950/30 border border-blue-900/40 rounded-xl text-xs text-blue-200 space-y-1">
            <span className="font-mono text-[10px] uppercase font-bold text-blue-400 block">DOCUMENT CONTEXTUAL ROLE</span>
            <p>This document serves as primary architectural specification and evidence in workspace workflows.</p>
          </div>
        )}

        {/* Source Link */}
        {data.deep_link && (
          <div className="pt-1 flex justify-end">
            <a
              href={data.deep_link}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center space-x-1 text-xs text-indigo-400 hover:text-indigo-300 font-medium"
            >
              <span>View Source Entity Record</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>
        )}
      </div>

      {/* Ask MindMesh AI Button */}
      <button
        onClick={handleAskHandoff}
        className="w-full flex items-center justify-between px-4 py-3 bg-gradient-to-r from-indigo-950/80 via-purple-950/60 to-slate-900 border border-indigo-800/60 hover:border-indigo-600 rounded-2xl text-xs font-semibold text-indigo-200 hover:text-white transition-all shadow-md group"
      >
        <div className="flex items-center space-x-2">
          <Sparkles className="w-4 h-4 text-indigo-400 group-hover:rotate-12 transition-transform" />
          <span>Ask MindMesh about this entity's connections</span>
        </div>
        <ArrowRight className="w-4 h-4 text-indigo-400 group-hover:translate-x-1 transition-transform" />
      </button>

      {/* Real Honest Empty State if no verified connections */}
      {!hasVerified && (
        <div className="p-5 bg-slate-950/80 rounded-2xl border border-slate-800 text-center space-y-2">
          <Brain className="w-8 h-8 text-slate-600 mx-auto stroke-[1.5]" />
          <h4 className="text-xs font-bold text-slate-300">No verified connections found for this item yet.</h4>
          <p className="text-[11px] text-slate-500">
            Basic Record Metadata: {data.entity_type} created {data.created_at ? new Date(data.created_at).toLocaleDateString() : 'in workspace'}.
          </p>
        </div>
      )}

      {/* Section 1: WHY DOES IT EXIST? */}
      {data.why_exists && (
        <div className="space-y-1.5 p-3 bg-slate-950/60 rounded-xl border border-slate-800">
          <h4 className="text-[11px] font-mono font-bold uppercase tracking-wider text-indigo-400 flex items-center space-x-1.5">
            <GitBranch className="w-3.5 h-3.5" />
            <span>Why Does It Exist? (Creation Provenance)</span>
          </h4>
          <p className="text-xs text-slate-200">{data.why_exists}</p>
        </div>
      )}

      {/* Section 2: CONNECTED PROJECT */}
      {data.connected_project && (
        <div className="space-y-1.5">
          <h4 className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
            <Briefcase className="w-3.5 h-3.5 text-indigo-400" />
            <span>Primary Connected Project</span>
          </h4>
          <RelatedItemRow item={data.connected_project} onSelect={onSelectRelatedItem} />
        </div>
      )}

      {/* Section 3: SUPPORTING EVIDENCE */}
      {data.supporting_evidence && data.supporting_evidence.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />
            <span>Supporting Evidence ({data.supporting_evidence.length})</span>
          </h4>
          <div className="space-y-2">
            {data.supporting_evidence.map((item, idx) => (
              <RelatedItemRow key={idx} item={item} onSelect={onSelectRelatedItem} />
            ))}
          </div>
        </div>
      )}

      {/* Section 4: RELATED DECISIONS */}
      {data.related_decisions && data.related_decisions.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
            <Brain className="w-3.5 h-3.5 text-amber-400" />
            <span>Related Decisions ({data.related_decisions.length})</span>
          </h4>
          <div className="space-y-2">
            {data.related_decisions.map((item, idx) => (
              <RelatedItemRow key={idx} item={item} onSelect={onSelectRelatedItem} />
            ))}
          </div>
        </div>
      )}

      {/* Section 5: RESULTING TASKS */}
      {data.resulting_tasks && data.resulting_tasks.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
            <Layers className="w-3.5 h-3.5 text-emerald-400" />
            <span>Resulting / Connected Tasks ({data.resulting_tasks.length})</span>
          </h4>
          <div className="space-y-2">
            {data.resulting_tasks.map((item, idx) => (
              <RelatedItemRow key={idx} item={item} onSelect={onSelectRelatedItem} />
            ))}
          </div>
        </div>
      )}

      {/* Section 6: DEPENDENCIES & BLOCKERS */}
      {data.dependencies_and_blockers && data.dependencies_and_blockers.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-[11px] font-mono font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
            <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
            <span>Dependencies & Blockers ({data.dependencies_and_blockers.length})</span>
          </h4>
          <div className="space-y-2">
            {data.dependencies_and_blockers.map((item, idx) => (
              <RelatedItemRow key={idx} item={item} onSelect={onSelectRelatedItem} />
            ))}
          </div>
        </div>
      )}

    </div>
  );
};

const RelatedItemRow: React.FC<{ item: RelatedItem; onSelect?: (type: string, id: string) => void }> = ({ item, onSelect }) => {
  return (
    <div
      onClick={() => onSelect?.(item.type, item.id)}
      className="flex items-center justify-between p-3 bg-slate-950/60 hover:bg-slate-800/80 border border-slate-800/80 hover:border-slate-700 rounded-xl cursor-pointer transition-all group"
    >
      <div className="flex items-center space-x-3 min-w-0">
        <span className="text-xs px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-300 font-mono">
          {item.relation}
        </span>
        <span className="text-xs font-medium text-slate-200 truncate group-hover:text-indigo-300 transition-colors">
          {item.title}
        </span>
      </div>

      <div className="flex items-center space-x-2 text-[10px] text-slate-400 shrink-0 ml-2">
        <span className={`px-1.5 py-0.5 rounded border ${
          item.evidence_type === 'EXPLICIT_FK'
            ? 'bg-emerald-950/60 text-emerald-400 border-emerald-800/60'
            : 'bg-indigo-950/60 text-indigo-400 border-indigo-800/60'
        }`}>
          {item.evidence_type === 'EXPLICIT_FK' ? 'Direct DB' : 'Inferred'}
        </span>
        <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-indigo-400 group-hover:translate-x-0.5 transition-all" />
      </div>
    </div>
  );
};
