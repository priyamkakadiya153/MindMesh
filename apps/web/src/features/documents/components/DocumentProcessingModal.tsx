import React, { useState, useEffect } from 'react';
import {
  X,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Clock,
  Layers,
  Cpu,
  Hash,
  Copy,
  Check,
  Zap,
  Box
} from 'lucide-react';
import {
  getDocumentProcessingStatus,
  getDocumentChunks,
  reprocessDocument,
  getDocumentEmbeddingStatus,
  generateDocumentEmbeddings
} from '../api';
import { useAuth } from '../../auth/auth-provider';

interface DocumentProcessingModalProps {
  documentId: string | null;
  documentTitle?: string;
  onClose: () => void;
}

export interface ChunkItem {
  id: string;
  document_id: string;
  chunk_index: number;
  page_number?: number;
  section_title?: string;
  content: string;
  token_count: number;
  character_count: number;
  checksum: string;
  created_at: string;
}

export interface ProcessingJob {
  id: string;
  document_id: string;
  status: string;
  progress: number;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  retry_count: number;
  processing_time_ms: number;
}

export interface EmbeddingStatus {
  document_id: string;
  status: string;
  total_chunks: number;
  embedded_vectors: number;
  embedding_model: string;
  dimension: number;
  version: number;
  generated_at?: string;
}

export const DocumentProcessingModal: React.FC<DocumentProcessingModalProps> = ({
  documentId,
  documentTitle,
  onClose
}) => {
  const { token, user } = useAuth();
  const orgId = user?.current_organization_id || '';

  const [activeTab, setActiveTab] = useState<'status' | 'chunks' | 'embeddings'>('status');
  const [job, setJob] = useState<ProcessingJob | null>(null);
  const [chunks, setChunks] = useState<ChunkItem[]>([]);
  const [embStatus, setEmbStatus] = useState<EmbeddingStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [reprocessing, setReprocessing] = useState(false);
  const [embeddingLoading, setEmbeddingLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const loadData = async () => {
    if (!documentId || !token) return;
    try {
      setLoading(true);
      const [statusRes, chunksRes, embRes] = await Promise.all([
        getDocumentProcessingStatus(token, orgId, documentId).catch(() => null),
        getDocumentChunks(token, orgId, documentId).catch(() => []),
        getDocumentEmbeddingStatus(token, orgId, documentId).catch(() => null)
      ]);

      if (statusRes) setJob(statusRes);
      if (Array.isArray(chunksRes)) setChunks(chunksRes);
      if (embRes) setEmbStatus(embRes);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(() => {
      if (job && ['QUEUED', 'PROCESSING', 'RETRYING'].includes(job.status)) {
        loadData();
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [documentId, token]);

  const handleReprocess = async () => {
    if (!documentId || !token) return;
    try {
      setReprocessing(true);
      await reprocessDocument(token, orgId, documentId);
      await loadData();
    } catch (err) {
      console.error(err);
    } finally {
      setReprocessing(false);
    }
  };

  const handleGenerateEmbeddings = async () => {
    if (!documentId || !token) return;
    try {
      setEmbeddingLoading(true);
      await generateDocumentEmbeddings(token, orgId, documentId, { provider: 'gemini' });
      await loadData();
    } catch (err) {
      console.error(err);
    } finally {
      setEmbeddingLoading(false);
    }
  };

  const copyChunk = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  if (!documentId) return null;

  return (
    <div className="fixed inset-0 bg-bgOverlay backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-bgDialog border border-borderColor rounded-2xl w-full max-w-4xl shadow-2xl flex flex-col max-h-[85vh] overflow-hidden">
        {/* Header */}
        <div className="p-4 px-6 border-b border-borderMuted flex items-center justify-between bg-bgHeader">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-accentSubtle border border-accent/20 text-accentText rounded-xl">
              <Cpu size={20} />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-textPrimary">
                {documentTitle || 'Document Processing Inspector'}
              </h3>
              <p className="text-[11px] text-textMuted font-mono">
                Document ID: {documentId}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleReprocess}
              disabled={reprocessing}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-accent hover:bg-accentHover disabled:opacity-50 text-white rounded-xl text-xs font-medium transition-colors"
            >
              <RefreshCw size={13} className={reprocessing ? 'animate-spin' : ''} />
              <span>{reprocessing ? 'Queuing...' : 'Reprocess'}</span>
            </button>
            <button onClick={onClose} className="p-1.5 text-textMuted hover:text-textPrimary rounded-lg hover:bg-bgHover">
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Tab Selection */}
        <div className="flex border-b border-borderMuted bg-bgHeader px-6 gap-6 text-xs font-medium">
          <button
            onClick={() => setActiveTab('status')}
            className={`py-3 border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === 'status'
                ? 'border-accent text-accentText'
                : 'border-transparent text-textMuted hover:text-textPrimary'
            }`}
          >
            <Clock size={14} /> Pipeline Status
          </button>
          <button
            onClick={() => setActiveTab('chunks')}
            className={`py-3 border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === 'chunks'
                ? 'border-accent text-accentText'
                : 'border-transparent text-textMuted hover:text-textPrimary'
            }`}
          >
            <Layers size={14} /> Extracted Chunks ({chunks.length})
          </button>
          <button
            onClick={() => setActiveTab('embeddings')}
            className={`py-3 border-b-2 flex items-center gap-2 transition-colors ${
              activeTab === 'embeddings'
                ? 'border-accent text-accentText'
                : 'border-transparent text-textMuted hover:text-textPrimary'
            }`}
          >
            <Zap size={14} /> Vector Embeddings ({embStatus?.embedded_vectors || 0})
          </button>
        </div>

        {/* Content View */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {activeTab === 'status' && (
            <div className="space-y-6">
              {/* Status Badge & Progress */}
              <div className="bg-bgCard border border-borderColor rounded-xl p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-textMuted">Current Status:</span>
                    {renderStatusBadge(job?.status || 'QUEUED')}
                  </div>
                  <span className="text-xs font-mono font-bold text-accentText">
                    {Math.round(job?.progress || 0)}%
                  </span>
                </div>

                <div className="w-full bg-bgTertiary rounded-full h-2.5 overflow-hidden">
                  <div
                    className="bg-accent h-2.5 transition-all duration-500 rounded-full"
                    style={{ width: `${job?.progress || 0}%` }}
                  />
                </div>
              </div>

              {/* Job Metrics Table */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                <div className="bg-bgCard border border-borderColor p-3.5 rounded-xl">
                  <span className="text-[10px] text-textMuted uppercase font-bold tracking-wider">Processing Time</span>
                  <p className="text-sm font-semibold text-textPrimary mt-1">
                    {job?.processing_time_ms ? `${job.processing_time_ms} ms` : 'N/A'}
                  </p>
                </div>
                <div className="bg-bgCard border border-borderColor p-3.5 rounded-xl">
                  <span className="text-[10px] text-textMuted uppercase font-bold tracking-wider">Retry Count</span>
                  <p className="text-sm font-semibold text-textPrimary mt-1">
                    {job?.retry_count ?? 0}
                  </p>
                </div>
                <div className="bg-bgCard border border-borderColor p-3.5 rounded-xl">
                  <span className="text-[10px] text-textMuted uppercase font-bold tracking-wider">Total Chunks</span>
                  <p className="text-sm font-semibold text-textPrimary mt-1">
                    {chunks.length}
                  </p>
                </div>
                <div className="bg-bgCard border border-borderColor p-3.5 rounded-xl">
                  <span className="text-[10px] text-textMuted uppercase font-bold tracking-wider">Vector Status</span>
                  <p className="text-sm font-semibold text-accentText mt-1">
                    {embStatus?.embedded_vectors ? `${embStatus.embedded_vectors} Vectors` : 'Pending'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'chunks' && (
            <div className="space-y-4">
              {chunks.length === 0 ? (
                <div className="text-center py-12 text-textMuted text-xs">
                  No extracted chunks found for this document yet. Click "Reprocess" to generate chunks.
                </div>
              ) : (
                chunks.map((chunk) => (
                  <div
                    key={chunk.id}
                    className="bg-bgCard border border-borderColor rounded-xl p-4 space-y-3"
                  >
                    <div className="flex items-center justify-between text-xs border-b border-borderMuted pb-2">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-accentText bg-accentSubtle px-2 py-0.5 rounded text-[11px]">
                          Chunk #{chunk.chunk_index}
                        </span>
                        {chunk.section_title && (
                          <span className="text-textSecondary font-medium truncate max-w-xs">
                            Section: {chunk.section_title}
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-3 text-[11px] text-textMuted">
                        <span>{chunk.token_count} Tokens</span>
                        <span>{chunk.character_count} Chars</span>
                        <button
                          onClick={() => copyChunk(chunk.content, chunk.id)}
                          className="text-textMuted hover:text-textPrimary flex items-center gap-1"
                        >
                          {copiedId === chunk.id ? <Check size={12} className="text-successText" /> : <Copy size={12} />}
                        </button>
                      </div>
                    </div>

                    <div className="bg-bgInput p-3 rounded-lg border border-borderColor text-xs text-textSecondary font-mono leading-relaxed whitespace-pre-wrap">
                      {chunk.content}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === 'embeddings' && (
            <div className="space-y-6">
              <div className="bg-bgCard border border-borderColor rounded-xl p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <Box size={18} className="text-accentText" />
                    <h4 className="text-xs font-semibold text-textPrimary">pgvector Embedding Status</h4>
                  </div>
                  <button
                    onClick={handleGenerateEmbeddings}
                    disabled={embeddingLoading}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-accent hover:bg-accentHover disabled:opacity-50 text-white rounded-xl text-xs font-medium transition-colors"
                  >
                    <Zap size={13} className={embeddingLoading ? 'animate-spin' : ''} />
                    <span>{embeddingLoading ? 'Generating Vectors...' : 'Generate Vectors'}</span>
                  </button>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs pt-2">
                  <div className="bg-bgInput border border-borderColor p-3 rounded-lg">
                    <span className="text-[10px] text-textMuted uppercase font-bold">Model Name</span>
                    <p className="text-xs font-mono font-semibold text-accentText mt-1">
                      {embStatus?.embedding_model || 'text-embedding-004'}
                    </p>
                  </div>
                  <div className="bg-bgInput border border-borderColor p-3 rounded-lg">
                    <span className="text-[10px] text-textMuted uppercase font-bold">Vector Dimension</span>
                    <p className="text-xs font-mono font-semibold text-textPrimary mt-1">
                      {embStatus?.dimension ? `${embStatus.dimension} float32` : '768 float32'}
                    </p>
                  </div>
                  <div className="bg-bgInput border border-borderColor p-3 rounded-lg">
                    <span className="text-[10px] text-textMuted uppercase font-bold">Embedded Vectors</span>
                    <p className="text-xs font-semibold text-successText mt-1">
                      {embStatus?.embedded_vectors || 0} / {chunks.length} Chunks
                    </p>
                  </div>
                  <div className="bg-bgInput border border-borderColor p-3 rounded-lg">
                    <span className="text-[10px] text-textMuted uppercase font-bold">Embedding Version</span>
                    <p className="text-xs font-semibold text-textPrimary mt-1">
                      v{embStatus?.version || 1}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  function renderStatusBadge(statusStr: string) {
    switch (statusStr.toUpperCase()) {
      case 'COMPLETED':
      case 'EMBEDDED':
        return (
          <span className="px-2.5 py-1 bg-successBg border border-successBorder text-successText text-xs font-semibold rounded-full flex items-center gap-1">
            <CheckCircle2 size={12} /> Completed & Vectorized
          </span>
        );
      case 'PROCESSING':
        return (
          <span className="px-2.5 py-1 bg-accentSubtle border border-accent/30 text-accentText text-xs font-semibold rounded-full flex items-center gap-1">
            <RefreshCw size={12} className="animate-spin" /> Processing
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-1 bg-bgTertiary text-textMuted text-xs font-semibold rounded-full flex items-center gap-1">
            <Clock size={12} /> Queued
          </span>
        );
    }
  }
};
