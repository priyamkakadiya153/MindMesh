import React from 'react';
import { X, FileText, MessageSquare, Folder, CheckSquare, GitCommit, AlertTriangle, ExternalLink, Calendar, Layers, Activity } from 'lucide-react';
import { CognitiveAgentOutputRecord, CognitiveAgentProvenanceSource } from '../../../types/cognitive-agent';

interface OutputDetailModalProps {
  isOpen: boolean;
  output: CognitiveAgentOutputRecord | null;
  agentName?: string;
  onClose: () => void;
  onNavigateToSource?: (source: CognitiveAgentProvenanceSource) => void;
}

export const OutputDetailModal: React.FC<OutputDetailModalProps> = ({
  isOpen,
  output,
  agentName = 'Cognitive Agent',
  onClose,
  onNavigateToSource
}) => {
  if (!isOpen || !output) return null;

  const renderSourceIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'document':
        return <FileText className="w-4 h-4 text-blue-400" />;
      case 'conversation':
      case 'message':
        return <MessageSquare className="w-4 h-4 text-emerald-400" />;
      case 'project':
        return <Folder className="w-4 h-4 text-purple-400" />;
      case 'task':
        return <CheckSquare className="w-4 h-4 text-amber-400" />;
      case 'decision':
        return <GitCommit className="w-4 h-4 text-indigo-400" />;
      default:
        return <Layers className="w-4 h-4 text-accent" />;
    }
  };

  return (
    <div className="fixed inset-0 z-[120] flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-fadeIn font-outfit">
      <div className="bg-bgCard border border-borderColor rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-5 text-textPrimary max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-borderMuted pb-4 flex-shrink-0">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 text-[9px] font-bold uppercase rounded-md bg-accentSubtle text-accent border border-accent/20">
                {output.output_type}
              </span>
              <span className="text-xs text-textMuted font-mono">By {agentName}</span>
            </div>
            <h3 className="text-lg font-bold text-textPrimary">{output.title}</h3>
            <div className="flex items-center gap-4 text-xs text-textMuted">
              <span className="flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5 text-textMuted" />
                {new Date(output.created_at).toLocaleString()}
              </span>
              <span className="flex items-center gap-1 font-mono text-[11px]">
                <Activity className="w-3.5 h-3.5 text-textMuted" />
                Execution ID: {output.execution_id.slice(0, 8)}
              </span>
            </div>
          </div>
          <button onClick={onClose} className="p-1 text-textMuted hover:text-textPrimary rounded-lg transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Content Body */}
        <div className="overflow-y-auto pr-1 space-y-5 flex-1 custom-scrollbar">
          {/* Analysis Body */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-textSecondary">Analysis & Intelligence</h4>
            <div className="p-4 bg-bgInput/50 rounded-xl border border-borderMuted text-xs text-textPrimary leading-relaxed whitespace-pre-wrap font-sans">
              {output.body}
            </div>
          </div>

          {/* Provenance Sources */}
          <div className="space-y-2.5">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold uppercase tracking-wider text-textSecondary">
                Grounded Knowledge Sources ({output.provenance?.length || 0})
              </h4>
            </div>

            {!output.provenance || output.provenance.length === 0 ? (
              <p className="text-xs text-textMuted italic">No explicit sources recorded for this analysis.</p>
            ) : (
              <div className="space-y-2">
                {output.provenance.map((src, idx) => (
                  <div
                    key={idx}
                    className={`p-3 rounded-xl border transition-all flex items-center justify-between gap-3 text-xs ${
                      src.is_available === false
                        ? 'bg-red-500/5 border-red-500/20'
                        : src.is_stale
                        ? 'bg-amber-500/5 border-amber-500/20'
                        : 'bg-bgInput/40 border-borderMuted hover:border-borderColor'
                    }`}
                  >
                    <div className="flex items-start gap-3 min-w-0">
                      <div className="p-2 rounded-lg bg-bgCard border border-borderMuted flex-shrink-0">
                        {renderSourceIcon(src.source_type)}
                      </div>
                      <div className="space-y-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-semibold text-textPrimary truncate">{src.title}</span>
                          <span className="px-1.5 py-0.2 text-[9px] font-mono uppercase bg-bgCard text-textMuted rounded border border-borderMuted">
                            {src.source_type}
                          </span>
                        </div>

                        {/* Status / Warnings */}
                        {src.is_available === false && (
                          <div className="text-[11px] text-red-400 flex items-center gap-1 font-medium">
                            <AlertTriangle className="w-3 h-3 flex-shrink-0" />
                            {src.status_message || 'Source no longer available (permission revoked or deleted).'}
                          </div>
                        )}
                        {src.is_stale && (
                          <div className="text-[11px] text-amber-400 flex items-center gap-1 font-medium">
                            <AlertTriangle className="w-3 h-3 flex-shrink-0" />
                            {src.stale_message || 'Source updated since this analysis.'}
                          </div>
                        )}
                        {src.message_text && src.is_available !== false && (
                          <p className="text-[11px] text-textMuted italic truncate max-w-md">
                            "{src.message_text}"
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Navigation Button */}
                    {src.is_available !== false && onNavigateToSource && (
                      <button
                        onClick={() => onNavigateToSource(src)}
                        className="px-2.5 py-1 text-[11px] font-semibold text-accent border border-accent/30 bg-accentSubtle hover:bg-accent/20 rounded-lg transition-all flex items-center gap-1 flex-shrink-0"
                      >
                        <ExternalLink className="w-3 h-3" />
                        Open Source
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end pt-3 border-t border-borderMuted flex-shrink-0">
          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-medium text-textSecondary hover:text-textPrimary bg-bgInput hover:bg-bgHover border border-borderColor rounded-xl transition-all"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
