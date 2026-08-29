import React, { useState, useEffect, useRef } from 'react';
import { Send, Sliders, AlertTriangle, MessageSquare, ShieldCheck } from 'lucide-react';
import { useAuth } from '../auth/auth-provider';
import { useWorkspaceStore } from '../workspace/store';
import {
  fetchConversations,
  fetchMessages,
  createConversation,
  createMessage,
  streamChatMessage,
  executeChat,
  updateConversation,
  pinConversation,
  deleteConversation,
  regenerateResponse,
  stopGeneration,
  exportConversation,
  ConversationItem,
  ChatMessage,
  CitationData,
  ActionProposalData
} from './chat-api';
import { ChatSidebar } from './components/ChatSidebar';
import { ChatMessageList } from './components/ChatMessageList';
import { SuggestedQuestions } from './components/SuggestedQuestions';
import { DocumentPreviewModal } from './components/DocumentPreviewModal';
import { ChatSettingsModal } from './components/ChatSettingsModal';
import { EvidenceViewer } from '../evidence/components/EvidenceViewer';
import { subscribeToChatSync } from './utils/chatSync';
import { ProactiveSuggestionCard } from './components/ProactiveSuggestionCard';
import {
  detectActionableSignal,
  dismissProactiveSuggestion,
  promoteProactiveSuggestion,
  ProactiveSuggestionItem
} from '../proactive-intelligence/proactive-detection-api';

export const EnterpriseAIChat: React.FC = () => {
  const { token, user } = useAuth();
  const { currentWorkspace } = useWorkspaceStore();

  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState('');
  
  const [historyLoading, setHistoryLoading] = useState(false);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Pagination state
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);

  // Streaming State
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingToken, setStreamingToken] = useState('');
  const abortControllerRef = useRef<AbortController | null>(null);

  // Modals
  const [previewCitation, setPreviewCitation] = useState<CitationData | null>(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [aiSettings, setAiSettings] = useState({
    provider: 'gemini',
    model: 'gemini-2.5-flash',
    temperature: 0.2,
    maxTokens: 1024,
    topP: 0.95,
    systemPrompt: ''
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [streamingActionProposal, setStreamingActionProposal] = useState<ActionProposalData | null>(null);
  const [proactiveSuggestion, setProactiveSuggestion] = useState<ProactiveSuggestionItem | null>(null);

  const handlePromoteSuggestion = async (sugg: ProactiveSuggestionItem, targetType: 'TASK' | 'REMINDER') => {
    if (!token) return;
    try {
      const res = await promoteProactiveSuggestion(token, sugg.id, targetType);
      if (res.proposal) {
        setStreamingActionProposal(res.proposal);
        setProactiveSuggestion(null);
      }
    } catch (err) {
      console.error("Failed to promote proactive suggestion:", err);
    }
  };

  const handleDismissSuggestion = async (id: string) => {
    if (token) {
      dismissProactiveSuggestion(token, id).catch(() => {});
    }
    setProactiveSuggestion(null);
  };

  // Helper: Deduplicate messages by stable ID and content
  const deduplicateMessages = (msgList: ChatMessage[]): ChatMessage[] => {
    const seen = new Set<string>();
    return msgList.filter(m => {
      if (!m) return false;
      const idKey = m.id ? `id-${m.id}` : null;
      const contentKey = `${m.role}-${(m.content || '').trim()}`;
      if ((idKey && seen.has(idKey)) || seen.has(contentKey)) return false;
      if (idKey) seen.add(idKey);
      seen.add(contentKey);
      return true;
    });
  };

  // 1. Load Conversations History with Pagination
  const loadConversations = async (resetPage: boolean = false) => {
    if (!token) return;
    try {
      setHistoryLoading(true);
      const nextPage = resetPage ? 1 : page;
      if (resetPage) setPage(1);

      const res = await fetchConversations(token, {
        workspace_id: currentWorkspace?.id,
        q: searchQuery || undefined,
        page: nextPage,
        limit: 20
      });

      if (resetPage) {
        setConversations(res.conversations);
      } else {
        setConversations(prev => [...prev, ...res.conversations]);
      }

      setHasMore(res.page < res.total_pages);
    } catch (err: any) {
      console.error("Failed to load conversations:", err);
    } finally {
      setHistoryLoading(false);
    }
  };

  useEffect(() => {
    loadConversations(true);
  }, [token, currentWorkspace?.id, searchQuery]);

  const handleLoadMore = () => {
    if (!hasMore || historyLoading) return;
    setPage(prev => prev + 1);
    loadConversations(false);
  };

  // Select Conversation with safe active stream abort
  const selectConversation = async (chatId: string) => {
    if (!token) return;
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsStreaming(false);
      setStreamingToken('');
    }
    try {
      setActiveChatId(chatId);
      setMessagesLoading(true);
      setErrorMessage(null);
      const msgList = await fetchMessages(token, chatId);
      setMessages(deduplicateMessages(msgList));
    } catch (err: any) {
      setErrorMessage("Unable to load conversation messages.");
    } finally {
      setMessagesLoading(false);
    }
  };

  // Multi-tab synchronization
  useEffect(() => {
    const unsub = subscribeToChatSync((evt) => {
      if (evt.conversationId === activeChatId && token) {
        fetchMessages(token, activeChatId).then(list => setMessages(deduplicateMessages(list)));
      }
    });
    return () => unsub();
  }, [activeChatId, token]);

  // 3. New Chat Creation
  const handleNewChat = async () => {
    if (!token) return;
    try {
      setErrorMessage(null);
      const newConv = await createConversation(token, {
        title: "New Conversation",
        workspace_id: currentWorkspace?.id
      });
      setActiveChatId(newConv.id);
      setMessages([]);
      loadConversations(true);
    } catch (err) {
      setErrorMessage("Unable to create new conversation.");
    }
  };

  // 4. Send Message Handler (Guarded against double submission & message duplication)
  const handleSendMessage = async (queryText?: string) => {
    const textToSend = queryText || inputQuery;
    if (!textToSend.trim() || !token || isSubmitting || isStreaming) return;

    setIsSubmitting(true);
    setErrorMessage(null);
    setInputQuery('');

    // Ensure conversation exists in DB first
    let currentConvId = activeChatId;
    if (!currentConvId) {
      try {
        const newConv = await createConversation(token, {
          title: textToSend.substring(0, 30) + "...",
          workspace_id: currentWorkspace?.id
        });
        currentConvId = newConv.id;
        setActiveChatId(currentConvId);
      } catch (err) {
        setErrorMessage("Failed to initialize conversation.");
        setIsSubmitting(false);
        return;
      }
    }

    const clientMsgId = crypto.randomUUID();

    // Optimistically add user message once
    const tempUserMsg: ChatMessage = {
      id: clientMsgId,
      conversation_id: currentConvId,
      role: 'user',
      content: textToSend,
      created_at: new Date().toISOString()
    };
    setMessages(prev => deduplicateMessages([...prev, tempUserMsg]));

    // Run AUTO-08 Proactive Detection Engine asynchronously in background
    if (token && textToSend.trim()) {
      detectActionableSignal(token, {
        text: textToSend,
        source_type: 'AI_CHAT',
        conversation_id: currentConvId || 'chat',
        history: messages.map(m => ({ sender: m.role, content: m.content }))
      }).then(res => {
        if (res.detected && res.suggestion) {
          setProactiveSuggestion(res.suggestion);
        }
      }).catch(() => {});
    }

    setIsStreaming(true);
    setStreamingToken('');

    try {
      const abortController = new AbortController();
      abortControllerRef.current = abortController;

      await streamChatMessage(
        token,
        {
          query: textToSend,
          chat_id: currentConvId,
          workspace_id: currentWorkspace?.id,
          organization_id: (currentWorkspace as any)?.organization_id || user?.current_organization_id,
          provider: aiSettings.provider,
          model: aiSettings.model,
          temperature: aiSettings.temperature,
          max_tokens: aiSettings.maxTokens,
          system_prompt: aiSettings.systemPrompt,
          client_message_id: clientMsgId
        },
        {
          signal: abortController.signal,
          onActionProposal: (prop) => {
            setStreamingActionProposal(prop);
          },
          onToken: (tok) => {
            setStreamingToken(prev => prev + tok);
          },
          onFinal: (payload) => {
            setIsStreaming(false);
            setIsSubmitting(false);
            const content = payload?.answer || payload?.content || streamingToken;
            const proposal = payload?.action_proposal || payload?.metadata?.action_proposal || streamingActionProposal;
            
            if (proposal) {
              const asstMsg: ChatMessage = {
                id: `asst-${Date.now()}`,
                conversation_id: currentConvId!,
                role: 'assistant',
                content: content || `I've prepared an action proposal: '${proposal.title}'. Please confirm below to proceed.`,
                action_proposal: proposal,
                created_at: new Date().toISOString()
              };
              setMessages(prev => deduplicateMessages([...prev, asstMsg]));
            } else if (content) {
              const asstMsg: ChatMessage = {
                id: `asst-${Date.now()}`,
                conversation_id: currentConvId!,
                role: 'assistant',
                content: content,
                created_at: new Date().toISOString()
              };
              setMessages(prev => deduplicateMessages([...prev, asstMsg]));
            }
            setStreamingToken('');
            setStreamingActionProposal(null);
            if (currentConvId) {
              loadConversations(true);
            }
          },
          onError: (err?: any) => {
            setIsStreaming(false);
            setIsSubmitting(false);
            setStreamingToken('');
            setStreamingActionProposal(null);
            const msg = typeof err === 'string' ? err : err?.message || "AI is temporarily rate-limited. Please try again shortly.";
            setErrorMessage(msg);
          }
        }
      );
    } catch (err: any) {
      console.error('Chat execution failed:', err);
      setIsStreaming(false);
      setIsSubmitting(false);
    } finally {
      setIsStreaming(false);
      setIsSubmitting(false);
      abortControllerRef.current = null;
    }
  };

  // 5. Actions
  const handleStopGeneration = async () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setIsStreaming(false);
    setStreamingToken('');
    if (activeChatId && token) {
      await stopGeneration(token, activeChatId);
    }
  };

  const handleRegenerate = async () => {
    if (!activeChatId || !token) return;
    try {
      setIsStreaming(true);
      await regenerateResponse(token, activeChatId);
      await selectConversation(activeChatId);
    } catch (err) {
      setErrorMessage("Failed to regenerate response.");
    } finally {
      setIsStreaming(false);
    }
  };

  const handleRename = async (id: string, newTitle: string) => {
    if (!token) return;
    try {
      await updateConversation(token, id, { title: newTitle });
      loadConversations(true);
    } catch (err) {
      console.error(err);
    }
  };

  const handleTogglePin = async (id: string, isPinned: boolean) => {
    if (!token) return;
    try {
      await pinConversation(token, id, isPinned);
      loadConversations(true);
    } catch (err) {
      console.error(err);
    }
  };

  const handleDelete = async (id: string) => {
    if (!token) return;
    if (confirm("Are you sure you want to delete this conversation?")) {
      try {
        await deleteConversation(token, id);
        if (activeChatId === id) {
          setActiveChatId(null);
          setMessages([]);
        }
        loadConversations(true);
      } catch (err) {
        console.error(err);
      }
    }
  };

  const handleExport = async (id: string, format: 'markdown' | 'json') => {
    if (!token) return;
    try {
      const data = await exportConversation(token, id, format);
      if (format === 'markdown') {
        const url = window.URL.createObjectURL(new Blob([data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `mindmesh_conversation_${id}.md`);
        document.body.appendChild(link);
        link.click();
        link.remove();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const activeConvObj = conversations.find(c => c.id === activeChatId);

  return (
    <div className="flex-1 min-h-0 h-full w-full flex flex-col md:flex-row bg-bgPrimary text-textPrimary overflow-hidden border border-borderColor rounded-2xl shadow-lg">
      {/* On Desktop: Side-by-Side Left Sidebar. On Mobile: Top Stacked Section */}
      <ChatSidebar
        conversations={conversations}
        activeConversationId={activeChatId}
        onSelectConversation={selectConversation}
        onNewChat={handleNewChat}
        onRenameConversation={handleRename}
        onDeleteConversation={handleDelete}
        onTogglePin={handleTogglePin}
        onExportConversation={handleExport}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        loading={historyLoading}
        hasMore={hasMore}
        onLoadMore={handleLoadMore}
      />

      {/* Main Chat View (Desktop right panel / Mobile bottom stacked panel) */}
      <div className="flex-1 flex flex-col h-full min-w-0 bg-bgPrimary">
        {/* Chat Header Bar */}
        <div className="p-3 px-4 border-b border-borderColor bg-bgHeader/90 backdrop-blur-md flex flex-wrap items-center justify-between gap-2.5 shrink-0">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="p-2 bg-accentSubtle border border-accent/25 rounded-xl text-accentText shrink-0 shadow-sm">
              <MessageSquare size={16} />
            </div>

            <div className="min-w-0 space-y-0.5">
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="font-semibold text-xs sm:text-sm truncate text-textPrimary">
                  {activeConvObj ? activeConvObj.title : 'Ask MindMesh'}
                </h2>
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-accentSubtle text-accentText border border-accent/20 shrink-0">
                  <span className="h-1.5 w-1.5 rounded-full bg-accent animate-pulse" /> MindMesh Intelligence — Grounded in Workspace Knowledge
                </span>
              </div>
              <p className="text-[10px] text-textMuted truncate flex items-center gap-1">
                Workspace: <span className="text-accentText font-medium">{currentWorkspace?.name || 'Primary Workspace'}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {/* Model Badge */}
            <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 bg-bgInput border border-borderColor rounded-xl text-[11px] text-textMuted font-mono">
              <ShieldCheck size={13} className="text-accentText" />
              <span>{aiSettings.model}</span>
            </div>

            {/* AI Settings Button */}
            <button
              type="button"
              onClick={() => setIsSettingsOpen(true)}
              aria-label="Open AI Settings"
              title="AI Settings"
              className="flex items-center gap-1.5 px-3 py-1.5 bg-bgInput hover:bg-bgHover border border-borderColor hover:border-accent/40 rounded-xl text-xs text-textSecondary hover:text-textPrimary font-medium transition-all active:scale-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >
              <Sliders size={14} className="text-accentText" aria-hidden="true" />
              <span>AI Settings</span>
            </button>
          </div>
        </div>

        {/* Error Alert */}
        {errorMessage && (
          <div role="alert" className="m-3 p-3 bg-dangerBg border border-dangerBorder rounded-xl text-xs text-dangerText flex items-center justify-between shadow-sm">
            <div className="flex items-center gap-2">
              <AlertTriangle size={15} className="text-dangerText shrink-0" aria-hidden="true" />
              <span>{errorMessage}</span>
            </div>
            <button type="button" onClick={() => setErrorMessage(null)} className="text-xs font-semibold hover:underline focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent rounded">Dismiss</button>
          </div>
        )}

        {/* Messages / Empty Welcome State */}
        {messages.length === 0 && !isStreaming ? (
          <SuggestedQuestions onSelectQuestion={(q) => handleSendMessage(q)} />
        ) : (
          <ChatMessageList
            messages={messages}
            streamingToken={streamingToken}
            streamingActionProposal={streamingActionProposal}
            isStreaming={isStreaming}
            onStopGeneration={handleStopGeneration}
            onRegenerateResponse={handleRegenerate}
            onPreviewCitation={(cit) => setPreviewCitation(cit)}
          />
        )}

        {/* Message Composer Input Bar */}
        <div className="p-3 sm:p-3.5 border-t border-borderColor bg-bgHeader/90 backdrop-blur-md">
          {/* Proactive Action & Deadline Suggestion Card */}
          {proactiveSuggestion && (
            <div className="max-w-4xl mx-auto px-1">
              <ProactiveSuggestionCard
                suggestion={proactiveSuggestion}
                onPromoteTask={(s) => handlePromoteSuggestion(s, 'TASK')}
                onPromoteReminder={(s) => handlePromoteSuggestion(s, 'REMINDER')}
                onDismiss={handleDismissSuggestion}
              />
            </div>
          )}

          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="relative flex items-center max-w-4xl mx-auto"
          >
            <label htmlFor="chat-input-field" className="sr-only">Ask MindMesh AI Engine</label>
            <input
              id="chat-input-field"
              type="text"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              disabled={isStreaming}
              placeholder="Ask MindMesh about documents, conversations, projects, decisions, or tasks..."
              aria-label="Ask MindMesh AI Engine"
              className="w-full pl-4 pr-12 py-3 bg-bgInput border border-borderColor hover:border-borderColor/80 focus:border-accent rounded-2xl text-xs text-textPrimary placeholder-textMuted outline-none transition-all duration-150 shadow-inner focus:ring-2 focus:ring-accent/20 focus-visible:ring-2 focus-visible:ring-accent disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={!inputQuery.trim() || isStreaming}
              className="absolute right-2 p-2 bg-accent hover:bg-accentHover text-white rounded-xl shadow-md shadow-accent/20 disabled:opacity-40 transition-all active:scale-95 flex items-center justify-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
              aria-label="Send message"
              title="Send message"
            >
              <Send size={15} aria-hidden="true" />
            </button>
          </form>
          <div className="flex items-center justify-between max-w-4xl mx-auto mt-2 text-[10px] text-textMuted px-1">
            <span>Powered by <strong className="text-textSecondary font-medium">MindMesh AI Engine</strong></span>
            <span className="hidden sm:inline">Enterprise Workspace Isolated • Grounded Knowledge Memory</span>
          </div>
        </div>
      </div>

      {/* Citation Preview Modal */}
      <DocumentPreviewModal
        citation={previewCitation}
        onClose={() => setPreviewCitation(null)}
      />

      {/* Workspace AI Settings Modal */}
      <ChatSettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        settings={aiSettings}
        onSaveSettings={(newSet) => setAiSettings(prev => ({ ...prev, ...newSet }))}
      />
    </div>
  );
};


