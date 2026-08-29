import React, { useState } from 'react';
import { FileText, ExternalLink, ShieldCheck, AlertTriangle, Layers } from 'lucide-react';
import { CitationItem } from './citation-api';
import { DocumentPreviewModal } from './DocumentPreviewModal';

interface CitationCardProps {
  citations: CitationItem[];
  isUngrounded?: boolean;
}

export const CitationCard: React.FC<CitationCardProps> = ({
  citations,
  isUngrounded = false
}) => {
  const [selectedCitation, setSelectedCitation] = useState<CitationItem | null>(null);

  if (isUngrounded || citations.length === 0) {
    return (
      <div className="bg-amber-500/10 border border-amber-500/20 text-amber-300 rounded-xl p-3.5 flex items-start gap-2.5 text-xs">
        <AlertTriangle size={16} className="text-amber-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold">Ungrounded Notice:</span> This response is based on general model knowledge and is not supported by your workspace documents.
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-2.5">
      <div className="flex items-center gap-2 text-xs font-semibold text-textSecondary border-t border-borderMuted pt-3">
        <ShieldCheck size={14} className="text-accentText" />
        <span>Verified Sources ({citations.length})</span>
      </div>

      {/* Citations List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
        {citations.map((cit) => {
          const isHigh = cit.confidence_score === 'High';
          const isMed = cit.confidence_score === 'Medium';

          return (
            <button
              key={cit.id}
              onClick={() => setSelectedCitation(cit)}
              className="group bg-bgCard hover:bg-bgHover border border-borderColor hover:border-accent/40 rounded-xl p-3 text-left transition-all flex flex-col justify-between"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-1.5 text-xs font-medium text-textPrimary truncate">
                  <span className="font-mono text-accentText font-bold">{cit.citation_tag}</span>
                  <FileText size={14} className="text-textMuted shrink-0" />
                  <span className="truncate">{cit.document_title}</span>
                </div>
                <ExternalLink size={12} className="text-textMuted group-hover:text-accentText shrink-0" />
              </div>

              <div className="flex items-center justify-between mt-2 text-[11px] font-mono">
                <span className="text-textMuted truncate">
                  {cit.page_number ? `Page ${cit.page_number}` : (cit.section_title || 'General')}
                </span>
                <span
                  className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                    isHigh
                      ? 'bg-successBg text-successText border border-successBorder'
                      : isMed
                      ? 'bg-warningBg text-warningText border border-warningBorder'
                      : 'bg-bgTertiary text-textMuted'
                  }`}
                >
                  {Math.round(cit.similarity_score * 100)}% Match
                </span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Document Chunk Preview Modal */}
      {selectedCitation && (
        <DocumentPreviewModal
          documentId={selectedCitation.document_id}
          chunkId={selectedCitation.chunk_id}
          isOpen={!!selectedCitation}
          onClose={() => setSelectedCitation(null)}
        />
      )}
    </div>
  );
};
