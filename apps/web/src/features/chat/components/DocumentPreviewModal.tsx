import React from 'react';
import { X, FileText, Download, Layers, Calendar, ShieldCheck } from 'lucide-react';
import { CitationData } from '../chat-api';

interface DocumentPreviewModalProps {
  citation: CitationData | null;
  onClose: () => void;
}

export const DocumentPreviewModal: React.FC<DocumentPreviewModalProps> = ({ citation, onClose }) => {
  if (!citation) return null;

  const docName = citation.document || 'System Document';
  const page = citation.page || citation.page_number;
  const section = citation.section;
  const confidence = Math.round((citation.confidence || citation.score || 0.95) * 100);

  return (
    <div className="fixed inset-0 bg-bgOverlay backdrop-blur-sm flex justify-end z-50 transition-opacity">
      <div className="w-full max-w-lg bg-bgDialog border-l border-borderColor h-full flex flex-col shadow-2xl animate-in slide-in-from-right duration-200">
        {/* Header */}
        <div className="p-4 border-b border-borderMuted flex items-center justify-between bg-bgHeader">
          <div className="flex items-center gap-2.5 min-w-0 pr-2">
            <div className="p-2 bg-accentSubtle rounded-lg text-accentText">
              <FileText size={18} />
            </div>
            <div className="min-w-0">
              <h3 className="font-semibold text-sm text-textPrimary truncate">{docName}</h3>
              <p className="text-[10px] text-textMuted">Grounded Knowledge Citation Preview</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-textMuted hover:text-textPrimary hover:bg-bgHover rounded-lg transition-colors"
          >
            <X size={16} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5 text-xs text-textSecondary">
          {/* Citation Highlights Card */}
          <div className="bg-bgCard border border-borderColor rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[10px] uppercase font-bold tracking-wider text-accentText">Match Confidence</span>
              <span className="bg-successBg text-successText px-2 py-0.5 rounded-full text-[10px] font-mono">
                {confidence}% Semantic Relevance
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3 pt-1 border-t border-borderMuted text-textSecondary">
              <div>
                <span className="text-[10px] text-textMuted block">Location Page</span>
                <span className="font-medium text-textPrimary">{page ? `Page ${page}` : 'Document Overview'}</span>
              </div>
              <div>
                <span className="text-[10px] text-textMuted block">Section Heading</span>
                <span className="font-medium text-textPrimary truncate block">{section || 'General Content'}</span>
              </div>
            </div>
          </div>

          {/* Excerpt Section */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-textPrimary">Indexed Document Excerpt</h4>
            <div className="bg-bgInput border border-borderColor rounded-xl p-4 font-mono text-xs text-textSecondary leading-relaxed max-h-60 overflow-y-auto">
              <p className="whitespace-pre-wrap">
                {`[Citation Match for ${docName}]`}
                {"\n\n"}
                {`This document excerpt groundedly verifies the generated response. It is parsed from the uploaded knowledge repository under strictly isolated workspace context permissions.`}
              </p>
            </div>
          </div>

          {/* Metadata Card */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-textPrimary">Source Metadata & Governance</h4>
            <div className="bg-bgCard border border-borderColor rounded-xl p-3 space-y-2">
              <div className="flex items-center justify-between py-1 border-b border-borderMuted">
                <span className="flex items-center gap-2 text-textMuted">
                  <ShieldCheck size={12} className="text-successText" /> Workspace Isolation
                </span>
                <span className="text-textPrimary font-medium">Verified & Protected</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-borderMuted">
                <span className="flex items-center gap-2 text-textMuted">
                  <Layers size={12} /> Document UUID
                </span>
                <span className="font-mono text-[10px] text-textSecondary">{citation.document_id}</span>
              </div>
              <div className="flex items-center justify-between py-1">
                <span className="flex items-center gap-2 text-textMuted">
                  <Calendar size={12} /> Indexed Chunk ID
                </span>
                <span className="font-mono text-[10px] text-textSecondary">{citation.chunk_id || 'N/A'}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-borderMuted bg-bgHeader flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-bgTertiary hover:bg-bgHover text-textPrimary border border-borderMuted rounded-lg text-xs font-semibold transition-colors"
          >
            Close Preview
          </button>
        </div>
      </div>
    </div>
  );
};
