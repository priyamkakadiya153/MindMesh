import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../features/auth/auth-provider';
import { useWorkspaceStore } from '../../features/workspace/store';
import { useNavigationStore } from '../../features/navigation/store';
import {
  fetchProactiveSuggestions,
  dismissProactiveSuggestion,
  promoteProactiveSuggestion,
  ProactiveSuggestionItem
} from '../../features/proactive-intelligence/proactive-detection-api';
import { ActionProposalCard } from '../../features/chat/components/ActionProposalCard';
import { ErrorBoundary } from '../../components/common/ErrorBoundary';
import {
  Zap,
  CheckSquare,
  Bell,
  X,
  Calendar,
  User,
  MessageSquare,
  ExternalLink,
  Sparkles,
  Loader2,
  Filter,
  CheckCircle2,
  Clock,
  AlertCircle,
  Inbox
} from 'lucide-react';

export default function ActionInboxPage() {
  return (
    <ErrorBoundary title="Action Inbox unavailable">
      <ActionInboxContent />
    </ErrorBoundary>
  );
}

function ActionInboxContent() {
  const { setActiveTab } = useNavigationStore();
  const { token, user } = useAuth();
  const { currentWorkspace } = useWorkspaceStore();

  const [suggestions, setSuggestions] = useState<ProactiveSuggestionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter State
  const [statusFilter, setStatusFilter] = useState<'NEEDS_ATTENTION' | 'DEADLINES' | 'COMMITMENTS' | 'COMPLETED' | 'DISMISSED' | 'ALL'>('NEEDS_ATTENTION');
  const [sourceTypeFilter, setSourceTypeFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Active Action Proposal state for AUTO-06 Confirmation Card
  const [activeProposal, setActiveProposal] = useState<{ id: string; proposal: any } | null>(null);

  const loadSuggestions = useCallback(async () => {
    if (!token) return;
    try {
      setLoading(true);
      setError(null);

      let backendStatusFilter = 'DETECTED';
      if (statusFilter === 'COMPLETED') backendStatusFilter = 'ACCEPTED';
      else if (statusFilter === 'DISMISSED') backendStatusFilter = 'DISMISSED';
      else if (statusFilter === 'ALL') backendStatusFilter = 'ALL';

      const items = await fetchProactiveSuggestions(token, undefined, sourceTypeFilter, backendStatusFilter);
      setSuggestions(items);
    } catch (err: any) {
      console.error('Failed to load Action Inbox candidates:', err);
      setError('Failed to load candidate actions.');
    } finally {
      setLoading(false);
    }
  }, [token, statusFilter, sourceTypeFilter]);

  useEffect(() => {
    loadSuggestions();
  }, [loadSuggestions]);

  // Handle Promote to Task or Reminder
  const handlePromote = async (suggestion: ProactiveSuggestionItem, targetType: 'TASK' | 'REMINDER') => {
    if (!token) return;
    try {
      const res = await promoteProactiveSuggestion(token, suggestion.id, targetType);
      if (res.proposal) {
        setActiveProposal({ id: suggestion.id, proposal: res.proposal });
      }
      await loadSuggestions();
    } catch (err) {
      console.error('Failed to promote candidate in Action Inbox:', err);
    }
  };

  // Handle Dismiss Candidate
  const handleDismiss = async (suggestionId: string) => {
    if (!token) return;
    await dismissProactiveSuggestion(token, suggestionId);
    setSuggestions(prev => prev.filter(s => s.id !== suggestionId));
  };

  // Handle Open Conversation Handoff (AUTO-11B Source Message Deep Link)
  const handleOpenConversation = (convId: string, messageId?: string) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('mindmesh_selected_conv_id', convId);
      if (messageId) {
        localStorage.setItem('mindmesh_target_message_id', messageId);
      } else {
        localStorage.removeItem('mindmesh_target_message_id');
      }
    }
    setActiveTab('messages');
  };

  // Calculated Metric Summary Counts
  const needsAttentionCount = suggestions.filter(s => s.status === 'DETECTED' || s.status === 'PENDING' || s.status === 'PENDING_CONFIRMATION').length;
  const dueSoonCount = suggestions.filter(s => s.normalized_deadline && new Date(s.normalized_deadline).getTime() - Date.now() < 48 * 3600 * 1000).length;
  const deadlinesCount = suggestions.filter(s => s.deadline).length;
  const followupsCount = suggestions.filter(s => s.detected_action_type === 'TASK' || s.confidence_level === 'HIGH').length;

  // Filtered Display List
  const filteredItems = suggestions.filter(item => {
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchTitle = item.title.toLowerCase().includes(q);
      const matchContent = (item.source_content || '').toLowerCase().includes(q);
      const matchSource = (item.source_label || '').toLowerCase().includes(q);
      if (!matchTitle && !matchContent && !matchSource) return false;
    }

    if (statusFilter === 'DEADLINES') {
      return !!item.deadline;
    }
    if (statusFilter === 'COMMITMENTS') {
      return item.confidence_level === 'HIGH' || item.detected_action_type === 'TASK';
    }
    return true;
  });

  return (
    <div className="flex-1 min-h-0 h-full w-full flex flex-col bg-bgPrimary text-textPrimary overflow-hidden rounded-2xl border border-borderColor shadow-lg p-6 space-y-6">
      {/* Header & Subtitle */}
      <div className="flex items-center justify-between shrink-0">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400">
              <Zap className="w-5 h-5" />
            </div>
            <h1 className="text-xl font-bold text-textPrimary tracking-tight">Action Inbox & Intelligence Center</h1>
          </div>
          <p className="text-xs text-textMuted mt-1">
            Important actions, deadlines, commitments, and follow-ups detected from your workspace conversations.
          </p>
        </div>

        <button
          onClick={loadSuggestions}
          className="px-3.5 py-2 rounded-xl bg-bgTertiary hover:bg-borderColor text-textSecondary hover:text-textPrimary text-xs font-semibold flex items-center gap-2 transition-all cursor-pointer"
        >
          <Clock className="w-4 h-4" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Summary Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 shrink-0">
        <div className="p-4 rounded-2xl bg-bgSidebar border border-borderColor/80 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-xs text-textMuted">
            <span>Needs Attention</span>
            <AlertCircle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-black text-textPrimary">{needsAttentionCount}</div>
        </div>

        <div className="p-4 rounded-2xl bg-bgSidebar border border-borderColor/80 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-xs text-textMuted">
            <span>Due Soon</span>
            <Clock className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-black text-textPrimary">{dueSoonCount}</div>
        </div>

        <div className="p-4 rounded-2xl bg-bgSidebar border border-borderColor/80 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-xs text-textMuted">
            <span>Deadlines</span>
            <Calendar className="w-4 h-4 text-rose-400" />
          </div>
          <div className="text-2xl font-black text-textPrimary">{deadlinesCount}</div>
        </div>

        <div className="p-4 rounded-2xl bg-bgSidebar border border-borderColor/80 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-xs text-textMuted">
            <span>Follow-ups</span>
            <Sparkles className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-black text-textPrimary">{followupsCount}</div>
        </div>
      </div>

      {/* Toolbar Filters */}
      <div className="flex flex-wrap items-center justify-between gap-3 shrink-0 pt-2 border-t border-borderColor/40">
        {/* Status Tabs */}
        <div className="flex items-center gap-1.5 p-1 bg-bgSidebar rounded-xl border border-borderColor/60 text-xs">
          {[
            { id: 'NEEDS_ATTENTION', label: 'Needs Attention' },
            { id: 'DEADLINES', label: 'Deadlines' },
            { id: 'COMMITMENTS', label: 'Commitments' },
            { id: 'COMPLETED', label: 'Completed / Resolved' },
            { id: 'DISMISSED', label: 'Dismissed' },
            { id: 'ALL', label: 'All Candidates' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setStatusFilter(tab.id as any)}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all cursor-pointer ${
                statusFilter === tab.id
                  ? 'bg-accent text-white shadow-sm'
                  : 'text-textMuted hover:text-textPrimary hover:bg-bgHover'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Source Dropdown & Search */}
        <div className="flex items-center gap-2">
          <select
            value={sourceTypeFilter}
            onChange={(e) => setSourceTypeFilter(e.target.value)}
            className="px-3 py-1.5 bg-bgSidebar border border-borderColor rounded-xl text-xs font-semibold text-textPrimary focus:outline-none focus:border-accent cursor-pointer"
          >
            <option value="ALL">All Sources</option>
            <option value="COGNITIVE_AGENT">Cognitive Agent</option>
            <option value="DIRECT_MESSAGE">Direct Messages</option>
            <option value="GROUP_CHAT">Group Chat</option>
            <option value="PROJECT_CHANNEL">Project Channels</option>
          </select>

          <input
            type="text"
            placeholder="Search candidates..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="px-3 py-1.5 bg-bgSidebar border border-borderColor rounded-xl text-xs text-textPrimary placeholder:text-textMuted focus:outline-none focus:border-accent w-44"
          />
        </div>
      </div>

      {/* Main Candidate Stream View */}
      <div className="flex-1 min-h-0 overflow-y-auto space-y-4 pr-1">
        {loading ? (
          <div className="flex items-center justify-center h-48 text-xs text-textMuted">
            <Loader2 className="w-5 h-5 animate-spin mr-2 text-accentText" />
            Loading Action Inbox...
          </div>
        ) : error ? (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs text-center">
            {error}
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-textMuted text-xs space-y-3">
            <Inbox className="w-10 h-10 text-textMuted opacity-50" />
            <p className="font-semibold">No candidates found in Action Inbox.</p>
            <p className="text-[11px] text-textMuted max-w-sm text-center">
              When colleagues assign tasks, mention deadlines, or express commitments in Direct Messages or Group Chats, MindMesh will automatically place them here.
            </p>
          </div>
        ) : (
          filteredItems.map(item => (
            <div
              key={item.id}
              className="p-5 rounded-2xl bg-bgSidebar border border-borderColor/80 shadow-md space-y-4 hover:border-indigo-500/40 transition-all"
            >
              {/* Card Header & Status */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className={`text-[10px] font-extrabold uppercase tracking-wider px-2.5 py-0.5 rounded-full border ${
                    item.detected_action_type === 'TASK'
                      ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20'
                      : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                  }`}>
                    {item.detected_action_type} CANDIDATE
                  </span>

                  <span className="text-[10px] font-mono text-textMuted">
                    {new Date(item.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                    {Math.round(item.confidence * 100)}% Confidence ({item.confidence_level})
                  </span>

                  <button
                    onClick={() => handleDismiss(item.id)}
                    className="p-1 text-textMuted hover:text-textPrimary rounded-lg hover:bg-bgHover transition-colors"
                    title="Dismiss candidate"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Title & Quoted Message Snippet */}
              <div className="space-y-1.5">
                <h3 className="text-base font-bold text-textPrimary leading-snug">{item.title}</h3>
                {item.source_content && (
                  <p className="text-xs text-textMuted italic bg-bgCard p-2.5 rounded-xl border border-borderColor/60">
                    "{item.source_content}"
                  </p>
                )}
              </div>

              {/* Provenance Metadata Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 p-3 rounded-xl bg-bgCard border border-borderColor/60 text-xs">
                <div className="flex items-center gap-2 text-textSecondary">
                  <User className="w-4 h-4 text-indigo-400 shrink-0" />
                  <span>Assignee: <strong>{item.assignee_name || 'Current User'}</strong></span>
                </div>

                {item.deadline && (
                  <div className="flex items-center gap-2 text-textSecondary">
                    <Calendar className="w-4 h-4 text-rose-400 shrink-0" />
                    <span>Due: <strong>{item.deadline}</strong></span>
                  </div>
                )}

                {item.source_label && (
                  <div className="flex items-center gap-2 text-textSecondary truncate">
                    <MessageSquare className="w-4 h-4 text-amber-400 shrink-0" />
                    <span className="truncate">{item.source_label}</span>
                  </div>
                )}
              </div>

              {/* Action Buttons Toolbar */}
              <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-borderColor/40">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleOpenConversation(item.conversation_id, item.message_id)}
                    className="px-3 py-1.5 rounded-xl bg-bgHover hover:bg-borderColor text-textSecondary hover:text-textPrimary text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer"
                  >
                    <ExternalLink className="w-3.5 h-3.5 text-indigo-400" />
                    <span>{item.source_type === 'COGNITIVE_AGENT' ? 'Open Source' : 'Open Conversation'}</span>
                  </button>
                </div>

                {item.status === 'DETECTED' || item.status === 'PENDING' ? (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handlePromote(item, 'TASK')}
                      className="px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-sm flex items-center gap-1.5 transition-all cursor-pointer"
                    >
                      <CheckSquare className="w-3.5 h-3.5" />
                      <span>Create Task</span>
                    </button>

                    <button
                      onClick={() => handlePromote(item, 'REMINDER')}
                      className="px-3.5 py-1.5 rounded-xl bg-bgCard hover:bg-bgHover text-textPrimary text-xs font-semibold border border-borderColor flex items-center gap-1.5 transition-all cursor-pointer"
                    >
                      <Bell className="w-3.5 h-3.5 text-amber-400" />
                      <span>Remind Me</span>
                    </button>

                    <button
                      onClick={() => handleDismiss(item.id)}
                      className="px-3 py-1.5 rounded-xl bg-transparent hover:bg-bgHover text-textMuted hover:text-textPrimary text-xs transition-all cursor-pointer"
                    >
                      Dismiss
                    </button>
                  </div>
                ) : item.status === 'PENDING_CONFIRMATION' ? (
                  <span className="text-xs font-bold text-amber-400 flex items-center gap-1">
                    <AlertCircle className="w-4 h-4" />
                    <span>Pending Confirmation</span>
                  </span>
                ) : (
                  <span className="text-xs font-bold text-emerald-400 flex items-center gap-1">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Status: {item.status}</span>
                  </span>
                )}
              </div>

              {/* AUTO-06 Confirmation Card overlay for promoted action (persistent across navigation) */}
              {(item.status === 'PENDING_CONFIRMATION' || (activeProposal && activeProposal.id === item.id)) && (item.pending_proposal || activeProposal?.proposal) && (
                <div className="mt-3">
                  <ActionProposalCard
                    proposal={item.pending_proposal || activeProposal?.proposal}
                    onActionResult={() => {
                      setTimeout(() => {
                        setActiveProposal(null);
                        loadSuggestions();
                      }, 1000);
                    }}
                  />
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
