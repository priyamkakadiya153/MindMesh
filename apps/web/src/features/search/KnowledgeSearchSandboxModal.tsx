import React, { useState } from 'react';
import {
  Search,
  X,
  Sparkles,
  Layers,
  FileText,
  Clock,
  Zap,
  Filter,
  CheckCircle2
} from 'lucide-react';
import { searchHybridKnowledge, HybridSearchPayload } from './api';
import { useAuth } from '../auth/auth-provider';

interface KnowledgeSearchSandboxModalProps {
  workspaceId?: string;
  isOpen: boolean;
  onClose: () => void;
}

export interface RetrievedChunk {
  chunk_id: string;
  document_id: string;
  title: string;
  section_title?: string;
  page_number?: number;
  content: string;
  token_count: number;
  score: number;
  match_type: string;
  file_type?: string;
}

export const KnowledgeSearchSandboxModal: React.FC<KnowledgeSearchSandboxModalProps> = ({
  workspaceId,
  isOpen,
  onClose
}) => {
  const { token, user } = useAuth();
  const orgId = user?.current_organization_id || '';

  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(10);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<{
    latency_ms: number;
    total_candidates_found: number;
    chunks: RetrievedChunk[];
  } | null>(null);

  if (!isOpen) return null;

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || !token) return;
    try {
      setLoading(true);
      const res = await searchHybridKnowledge(token, orgId, {
        query: query.trim(),
        workspace_id: workspaceId,
        top_k: topK
      });
      setResults(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-bgOverlay backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-bgDialog border border-borderColor rounded-2xl w-full max-w-4xl shadow-2xl flex flex-col max-h-[85vh] overflow-hidden">
        {/* Header */}
        <div className="p-4 px-6 border-b border-borderColor flex items-center justify-between bg-bgHeader">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-accentSubtle border border-accent/20 text-accentText rounded-xl">
              <Sparkles size={20} />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-textPrimary">
                Hybrid Knowledge Retrieval Engine
              </h3>
              <p className="text-[11px] text-textMuted font-mono">
                pgvector Cosine Similarity + PostgreSQL Full-Text Search
              </p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 text-textMuted hover:text-textPrimary rounded-lg hover:bg-bgHover">
            <X size={18} />
          </button>
        </div>

        {/* Query Form Bar */}
        <form onSubmit={handleSearch} className="p-5 border-b border-borderColor bg-bgTertiary flex items-center gap-3">
          <div className="relative flex-1">
            <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-textMuted" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask a question or search keywords across document knowledge..."
              className="w-full bg-bgInput border border-borderColor rounded-xl pl-10 pr-4 py-2.5 text-xs text-textPrimary placeholder-textMuted focus:outline-none focus:border-accent"
            />
          </div>

          <div className="flex items-center gap-2">
            <select
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="bg-bgInput border border-borderColor text-xs text-textPrimary rounded-xl px-3 py-2.5 focus:outline-none"
            >
              <option value={5}>Top 5</option>
              <option value={10}>Top 10</option>
              <option value={20}>Top 20</option>
            </select>

            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="px-4 py-2.5 bg-accent hover:bg-accentHover disabled:opacity-50 text-white rounded-xl text-xs font-semibold flex items-center gap-2 transition-all shadow-lg shadow-accent/10"
            >
              <Zap size={14} className={loading ? 'animate-spin' : ''} />
              <span>{loading ? 'Retrieving...' : 'Search Context'}</span>
            </button>
          </div>
        </form>

        {/* Results Metadata & List */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {results && (
            <div className="flex items-center justify-between text-xs text-textMuted bg-bgTertiary p-3 px-4 rounded-xl border border-borderColor">
              <span className="flex items-center gap-1.5 font-medium text-textPrimary">
                <CheckCircle2 size={13} className="text-successText" />
                Retrieved {results.chunks.length} chunks (from {results.total_candidates_found} candidates)
              </span>
              <span className="font-mono text-[11px] text-accentText">
                Latency: {results.latency_ms} ms
              </span>
            </div>
          )}

          {!results && !loading && (
            <div className="text-center py-16 text-textMuted space-y-2">
              <Search size={32} className="mx-auto text-textMuted mb-2" />
              <p className="text-xs font-medium text-textSecondary">
                Enter a question or search query above to test hybrid retrieval.
              </p>
              <p className="text-[11px] text-textMuted">
                Results combine semantic vector embeddings and full-text keyword matching using RRF reranking.
              </p>
            </div>
          )}

          {results?.chunks.map((chunk, idx) => (
            <div
              key={chunk.chunk_id}
              className="bg-bgTertiary border border-borderMuted hover:border-accent/40 rounded-xl p-4 space-y-3 transition-colors"
            >
              <div className="flex items-center justify-between text-xs border-b border-borderMuted pb-2">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-textMuted text-[11px]">
                    #{idx + 1}
                  </span>
                  <span className="text-textPrimary font-semibold truncate max-w-xs flex items-center gap-1.5">
                    <FileText size={13} className="text-accentText" />
                    {chunk.title}
                  </span>
                  {chunk.section_title && (
                    <span className="text-textMuted text-[11px] truncate max-w-xs">
                      • {chunk.section_title}
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  {renderMatchTypeBadge(chunk.match_type)}
                  <span className="px-2 py-0.5 bg-accentSubtle border border-accent/30 text-accentText font-mono text-[11px] font-bold rounded">
                    {Math.round(chunk.score * 100)}% Match
                  </span>
                </div>
              </div>

              {/* Chunk Content Text */}
              <div className="bg-bgCard p-3 rounded-lg border border-borderMuted text-xs text-textSecondary font-mono leading-relaxed whitespace-pre-wrap">
                {chunk.content}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  function renderMatchTypeBadge(matchType: string) {
    switch (matchType) {
      case 'hybrid':
        return (
          <span className="px-2 py-0.5 bg-violet-500/10 border border-violet-500/30 text-purple-600 dark:text-purple-300 text-[10px] font-bold rounded uppercase">
            Hybrid RRF
          </span>
        );
      case 'vector':
        return (
          <span className="px-2 py-0.5 bg-blue-500/10 border border-blue-500/30 text-blue-600 dark:text-blue-300 text-[10px] font-bold rounded uppercase">
            Vector
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 bg-emerald-500/10 border border-emerald-500/30 text-emerald-600 dark:text-emerald-300 text-[10px] font-bold rounded uppercase">
            Keyword FTS
          </span>
        );
    }
  }
};
