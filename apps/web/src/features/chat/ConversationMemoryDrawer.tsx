import React, { useState, useEffect } from 'react';
import {
  Brain,
  X,
  Pin,
  Trash2,
  RefreshCw,
  CheckCircle2,
  FileText,
  ListOrdered,
  Sparkles,
  Star
} from 'lucide-react';
import {
  getChatMemories,
  getChatSummaries,
  triggerSummarize,
  updateMemory,
  deleteMemory,
  MemoryItem,
  SummaryItem
} from './memory-api';
import { useAuth } from '../auth/auth-provider';

interface ConversationMemoryDrawerProps {
  conversationId: string;
  workspaceId: string;
  isOpen: boolean;
  onClose: () => void;
}

export const ConversationMemoryDrawer: React.FC<ConversationMemoryDrawerProps> = ({
  conversationId,
  workspaceId,
  isOpen,
  onClose
}) => {
  const { token, user } = useAuth();
  const orgId = user?.organization_id || '';

  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [summaries, setSummaries] = useState<SummaryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [summarizing, setSummarizing] = useState(false);

  const loadData = async () => {
    if (!token || !conversationId || !workspaceId) return;
    try {
      setLoading(true);
      const [memRes, sumRes] = await Promise.all([
        getChatMemories(token, orgId, workspaceId, conversationId).catch(() => []),
        getChatSummaries(token, orgId, conversationId).catch(() => [])
      ]);
      setMemories(memRes);
      setSummaries(sumRes);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) loadData();
  }, [isOpen, conversationId, workspaceId, token]);

  const handleTogglePin = async (mem: MemoryItem) => {
    if (!token) return;
    try {
      await updateMemory(token, orgId, mem.id, { is_pinned: !mem.is_pinned });
      await loadData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleDeleteMemory = async (memoryId: string) => {
    if (!token) return;
    try {
      await deleteMemory(token, orgId, memoryId);
      await loadData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleRegenerateSummary = async () => {
    if (!token || !conversationId || !workspaceId) return;
    try {
      setSummarizing(true);
      await triggerSummarize(token, orgId, { conversation_id: conversationId, workspace_id: workspaceId });
      await loadData();
    } catch (err) {
      console.error(err);
    } finally {
      setSummarizing(false);
    }
  };

  if (!isOpen) return null;

  const latestSummary = summaries[0];

  return (
    <div className="fixed inset-y-0 right-0 w-full max-w-md bg-bgSidebar border-l border-borderColor z-50 shadow-2xl flex flex-col">
      {/* Header */}
      <div className="p-4 px-6 border-b border-borderMuted flex items-center justify-between bg-bgHeader">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-accentSubtle border border-accent/20 text-accentText rounded-xl">
            <Brain size={18} />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-textPrimary">Conversation Memory & AI Summary</h3>
            <p className="text-[11px] text-textMuted font-mono">Long-Term Memory & Decision Records</p>
          </div>
        </div>
        <button onClick={onClose} className="p-1.5 text-textMuted hover:text-textPrimary rounded-lg hover:bg-bgHover">
          <X size={18} />
        </button>
      </div>

      {/* Content Body */}
      <div className="flex-1 overflow-y-auto p-5 space-y-5">
        {/* Action Button */}
        <button
          onClick={handleRegenerateSummary}
          disabled={summarizing}
          className="w-full bg-accent hover:bg-accentHover disabled:opacity-50 text-white rounded-xl p-2.5 text-xs font-semibold flex items-center justify-center gap-2 shadow-lg transition-colors"
        >
          <RefreshCw size={14} className={summarizing ? 'animate-spin' : ''} />
          <span>{summarizing ? 'Compressing History...' : 'Generate / Refresh AI Summary'}</span>
        </button>

        {/* Executive Summary Card */}
        {latestSummary && (
          <div className="bg-bgCard border border-borderColor rounded-xl p-4 space-y-3 shadow-md">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-accentText border-b border-borderMuted pb-2">
              <Sparkles size={14} /> Executive Summary (Msgs 1–{latestSummary.message_range_end})
            </div>
            <p className="text-xs font-mono text-textPrimary leading-relaxed">{latestSummary.summary}</p>

            {/* Key Decisions */}
            {latestSummary.key_decisions?.items && latestSummary.key_decisions.items.length > 0 && (
              <div className="space-y-1.5 pt-2 border-t border-borderMuted">
                <span className="text-[11px] font-semibold text-textSecondary flex items-center gap-1">
                  <CheckCircle2 size={12} className="text-successText" /> Key Decisions
                </span>
                <ul className="list-disc list-inside text-[11px] font-mono text-textMuted space-y-1">
                  {latestSummary.key_decisions.items.map((item, idx) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Pinned & Long-Term Memories List */}
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs font-semibold text-textSecondary">
            <span className="flex items-center gap-1.5"><Star size={14} className="text-amber-500" /> Pinned Facts & Memories ({memories.length})</span>
          </div>

          {memories.length === 0 ? (
            <p className="text-xs text-textMuted font-mono italic">No long-term memories or pinned facts saved yet.</p>
          ) : (
            <div className="space-y-2">
              {memories.map((mem) => (
                <div
                  key={mem.id}
                  className={`p-3 rounded-xl border transition-all ${
                    mem.is_pinned
                      ? 'bg-accentSubtle border-accent/30'
                      : 'bg-bgCard border-borderColor'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-xs font-mono text-textPrimary leading-normal flex-1">{mem.content}</p>
                    <div className="flex items-center gap-1 shrink-0">
                      <button
                        onClick={() => handleTogglePin(mem)}
                        className={`p-1.5 rounded-lg border text-xs transition-colors ${
                          mem.is_pinned
                            ? 'bg-amber-500/20 border-amber-500/40 text-amber-500'
                            : 'bg-bgTertiary border-borderMuted text-textMuted hover:text-textPrimary'
                        }`}
                      >
                        <Pin size={12} className={mem.is_pinned ? 'fill-current' : ''} />
                      </button>
                      <button
                        onClick={() => handleDeleteMemory(mem.id)}
                        className="p-1.5 text-textMuted hover:text-dangerText rounded-lg hover:bg-bgHover"
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
