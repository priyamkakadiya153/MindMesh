import React from 'react';
import { FileText, ExternalLink } from 'lucide-react';
import { CitationData } from '../chat-api';

interface CitationCardProps {
  citation: CitationData;
  onPreviewClick: (citation: CitationData) => void;
}

export const CitationCard: React.FC<CitationCardProps> = ({ citation, onPreviewClick }) => {
  const docName = citation.document || 'Document';
  const pageText = citation.page || citation.page_number ? ` (Page ${citation.page || citation.page_number})` : '';
  const scorePercent = citation.confidence || citation.score ? Math.round((citation.confidence || citation.score || 1) * 100) : 100;

  return (
    <div
      onClick={() => onPreviewClick(citation)}
      className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-accentSubtle hover:bg-accent/20 border border-accent/30 hover:border-accent rounded-lg text-xs text-accentText cursor-pointer transition-all shadow-sm group"
      title={`Click to preview source: ${docName}`}
    >
      <FileText size={12} className="text-accentText group-hover:scale-110 transition-transform" />
      <span className="font-medium truncate max-w-[180px]">
        {docName}{pageText}
      </span>
      <span className="text-[10px] bg-accent/15 text-accentText px-1.5 py-0.5 rounded font-mono font-semibold">
        {scorePercent}%
      </span>
      <ExternalLink size={10} className="text-accentText opacity-60 group-hover:opacity-100" />
    </div>
  );
};
