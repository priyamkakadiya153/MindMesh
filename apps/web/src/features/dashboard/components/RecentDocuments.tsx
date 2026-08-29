import React, { useState } from 'react';
import { FolderOpen, Upload, ArrowRight, Eye, Download, ExternalLink, X, FileText, User, Calendar, CheckCircle2 } from 'lucide-react';
import { RecentDocument } from '../types';
import { EmptyState } from '../../../shared/components/EmptyState';
import { RecentListSkeleton, WidgetErrorCard } from './Skeletons';

interface RecentDocumentsProps {
  documents: RecentDocument[];
  onNavigateToDocuments: () => void;
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
}

export function RecentDocuments({
  documents = [],
  onNavigateToDocuments,
  loading,
  error,
  onRetry
}: RecentDocumentsProps) {
  const [selectedDoc, setSelectedDoc] = useState<RecentDocument | null>(null);

  if (error) {
    return <WidgetErrorCard title="Unable to load Recent Documents" message={error} onRetry={onRetry} />;
  }

  if (loading) {
    return <RecentListSkeleton title="Indexed Knowledge Base" count={4} />;
  }

  const formatBytes = (bytes: number) => {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const dm = 1;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return 'Recently';
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });
    } catch (e) {
      return dateStr;
    }
  };

  const handleDownload = (doc: RecentDocument) => {
    const link = document.createElement('a');
    link.href = `http://127.0.0.1:4000/api/v1/documents/${doc.id}/download`;
    link.download = doc.name;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="bg-bgCard border border-borderColor text-textPrimary rounded-2xl p-3.5 shadow-sm flex flex-col justify-between h-full">
      <div>
        <div className="flex items-center justify-between mb-2.5 pb-1.5 border-b border-borderColor">
          <h2 className="text-xs font-semibold text-textPrimary tracking-wide flex items-center gap-2">
            <FolderOpen size={15} className="text-accentText" aria-hidden="true" />
            <span>Indexed Knowledge Base</span>
          </h2>
          <span className="text-[9px] bg-successBg text-successText border border-successBorder px-2 py-0.5 rounded-full font-medium">
            {documents.length > 0 ? 'Active' : 'Empty'}
          </span>
        </div>

        {documents.length > 0 ? (
          <div className="overflow-x-auto pr-1">
            <table className="w-full text-left text-xs text-textSecondary" aria-label="Indexed Knowledge Base Documents">
              <thead>
                <tr className="border-b border-borderMuted pb-1.5 text-textMuted uppercase tracking-widest text-[9px] font-semibold">
                  <th scope="col" className="py-1.5 px-1">Document Name</th>
                  <th scope="col" className="py-1.5 px-1">Type</th>
                  <th scope="col" className="py-1.5 px-1">Size</th>
                  <th scope="col" className="py-1.5 px-1">Uploader</th>
                  <th scope="col" className="py-1.5 px-1">Date</th>
                  <th scope="col" className="py-1.5 px-1 text-center">Status</th>
                  <th scope="col" className="py-1.5 px-1 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-borderMuted">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-bgHover transition-colors group">
                    <td className="py-1.5 px-1 font-medium text-textPrimary group-hover:text-accentText max-w-[150px] truncate">
                      <button
                        type="button"
                        onClick={() => setSelectedDoc(doc)}
                        className="hover:underline text-left font-semibold text-textPrimary group-hover:text-accentText transition-colors flex items-center gap-1.5"
                        title={`Preview ${doc.name}`}
                      >
                        <FileText size={12} className="text-accentText shrink-0" />
                        <span className="truncate">{doc.name}</span>
                      </button>
                    </td>
                    <td className="py-1.5 px-1 text-textMuted text-[10px] uppercase">{doc.mime_type.split('/')[1] || doc.mime_type}</td>
                    <td className="py-1.5 px-1 text-textSecondary text-[10px]">{formatBytes(doc.size)}</td>
                    <td className="py-1.5 px-1 text-textMuted text-[10px] truncate max-w-[90px]">{doc.uploader_name || 'Member'}</td>
                    <td className="py-1.5 px-1 text-textMuted text-[10px]">{formatDate(doc.created_at)}</td>
                    <td className="py-1.5 px-1 text-center">
                      <span className="text-successText font-semibold uppercase tracking-wider text-[8px] bg-successBg/50 border border-successBorder/40 px-1.5 py-0.5 rounded-md">
                        {doc.processing_status || 'INDEXED'}
                      </span>
                    </td>
                    <td className="py-1.5 px-1 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          type="button"
                          onClick={() => setSelectedDoc(doc)}
                          title="Preview Document"
                          aria-label={`Preview ${doc.name}`}
                          className="p-1 rounded bg-bgTertiary hover:bg-accentSubtle text-textMuted hover:text-accentText transition-all"
                        >
                          <Eye size={11} />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDownload(doc)}
                          title="Download Document"
                          aria-label={`Download ${doc.name}`}
                          className="p-1 rounded bg-bgTertiary hover:bg-accentSubtle text-textMuted hover:text-accentText transition-all"
                        >
                          <Download size={11} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            title="No Documents Uploaded"
            description="Upload PDFs, TXT, or Markdown documents to enable AI retrieval."
            icon={FolderOpen}
            variant="card"
            primaryAction={{
              label: "Upload Document",
              onClick: onNavigateToDocuments,
              icon: Upload
            }}
          />
        )}
      </div>

      <button 
        type="button"
        onClick={onNavigateToDocuments}
        className="mt-2.5 w-full py-1.5 bg-accentSubtle text-accentText hover:bg-accent/20 text-xs font-semibold rounded-xl border border-accent/20 flex items-center justify-center gap-1.5 transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
      >
        <span>Open Knowledge Hub</span>
        <ArrowRight size={12} aria-hidden="true" />
      </button>

      {/* Document Preview Modal */}
      {selectedDoc && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 animate-fadeIn">
          <div className="bg-bgCard border border-borderColor rounded-2xl p-5 max-w-lg w-full shadow-2xl space-y-4">
            <div className="flex items-start justify-between border-b border-borderColor pb-3">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-accentSubtle text-accentText">
                  <FileText size={20} />
                </div>
                <div>
                  <h3 className="font-bold text-textPrimary text-sm sm:text-base leading-tight">
                    {selectedDoc.name}
                  </h3>
                  <span className="text-[10px] text-textMuted font-mono">
                    ID: {selectedDoc.id.substring(0, 12)}...
                  </span>
                </div>
              </div>
              <button
                onClick={() => setSelectedDoc(null)}
                className="p-1 rounded-lg text-textMuted hover:text-textPrimary hover:bg-bgHover transition-all"
              >
                <X size={16} />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-2.5 rounded-xl bg-bgTertiary border border-borderMuted space-y-1">
                <span className="text-[10px] text-textMuted uppercase font-semibold block">File Details</span>
                <p className="font-medium text-textPrimary">Size: {formatBytes(selectedDoc.size)}</p>
                <p className="text-textMuted text-[11px]">Type: {selectedDoc.mime_type}</p>
              </div>

              <div className="p-2.5 rounded-xl bg-bgTertiary border border-borderMuted space-y-1">
                <span className="text-[10px] text-textMuted uppercase font-semibold block">Metadata</span>
                <p className="font-medium text-textPrimary flex items-center gap-1">
                  <User size={10} className="text-accentText" /> {selectedDoc.uploader_name || 'Member'}
                </p>
                <p className="text-textMuted text-[11px] flex items-center gap-1">
                  <Calendar size={10} /> {formatDate(selectedDoc.created_at)}
                </p>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-accentSubtle/50 border border-accent/20 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2 text-successText font-semibold">
                <CheckCircle2 size={14} />
                <span>Processing Status: {selectedDoc.processing_status || 'INDEXED'}</span>
              </div>
              <span className="text-[9px] text-textMuted font-mono">Vectorized</span>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-borderColor">
              <button
                type="button"
                onClick={() => handleDownload(selectedDoc)}
                className="px-3.5 py-2 rounded-xl border border-borderColor bg-bgInput hover:bg-bgHover text-textPrimary text-xs font-semibold flex items-center gap-1.5 transition-all"
              >
                <Download size={13} />
                <span>Download</span>
              </button>
              <button
                type="button"
                onClick={() => {
                  setSelectedDoc(null);
                  onNavigateToDocuments();
                }}
                className="px-4 py-2 rounded-xl bg-accent hover:bg-accentHover text-white text-xs font-bold flex items-center gap-1.5 transition-all shadow-md shadow-accent/10"
              >
                <ExternalLink size={13} />
                <span>Open in Knowledge Hub</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
