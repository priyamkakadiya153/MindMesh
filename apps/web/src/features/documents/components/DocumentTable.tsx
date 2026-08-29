import React from 'react';
import { Document } from '../types';
import { Download, Edit2, Trash2, Eye, RotateCcw } from 'lucide-react';

interface DocumentTableProps {
  documents: Document[];
  selectedIds: string[];
  onToggleSelect: (id: string) => void;
  onSelectDoc: (id: string) => void;
  onRename?: (doc: Document) => void;
  onDelete?: (doc: Document) => void;
  onRestore?: (doc: Document) => void;
  onDownload?: (doc: Document) => void;
  isTrashView?: boolean;
}

export const DocumentTable: React.FC<DocumentTableProps> = ({
  documents,
  selectedIds,
  onToggleSelect,
  onSelectDoc,
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
    const b = bytes || 0;
    if (b === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(b) / Math.log(k));
    return parseFloat((b / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  return (
    <div className="overflow-x-auto w-full rounded-2xl border border-borderColor bg-bgCard backdrop-blur-xl">
      <table className="w-full text-left text-xs text-textSecondary border-collapse">
        <thead className="bg-bgTertiary text-textMuted text-[11px] font-semibold uppercase tracking-wider border-b border-borderMuted">
          <tr>
            <th className="p-3 w-10"></th>
            <th className="p-3">Name</th>
            <th className="p-3">Status</th>
            <th className="p-3">Ext</th>
            <th className="p-3">Size</th>
            <th className="p-3">Uploaded At</th>
            <th className="p-3 text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-borderMuted">
          {documents.map((doc) => {
            const isSelected = selectedIds.includes(doc.id);
            const ext = (doc.extension || doc.filename.split('.').pop() || '').toLowerCase();

            return (
              <tr 
                key={doc.id} 
                onClick={() => onSelectDoc(doc.id)}
                className={`hover:bg-bgHover transition cursor-pointer ${
                  isSelected ? 'bg-accentSubtle' : ''
                }`}
              >
                <td className="p-3" onClick={(e) => { e.stopPropagation(); onToggleSelect(doc.id); }}>
                  <div className={`w-4 h-4 rounded-md border flex items-center justify-center transition ${
                    isSelected ? 'bg-accent border-accent text-white' : 'border-borderMuted hover:border-borderColor'
                  }`}>
                    {isSelected && (
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={3} stroke="currentColor" className="w-3 h-3">
                        <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                      </svg>
                    )}
                  </div>
                </td>
                <td className="p-3 font-semibold text-textPrimary max-w-[220px] truncate font-outfit">
                  {doc.title || doc.filename}
                </td>
                <td className="p-3">
                  <span className={`px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider rounded-full border ${getStatusColor(doc.processing_status || 'READY')}`}>
                    {doc.processing_status || 'READY'}
                  </span>
                </td>
                <td className="p-3 font-mono text-textMuted uppercase">.{ext || 'file'}</td>
                <td className="p-3 text-textMuted">{formatSize(doc.size || doc.size_bytes)}</td>
                <td className="p-3 text-textMuted">
                  {doc.created_at ? new Date(doc.created_at).toLocaleDateString() : 'N/A'}
                </td>
                <td className="p-3 text-right" onClick={(e) => e.stopPropagation()}>
                  <div className="flex items-center justify-end gap-1">
                    <button
                      onClick={() => onSelectDoc(doc.id)}
                      className="p-1 rounded-lg hover:bg-bgHover text-textMuted hover:text-textPrimary transition"
                      title="Preview Document"
                    >
                      <Eye size={13} />
                    </button>
                    {onDownload && (
                      <button
                        onClick={() => onDownload(doc)}
                        className="p-1 rounded-lg hover:bg-bgHover text-textMuted hover:text-textPrimary transition"
                        title="Download Original"
                      >
                        <Download size={13} />
                      </button>
                    )}
                    {!isTrashView && onRename && (
                      <button
                        onClick={() => onRename(doc)}
                        className="p-1 rounded-lg hover:bg-bgHover text-textMuted hover:text-accentText transition"
                        title="Rename"
                      >
                        <Edit2 size={13} />
                      </button>
                    )}
                    {isTrashView && onRestore ? (
                      <button
                        onClick={() => onRestore(doc)}
                        className="p-1 rounded-lg hover:bg-bgHover text-emerald-500 transition"
                        title="Restore Document"
                      >
                        <RotateCcw size={13} />
                      </button>
                    ) : onDelete ? (
                      <button
                        onClick={() => onDelete(doc)}
                        className="p-1 rounded-lg hover:bg-bgHover text-dangerText transition"
                        title="Delete Document"
                      >
                        <Trash2 size={13} />
                      </button>
                    ) : null}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
export default DocumentTable;
