import React from 'react';
import { Document } from '../types';
import { Download, Edit2, Trash2, Eye, RotateCcw, FileText, Code, Image as ImageIcon, Archive } from 'lucide-react';

interface DocumentCardProps {
  doc: Document;
  isSelected: boolean;
  onSelect: () => void;
  onClick: () => void;
  onRename?: (doc: Document) => void;
  onDelete?: (doc: Document) => void;
  onRestore?: (doc: Document) => void;
  onDownload?: (doc: Document) => void;
  isTrashView?: boolean;
}

export const DocumentCard: React.FC<DocumentCardProps> = ({
  doc,
  isSelected,
  onSelect,
  onClick,
  onRename,
  onDelete,
  onRestore,
  onDownload,
  isTrashView = false
}) => {
  const getStatusColor = (status?: string) => {
    switch (status?.toUpperCase()) {
      case 'READY':
      case 'COMPLETED': return 'bg-successBg text-successText border-successBorder';
      case 'FAILED': return 'bg-dangerBg text-dangerText border-dangerBorder';
      case 'QUEUED': return 'bg-warningBg text-warningText border-warningBorder';
      default: return 'bg-accentSubtle text-accentText border-accent/30';
    }
  };

  const formatSize = (bytes?: number) => {
    const b = bytes || doc.size_bytes || 0;
    if (b === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(b) / Math.log(k));
    return parseFloat((b / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const ext = (doc.extension || doc.filename.split('.').pop() || '').toLowerCase();

  return (
    <div
      onClick={onClick}
      className={`group relative p-4 rounded-2xl border transition-all duration-200 backdrop-blur-xl cursor-pointer hover:-translate-y-0.5 ${
        isSelected 
          ? 'bg-accentSubtle border-accent/50 shadow-lg shadow-accent/10' 
          : 'bg-bgCard border-borderColor hover:border-borderHover hover:bg-bgCardHover'
      }`}
    >
      {/* Selection Checkbox */}
      <div className="absolute top-3.5 left-3.5 z-10" onClick={(e) => { e.stopPropagation(); onSelect(); }}>
        <div className={`w-4 h-4 rounded-md border flex items-center justify-center transition ${
          isSelected 
            ? 'bg-accent border-accent text-white' 
            : 'border-borderMuted group-hover:border-borderColor bg-bgCard'
        }`}>
          {isSelected && (
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={3} stroke="currentColor" className="w-3 h-3">
              <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
            </svg>
          )}
        </div>
      </div>

      {/* Action Overlay */}
      <div className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1 bg-bgDialog/90 backdrop-blur-md p-1 rounded-xl border border-borderColor shadow-md z-10">
        <button
          onClick={(e) => { e.stopPropagation(); onClick(); }}
          className="p-1 rounded-lg hover:bg-bgHover text-textMuted hover:text-textPrimary transition"
          title="Preview Document"
        >
          <Eye size={12} />
        </button>
        {onDownload && (
          <button
            onClick={(e) => { e.stopPropagation(); onDownload(doc); }}
            className="p-1 rounded-lg hover:bg-bgHover text-textMuted hover:text-textPrimary transition"
            title="Download Original"
          >
            <Download size={12} />
          </button>
        )}
        {!isTrashView && onRename && (
          <button
            onClick={(e) => { e.stopPropagation(); onRename(doc); }}
            className="p-1 rounded-lg hover:bg-bgHover text-textMuted hover:text-accentText transition"
            title="Rename"
          >
            <Edit2 size={12} />
          </button>
        )}
        {isTrashView && onRestore ? (
          <button
            onClick={(e) => { e.stopPropagation(); onRestore(doc); }}
            className="p-1 rounded-lg hover:bg-bgHover text-emerald-500 transition"
            title="Restore Document"
          >
            <RotateCcw size={12} />
          </button>
        ) : onDelete ? (
          <button
            onClick={(e) => { e.stopPropagation(); onDelete(doc); }}
            className="p-1 rounded-lg hover:bg-bgHover text-dangerText transition"
            title="Delete Document"
          >
            <Trash2 size={12} />
          </button>
        ) : null}
      </div>

      <div className="flex flex-col items-center text-center mt-3">
        <div className="h-14 w-14 flex items-center justify-center rounded-2xl bg-accentSubtle border border-accent/20 text-accentText mb-3 group-hover:scale-105 transition duration-300">
          <FileText size={26} />
        </div>
        <h4 className="text-xs font-bold text-textPrimary line-clamp-1 w-full font-outfit" title={doc.title || doc.filename}>
          {doc.title || doc.filename}
        </h4>
        <span className="text-[11px] text-textMuted mt-0.5 font-mono">{formatSize(doc.size)} • .{ext || 'file'}</span>

        <span className={`mt-2.5 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider rounded-full border ${getStatusColor(doc.processing_status || 'ready')}`}>
          {doc.processing_status || 'READY'}
        </span>
      </div>
    </div>
  );
};
export default DocumentCard;
