import React, { useState, useEffect } from 'react';
import { FileText, X, Bookmark, Layers, Hash, Sparkles } from 'lucide-react';
import { getDocumentChunkPreview, ChunkPreview } from './citation-api';
import { useAuth } from '../auth/auth-provider';

interface DocumentPreviewModalProps {
  documentId: string;
  chunkId: string;
  isOpen: boolean;
  onClose: () => void;
}

export const DocumentPreviewModal: React.FC<DocumentPreviewModalProps> = ({
  documentId,
  chunkId,
  isOpen,
  onClose
}) => {
  const { token, user } = useAuth();
  const orgId = user?.organization_id || '';

  const [preview, setPreview] = useState<ChunkPreview | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || !documentId || !chunkId || !token) return;

    const loadChunk = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await getDocumentChunkPreview(token, orgId, documentId, chunkId);
        setPreview(data);
      } catch (err: any) {
        setError(err.message || 'Failed to load chunk preview.');
      } finally {
        setLoading(false);
      }
    };

    loadChunk();
  }, [isOpen, documentId, chunkId, token]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-bgOverlay backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-bgDialog border border-borderColor rounded-2xl w-full max-w-3xl shadow-2xl flex flex-col max-h-[85vh] overflow-hidden">
        {/* Header */}
        <div className="p-4 px-6 border-b border-borderMuted flex items-center justify-between bg-bgHeader">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-accentSubtle border border-accent/20 text-accentText rounded-xl">
              <FileText size={18} />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-textPrimary">
                {preview ? preview.document_title : 'Document Source Chunk Preview'}
              </h3>
              <p className="text-[11px] text-textMuted font-mono">Verifiable Source Citation Evidence</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 text-textMuted hover:text-textPrimary rounded-lg hover:bg-bgHover">
            <X size={18} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {loading && (
            <div className="py-12 text-center text-xs text-textMuted animate-pulse">
              Loading document chunk preview...
            </div>
          )}

          {error && (
            <div className="p-4 bg-dangerBg border border-dangerBorder text-dangerText rounded-xl text-xs">
              {error}
            </div>
          )}

          {preview && !loading && (
            <>
              {/* Metadata Pills */}
              <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
                {preview.page_number && (
                  <span className="px-2.5 py-1 bg-bgTertiary text-accentText rounded-lg flex items-center gap-1.5 border border-borderMuted">
                    <Bookmark size={12} /> Page {preview.page_number}
                  </span>
                )}
                {preview.section_title && (
                  <span className="px-2.5 py-1 bg-bgTertiary text-textSecondary rounded-lg flex items-center gap-1.5 border border-borderMuted">
                    <Layers size={12} /> Section: {preview.section_title}
                  </span>
                )}
                <span className="px-2.5 py-1 bg-bgTertiary text-textMuted rounded-lg flex items-center gap-1.5 border border-borderMuted">
                  <Hash size={12} /> {preview.character_count} chars
                </span>
              </div>

              {/* Chunk Highlight Card */}
              <div className="bg-bgCard border border-borderColor rounded-xl p-5 space-y-2">
                <div className="flex items-center gap-2 text-[11px] text-accentText font-semibold uppercase tracking-wider">
                  <Sparkles size={12} /> Referenced Context Snippet
                </div>
                <div className="text-xs font-mono text-textPrimary leading-relaxed whitespace-pre-wrap">
                  {preview.text}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
