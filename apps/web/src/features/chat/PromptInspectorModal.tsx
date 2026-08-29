import React, { useState } from 'react';
import {
  X,
  Terminal,
  Layers,
  FileText,
  Copy,
  Check,
  Zap,
  Sliders,
  ShieldAlert
} from 'lucide-react';
import { buildAssembledPrompt, BuildPromptPayload } from './api';
import { useAuth } from '../auth/auth-provider';

interface PromptInspectorModalProps {
  conversationId?: string;
  workspaceId?: string;
  isOpen: boolean;
  onClose: () => void;
}

export interface CitationSource {
  citation_index: number;
  citation_tag: string;
  chunk_id: string;
  document_id: string;
  title: string;
  section_title?: string;
  page_number?: number;
  score: number;
}

export interface PromptBuildResult {
  prompt: string;
  system_prompt: string;
  user_query: string;
  template_name: string;
  token_count: number;
  sources: CitationSource[];
  budget_summary: {
    max_total_tokens: number;
    system_tokens: number;
    context_tokens: number;
    history_tokens: number;
    query_tokens: number;
    chunks_count: number;
    history_count: number;
  };
}

export const PromptInspectorModal: React.FC<PromptInspectorModalProps> = ({
  conversationId,
  workspaceId,
  isOpen,
  onClose
}) => {
  const { token, user } = useAuth();
  const orgId = user?.organization_id || '';

  const [query, setQuery] = useState('');
  const [template, setTemplate] = useState('GeneralQA');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PromptBuildResult | null>(null);
  const [activeTab, setActiveTab] = useState<'prompt' | 'sources' | 'budget'>('prompt');
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const handleBuildPrompt = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || !token) return;
    try {
      setLoading(true);
      const res = await buildAssembledPrompt(token, orgId, {
        query: query.trim(),
        conversation_id: conversationId,
        workspace_id: workspaceId,
        template_name: template,
        top_k: 10,
        max_tokens: 8000
      });
      setResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const copyPrompt = () => {
    if (!result?.prompt) return;
    navigator.clipboard.writeText(result.prompt);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 bg-bgOverlay backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-bgDialog border border-borderColor rounded-2xl w-full max-w-4xl shadow-2xl flex flex-col max-h-[85vh] overflow-hidden">
        {/* Header */}
        <div className="p-4 px-6 border-b border-borderMuted flex items-center justify-between bg-bgHeader">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-accentSubtle border border-accent/20 text-accentText rounded-xl">
              <Terminal size={20} />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-textPrimary">
                Enterprise Prompt Builder & Context Inspector
              </h3>
              <p className="text-[11px] text-textMuted font-mono">
                Token Budgeting, Template Registry & Source Citations
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {result && (
              <button
                onClick={copyPrompt}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-bgTertiary hover:bg-bgHover text-textSecondary rounded-xl text-xs font-medium transition-colors border border-borderMuted"
              >
                {copied ? <Check size={13} className="text-successText" /> : <Copy size={13} />}
                <span>{copied ? 'Copied' : 'Copy Prompt'}</span>
              </button>
            )}
            <button onClick={onClose} className="p-1.5 text-textMuted hover:text-textPrimary rounded-lg hover:bg-bgHover">
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Input Bar */}
        <form onSubmit={handleBuildPrompt} className="p-5 border-b border-borderMuted bg-bgHeader flex items-center gap-3">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a test question to assemble a prompt..."
            className="flex-1 bg-bgInput border border-borderColor rounded-xl px-4 py-2.5 text-xs text-textPrimary placeholder-textMuted focus:outline-none focus:border-accent"
          />

          <select
            value={template}
            onChange={(e) => setTemplate(e.target.value)}
            className="bg-bgInput border border-borderColor text-xs text-textSecondary rounded-xl px-3 py-2.5 focus:outline-none"
          >
            <option value="GeneralQA">General QA</option>
            <option value="DocumentAnalysis">Document Analysis</option>
            <option value="Summarization">Summarization</option>
            <option value="CodeReview">Code Review</option>
            <option value="ProjectQuestions">Project Questions</option>
          </select>

          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-4 py-2.5 bg-accent hover:bg-accentHover disabled:opacity-50 text-white rounded-xl text-xs font-semibold flex items-center gap-2 transition-all"
          >
            <Zap size={14} className={loading ? 'animate-spin' : ''} />
            <span>{loading ? 'Assembling...' : 'Assemble Prompt'}</span>
          </button>
        </form>

        {/* Tab Selection */}
        {result && (
          <div className="flex border-b border-borderMuted bg-bgHeader px-6 gap-6 text-xs font-medium">
            <button
              onClick={() => setActiveTab('prompt')}
              className={`py-3 border-b-2 flex items-center gap-2 transition-colors ${
                activeTab === 'prompt'
                  ? 'border-accent text-accentText'
                  : 'border-transparent text-textMuted hover:text-textPrimary'
              }`}
            >
              <Terminal size={14} /> Assembled Prompt ({result.token_count} Tokens)
            </button>
            <button
              onClick={() => setActiveTab('sources')}
              className={`py-3 border-b-2 flex items-center gap-2 transition-colors ${
                activeTab === 'sources'
                  ? 'border-accent text-accentText'
                  : 'border-transparent text-textMuted hover:text-textPrimary'
              }`}
            >
              <FileText size={14} /> Citation Sources ({result.sources.length})
            </button>
            <button
              onClick={() => setActiveTab('budget')}
              className={`py-3 border-b-2 flex items-center gap-2 transition-colors ${
                activeTab === 'budget'
                  ? 'border-accent text-accentText'
                  : 'border-transparent text-textMuted hover:text-textPrimary'
              }`}
            >
              <Sliders size={14} /> Budget Allocation
            </button>
          </div>
        )}

        {/* Content View */}
        <div className="flex-1 overflow-y-auto p-6">
          {!result && !loading && (
            <div className="text-center py-16 text-textMuted space-y-2">
              <Terminal size={32} className="mx-auto text-textMuted mb-2" />
              <p className="text-xs font-medium text-textSecondary">
                Enter a question above to test the modular prompt builder.
              </p>
              <p className="text-[11px] text-textMuted">
                Inspect system prompts, token budgets, citation tags, and context assembly.
              </p>
            </div>
          )}

          {result && activeTab === 'prompt' && (
            <div className="space-y-4">
              <div className="bg-bgInput p-4 rounded-xl border border-borderColor text-xs text-textSecondary font-mono leading-relaxed whitespace-pre-wrap">
                {result.prompt}
              </div>
            </div>
          )}

          {result && activeTab === 'sources' && (
            <div className="space-y-4">
              {result.sources.map((src) => (
                <div key={src.chunk_id} className="bg-bgCard border border-borderColor rounded-xl p-4 space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-accentText bg-accentSubtle px-2 py-0.5 rounded text-[11px]">
                        {src.citation_tag}
                      </span>
                      <span className="text-textPrimary font-semibold">{src.title}</span>
                      {src.section_title && <span className="text-textMuted">• {src.section_title}</span>}
                    </div>
                    <span className="text-accentText font-mono text-[11px]">
                      Score: {Math.round(src.score * 100)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {result && activeTab === 'budget' && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
              <div className="bg-bgCard border border-borderColor p-4 rounded-xl">
                <span className="text-[10px] text-textMuted uppercase font-bold">Total Tokens</span>
                <p className="text-sm font-semibold text-accentText mt-1">{result.token_count} / {result.budget_summary.max_total_tokens}</p>
              </div>
              <div className="bg-bgCard border border-borderColor p-4 rounded-xl">
                <span className="text-[10px] text-textMuted uppercase font-bold">System Tokens</span>
                <p className="text-sm font-semibold text-textPrimary mt-1">{result.budget_summary.system_tokens}</p>
              </div>
              <div className="bg-bgCard border border-borderColor p-4 rounded-xl">
                <span className="text-[10px] text-textMuted uppercase font-bold">Retrieved Context</span>
                <p className="text-sm font-semibold text-textPrimary mt-1">{result.budget_summary.context_tokens} Tokens</p>
              </div>
              <div className="bg-bgCard border border-borderColor p-4 rounded-xl">
                <span className="text-[10px] text-textMuted uppercase font-bold">History Tokens</span>
                <p className="text-sm font-semibold text-textPrimary mt-1">{result.budget_summary.history_tokens} Tokens</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
