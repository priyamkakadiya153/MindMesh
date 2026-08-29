import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../../features/auth/auth-provider';
import { useWorkspaceStore } from '../../features/workspace/store';
import { Conversation, Message, WSEventPayload, AttachmentItem } from '../../features/direct-messages/types';
import * as dmApi from '../../features/direct-messages/api';
import * as groupsApi from '../../features/direct-messages/groups-api';
import { useDirectMessagesWS } from '../../features/direct-messages/useDirectMessagesWS';
import { ConversationSidebar } from '../../features/direct-messages/components/ConversationSidebar';
import { MessageBubble } from '../../features/direct-messages/components/MessageBubble';
import { MessageComposer } from '../../features/direct-messages/components/MessageComposer';
import { TypingIndicator } from '../../features/direct-messages/components/TypingIndicator';
import { GroupHeader } from '../../features/direct-messages/components/GroupHeader';
import { GroupModal } from '../../features/direct-messages/components/GroupModal';
import { MemberListDrawer } from '../../features/direct-messages/components/MemberListDrawer';
import { FilePreviewModal } from '../../features/files/components/FilePreviewModal';
import { WebSocketProvider } from '../../features/direct-messages/WebSocketContext';
import { EmptyState } from '../../shared/components/EmptyState';
import { ErrorBoundary } from '../../components/common/ErrorBoundary';
import { AlertCircle, ArrowDown, Loader2, MessageSquare, Plus, UserPlus, Users } from 'lucide-react';
import { ProactiveSuggestionCard } from '../../features/chat/components/ProactiveSuggestionCard';
import { ActionProposalCard } from '../../features/chat/components/ActionProposalCard';
import {
  detectActionableSignal,
  fetchProactiveSuggestions,
  dismissProactiveSuggestion,
  promoteProactiveSuggestion,
  ProactiveSuggestionItem
} from '../../features/proactive-intelligence/proactive-detection-api';

export function DirectMessagesPage() {
  return (
    <ErrorBoundary title="Direct Messages system unavailable">
      <WebSocketProvider>
        <DirectMessagesContent />
      </WebSocketProvider>
    </ErrorBoundary>
  );
}

function DirectMessagesContent() {

  const { user, token, currentOrg } = useAuth();
  const { currentWorkspace } = useWorkspaceStore();

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConvId, setSelectedConvId] = useState<string | null>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('mindmesh_selected_conv_id');
    }
    return null;
  });
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoadingConversations, setIsLoadingConversations] = useState(true);
  const [conversationsError, setConversationsError] = useState<string | null>(null);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [messagesError, setMessagesError] = useState<string | null>(null);
  const [typingUser, setTypingUser] = useState<string | null>(null);
  const [orgMembers, setOrgMembers] = useState<any[]>([]);

  // AUTO-11B Source Message Deep Link & Highlight State
  const [targetMessageId, setTargetMessageId] = useState<string | null>(null);
  const [highlightedMessageId, setHighlightedMessageId] = useState<string | null>(null);
  const [sourceMessageMissing, setSourceMessageMissing] = useState<boolean>(false);

  // AUTO-08 Proactive Action Detection State
  const [proactiveSuggestion, setProactiveSuggestion] = useState<ProactiveSuggestionItem | null>(null);
  const [activeActionProposal, setActiveActionProposal] = useState<any | null>(null);

  const handlePromoteSuggestion = async (sugg: ProactiveSuggestionItem, targetType: 'TASK' | 'REMINDER') => {
    if (!token) return;
    try {
      const res = await promoteProactiveSuggestion(token, sugg.id, targetType);
      if (res.proposal) {
        setActiveActionProposal(res.proposal);
        setProactiveSuggestion(null);
      }
    } catch (err) {
      console.error('Failed to promote proactive suggestion in DM:', err);
    }
  };

  const handleDismissSuggestion = async (id: string) => {
    if (token) {
      dismissProactiveSuggestion(token, id).catch(() => {});
    }
    setProactiveSuggestion(null);
  };

  // Modals & Drawers
  const [isGroupModalOpen, setIsGroupModalOpen] = useState(false);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [previewAttachment, setPreviewAttachment] = useState<AttachmentItem | null>(null);

  // Scrolling State & Refs
  const messageEndRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const isAtBottomRef = useRef<boolean>(true);
  const prevMessagesRef = useRef<Message[]>([]);
  const prevSelectedConvIdRef = useRef<string | null>(null);
  const [showNewMessageIndicator, setShowNewMessageIndicator] = useState(false);

  const isSameId = useCallback((id1?: string | null, id2?: string | null) => {
    if (!id1 || !id2) return false;
    return id1.toLowerCase() === id2.toLowerCase();
  }, []);

  const activeConversation = conversations.find(c => isSameId(c?.id, selectedConvId));

  // Persist selected conversation ID and load target message ID
  useEffect(() => {
    if (selectedConvId && typeof window !== 'undefined') {
      localStorage.setItem('mindmesh_selected_conv_id', selectedConvId);
      const tId = localStorage.getItem('mindmesh_target_message_id');
      if (tId) {
        setTargetMessageId(tId);
        setSourceMessageMissing(false);
      }
    }
  }, [selectedConvId]);

  // Scroll Helper
  const scrollToBottom = useCallback((behavior: ScrollBehavior = 'smooth') => {
    if (messageEndRef.current) {
      messageEndRef.current.scrollIntoView({ behavior, block: 'end' });
    } else if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
    }
    isAtBottomRef.current = true;
    setShowNewMessageIndicator(false);
  }, []);

  // Handle Container Scroll Event
  const handleScroll = useCallback(() => {
    const container = scrollContainerRef.current;
    if (!container) return;

    const { scrollTop, scrollHeight, clientHeight } = container;
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight;
    const atBottom = distanceFromBottom <= 60;

    isAtBottomRef.current = atBottom;

    if (atBottom) {
      setShowNewMessageIndicator(false);
    }
  }, []);

  // Reset scroll state on conversation switch
  useEffect(() => {
    if (selectedConvId !== prevSelectedConvIdRef.current) {
      prevSelectedConvIdRef.current = selectedConvId;
      prevMessagesRef.current = [];
      isAtBottomRef.current = true;
      setShowNewMessageIndicator(false);
    }
  }, [selectedConvId]);

  // Fetch Organization Members
  useEffect(() => {
    if (!currentOrg?.id || !token) return;
    fetch(`/api/v1/members?organization_id=${currentOrg.id}`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(data => {
        if (Array.isArray(data)) {
          setOrgMembers(data.filter((m: any) => {
            const mUserId = m?.user_id || m?.user?.id;
            return mUserId && !isSameId(mUserId, user?.id);
          }));
        }
      })
      .catch(() => {});
  }, [currentOrg?.id, token, user?.id, isSameId]);

  // Load Conversations List (DMs + Groups + Channels)
  const loadConversations = useCallback(async (showLoading = false) => {
    if (!currentOrg?.id) {
      setIsLoadingConversations(false);
      return;
    }
    try {
      if (showLoading) {
        setIsLoadingConversations(true);
      }
      setConversationsError(null);
      const dms = await dmApi.listConversations(currentOrg.id, currentWorkspace?.id, token || undefined).catch(() => []);
      const groups = await groupsApi.listGroups(currentOrg.id, undefined, token || undefined).catch(() => []);
      
      // Combine and deduplicate cleanly by conversation type
      const convMap = new Map<string, Conversation>();
      if (Array.isArray(dms)) {
        dms.forEach(c => {
          if (c?.id && c.type === 'private') {
            convMap.set(c.id.toLowerCase(), c);
          }
        });
      }
      if (Array.isArray(groups)) {
        groups.forEach(c => {
          if (c?.id && (c.type === 'group' || c.type === 'project_channel' || c.type === 'announcement')) {
            convMap.set(c.id.toLowerCase(), c);
          }
        });
      }

      const combined = Array.from(convMap.values());
      setConversations(combined);

      setSelectedConvId(prev => prev || (combined[0]?.id || null));
    } catch (err: any) {
      console.error('Failed to load conversations:', err);
      setConversationsError(err.message || 'Failed to load conversations.');
    } finally {
      setIsLoadingConversations(false);
    }
  }, [currentOrg?.id, currentWorkspace?.id, token]);

  const currentOrgId = currentOrg?.id;
  const currentWsId = currentWorkspace?.id;

  useEffect(() => {
    loadConversations(true);
  }, [currentOrgId, currentWsId, token]);

  // Fetch active conversation details (with members if group)
  const loadActiveConversationDetails = useCallback(async (convId: string) => {
    try {
      const details = await groupsApi.getGroupDetails(convId, token || undefined);
      if (details) {
        setConversations(prev => prev.map(c => isSameId(c.id, convId) ? { ...c, ...details } : c));
      }
    } catch (err) {
      // 1-on-1 fallback
    }
  }, [token, isSameId]);

  // Load Messages for Selected Conversation (with AUTO-11B Target Message Pagination & Deep Link)
  const loadMessages = useCallback(async (convId: string) => {
    try {
      setIsLoadingMessages(true);
      setMessagesError(null);

      const tId = typeof window !== 'undefined' ? localStorage.getItem('mindmesh_target_message_id') : null;
      if (tId) {
        setTargetMessageId(tId);
      }

      let msgs = await dmApi.getMessages(convId, 100, 0, token || undefined);
      let list = Array.isArray(msgs) ? msgs : [];

      // If target message ID is specified but not in initial 100 messages, fetch deeper history (300 messages)
      if (tId && !list.some(m => isSameId(m.id, tId))) {
        const deeper = await dmApi.getMessages(convId, 300, 0, token || undefined).catch(() => []);
        if (Array.isArray(deeper) && deeper.length > 0) {
          list = deeper;
        }
      }

      const sorted = list.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
      setMessages(sorted);

      if (tId) {
        const targetMsg = sorted.find(m => isSameId(m.id, tId));
        if (!targetMsg || targetMsg.deleted) {
          setSourceMessageMissing(true);
          if (typeof window !== 'undefined') {
            localStorage.removeItem('mindmesh_target_message_id');
          }
        } else {
          setSourceMessageMissing(false);
        }
      }

      const hasUnreadFromOther = sorted.some(m => !isSameId(m.sender_id, user?.id) && m.status !== 'read');
      if (hasUnreadFromOther) {
        await dmApi.markConversationAsRead(convId, token || undefined).catch(() => {});
      }
      setConversations(prev => prev.map(c => isSameId(c.id, convId) ? { ...c, unread_count: 0 } : c));
      loadActiveConversationDetails(convId);
    } catch (err: any) {
      console.error('Failed to load messages:', err);
      setMessagesError(err.message || 'Failed to load message history');
      setMessages([]);
    } finally {
      setIsLoadingMessages(false);
    }
  }, [token, user?.id, loadActiveConversationDetails, isSameId]);

  useEffect(() => {
    if (selectedConvId) {
      loadMessages(selectedConvId);
    }
  }, [selectedConvId, loadMessages]);

  // Target Message Auto-Scroll & Highlight Effect (AUTO-11B)
  useEffect(() => {
    if (!targetMessageId || messages.length === 0) return;

    const targetIndex = messages.findIndex(m => isSameId(m.id, targetMessageId));
    if (targetIndex >= 0) {
      const targetMsg = messages[targetIndex];
      if (targetMsg.deleted) {
        setSourceMessageMissing(true);
        return;
      }

      setHighlightedMessageId(targetMessageId);

      const scrollTimer = setTimeout(() => {
        const el = document.getElementById(`message-${targetMessageId}`);
        if (el) {
          el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }, 150);

      const clearTimer = setTimeout(() => {
        setHighlightedMessageId(null);
        setTargetMessageId(null);
        if (typeof window !== 'undefined') {
          localStorage.removeItem('mindmesh_target_message_id');
        }
      }, 4000);

      return () => {
        clearTimeout(scrollTimer);
        clearTimeout(clearTimer);
      };
    }
  }, [messages, targetMessageId, isSameId]);

  // Auto-scroll to bottom for new messages (skip if deep-linking to a specific target message)
  useEffect(() => {
    if (isLoadingMessages || targetMessageId) return;
    if (messages.length === 0) return;

    const prevMsgs = prevMessagesRef.current;
    prevMessagesRef.current = messages;

    // First load of messages for selected conversation
    if (prevMsgs.length === 0) {
      const timer = setTimeout(() => {
        scrollToBottom('smooth');
      }, 50);
      return () => clearTimeout(timer);
    }

    // New messages added
    if (messages.length > prevMsgs.length) {
      const lastMsg = messages[messages.length - 1];
      const isSentByMe = isSameId(lastMsg.sender_id, user?.id);

      if (isSentByMe) {
        const timer = setTimeout(() => {
          scrollToBottom('smooth');
        }, 50);
        return () => clearTimeout(timer);
      } else if (isAtBottomRef.current) {
        const timer = setTimeout(() => {
          scrollToBottom('smooth');
        }, 50);
        return () => clearTimeout(timer);
      } else {
        setShowNewMessageIndicator(true);
      }
    }
  }, [messages, isLoadingMessages, user?.id, scrollToBottom, isSameId]);

  // WebSocket Event Handlers
  const handleWSMessageReceived = useCallback((payload: WSEventPayload) => {
    if (payload.event === 'new_message' && payload.message) {
      const newMsg = payload.message;
      if (isSameId(newMsg.conversation_id, selectedConvId)) {
        setMessages(prev => {
          const index = prev.findIndex(m => (newMsg.client_msg_id && m.client_msg_id === newMsg.client_msg_id) || isSameId(m.id, newMsg.id));
          let updated: Message[];
          if (index >= 0) {
            updated = [...prev];
            updated[index] = newMsg;
          } else {
            updated = [...prev, newMsg];
          }
          return updated.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
        });

        if (!isSameId(newMsg.sender_id, user?.id)) {
          dmApi.markConversationAsRead(newMsg.conversation_id, token || undefined).catch(() => {});

          if (token && newMsg.content) {
            detectActionableSignal(token, {
              text: newMsg.content,
              source_type: activeConversation?.type === 'group' ? 'GROUP_CHAT' : 'DIRECT_MESSAGE',
              conversation_id: newMsg.conversation_id,
              sender_name: newMsg.sender?.full_name || 'Member',
              history: messages.map(m => ({ sender: m.sender?.full_name, content: m.content }))
            }).then(res => {
              if (res.detected && res.suggestion) {
                setProactiveSuggestion(res.suggestion);
              }
            }).catch(() => {});
          }
        }
      }

      setConversations(prev => {
        const exists = prev.some(c => c && isSameId(c.id, newMsg.conversation_id));
        let list: Conversation[];
        if (exists) {
          list = prev.map(c => {
            if (isSameId(c.id, newMsg.conversation_id)) {
              const unread = (isSameId(newMsg.conversation_id, selectedConvId) || isSameId(newMsg.sender_id, user?.id)) ? 0 : (c.unread_count || 0) + 1;
              return { ...c, last_message: newMsg, last_message_at: newMsg.created_at, unread_count: unread, updated_at: new Date().toISOString() };
            }
            return c;
          });
        } else {
          loadConversations(false);
          return prev;
        }

        return list.sort((a, b) => {
          const timeA = new Date(a.last_message_at || a.created_at).getTime();
          const timeB = new Date(b.last_message_at || b.created_at).getTime();
          return timeB - timeA;
        });
      });
    } else if (payload.event === 'messages_read' && payload.conversation_id) {
      if (isSameId(payload.conversation_id, selectedConvId)) {
        setMessages(prev => prev.map(m => isSameId(m.sender_id, user?.id) ? { ...m, status: 'read' } : m));
      }
      setConversations(prev => prev.map(c => isSameId(c.id, payload.conversation_id) ? { ...c, unread_count: 0 } : c));
    } else if (payload.event === 'message_edited' && payload.message) {
      const editedMsg = payload.message;
      setMessages(prev => prev.map(m => isSameId(m.id, editedMsg.id) ? {
        ...m,
        content: editedMsg.content,
        edited: true,
        updated_at: editedMsg.updated_at || new Date().toISOString(),
        status: editedMsg.status || m.status
      } : m));
    } else if (payload.event === 'message_deleted' && payload.message) {
      const deletedMsg = payload.message;
      setMessages(prev => prev.map(m => isSameId(m.id, deletedMsg.id) ? { ...m, deleted: true, content: 'This message was deleted' } : m));
    }
  }, [selectedConvId, token, user?.id, loadConversations, isSameId]);

  const handleWSTypingStatusChanged = useCallback((payload: WSEventPayload) => {
    if (payload.conversation_id === selectedConvId) {
      setTypingUser(payload.is_typing ? (payload.user_name || 'Someone') : null);
    }
  }, [selectedConvId]);

  const handleWSPresenceUpdated = useCallback((payload: WSEventPayload) => {
    const pData = payload as any;
    const targetUserId = pData.user_id || pData.presence?.user_id;
    const newStatus = pData.status || pData.presence?.status;
    const newLastSeen = pData.last_seen || pData.presence?.last_seen;

    if (targetUserId && newStatus) {
      setConversations(prev => prev.map(c => {
        if (c.type === 'private' && c.participant && (c.participant.id === targetUserId || (c as any).participant_one === targetUserId || (c as any).participant_two === targetUserId)) {
          return {
            ...c,
            participant: {
              ...c.participant,
              status: newStatus as any,
              last_seen: newLastSeen || c.participant.last_seen
            }
          };
        }
        return c;
      }));
    }
  }, []);

  const handleGroupUpdatedWS = useCallback((payload?: WSEventPayload) => {
    if (payload?.event === 'group_deleted' || payload?.event === 'group.deleted') {
      const deletedConvId = payload.conversation_id || payload.group_id;
      if (deletedConvId && isSameId(deletedConvId, selectedConvId)) {
        setIsDrawerOpen(false);
        setSelectedConvId(null);
        setMessages([]);
      }
    }
    loadConversations(false);
  }, [loadConversations, selectedConvId, isSameId]);

  // Load Unresolved Proactive Action Candidates for Active Conversation (AUTO-08 / AUTO-09)
  useEffect(() => {
    if (!selectedConvId || !token) {
      setProactiveSuggestion(null);
      return;
    }
    let isMounted = true;
    fetchProactiveSuggestions(token, selectedConvId, undefined, 'NEEDS_ATTENTION')
      .then(items => {
        if (!isMounted) return;
        if (items && items.length > 0) {
          const activeSug = items.find(s => s.status === 'DETECTED' || s.status === 'PENDING' || s.status === 'PENDING_CONFIRMATION');
          if (activeSug) {
            setProactiveSuggestion(activeSug);
            if (activeSug.pending_proposal) {
              setActiveActionProposal(activeSug.pending_proposal);
            }
          } else {
            setProactiveSuggestion(null);
          }
        } else {
          setProactiveSuggestion(null);
        }
      })
      .catch(() => {
        if (isMounted) setProactiveSuggestion(null);
      });
    return () => { isMounted = false; };
  }, [selectedConvId, token]);

  const handleWSProactiveActionDetected = useCallback((payload: any) => {
    if (payload.event === 'proactive_action_detected' && payload.suggestion) {
      const sug = payload.suggestion;
      if (isSameId(sug.conversation_id, selectedConvId)) {
        setProactiveSuggestion(sug);
        if (sug.pending_proposal) {
          setActiveActionProposal(sug.pending_proposal);
        }
      }
    }
  }, [selectedConvId, isSameId]);

  const { sendTypingStart, sendTypingStop } = useDirectMessagesWS({
    token: token || null,
    onMessageReceived: handleWSMessageReceived,
    onTypingStatusChanged: handleWSTypingStatusChanged,
    onPresenceUpdated: handleWSPresenceUpdated,
    onGroupUpdated: handleGroupUpdatedWS,
    onProactiveActionDetected: handleWSProactiveActionDetected
  });

  const handleSendMessage = async (content: string, attachmentIds?: string[]) => {
    if (!selectedConvId || !user) return;
    const clientMsgId = `client-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
    const nowIso = new Date().toISOString();

    const optimisticMsg: Message = {
      id: clientMsgId,
      conversation_id: selectedConvId,
      sender_id: user.id,
      sender: {
        id: user.id,
        full_name: (user as any).full_name || (user as any).first_name || user.email || 'You',
        email: user.email,
        avatar_url: (user as any).avatar_url || null
      },
      message_type: 'text',
      content,
      reply_to_id: null,
      client_msg_id: clientMsgId,
      status: 'sending',
      edited: false,
      deleted: false,
      created_at: nowIso,
      updated_at: nowIso
    };

    // Optimistic UI insert
    setMessages(prev => [...prev, optimisticMsg]);
    setConversations(prev => prev.map(c => c.id === selectedConvId ? {
      ...c,
      last_message: {
        id: clientMsgId,
        sender_id: user.id,
        content: content || '📎 File Attachment',
        status: 'sending',
        created_at: nowIso,
        edited: false,
        deleted: false
      },
      last_message_at: nowIso,
      updated_at: nowIso
    } : c));

    // Run AUTO-08 Proactive Detection Engine asynchronously in background
    if (token && content.trim()) {
      detectActionableSignal(token, {
        text: content,
        source_type: activeConversation?.type === 'group' ? 'GROUP_CHAT' : 'DIRECT_MESSAGE',
        conversation_id: selectedConvId,
        sender_name: user?.username || 'User',
        history: messages.map(m => ({ sender: m.sender?.full_name, content: m.content }))
      }).then(res => {
        if (res.detected && res.suggestion) {
          setProactiveSuggestion(res.suggestion);
        }
      }).catch(() => {});
    }

    try {
      const sentMsg = await dmApi.sendMessage(selectedConvId, content, 'text', undefined, token || undefined, clientMsgId, attachmentIds);
      setMessages(prev => prev.map(m => (m.client_msg_id === clientMsgId || m.id === clientMsgId || m.id === sentMsg.id) ? sentMsg : m));
      setConversations(prev => prev.map(c => c.id === selectedConvId ? { ...c, last_message: sentMsg, last_message_at: sentMsg.created_at, updated_at: new Date().toISOString() } : c));
    } catch (err) {
      console.error('Failed to send message:', err);
      setMessages(prev => prev.map(m => (m.client_msg_id === clientMsgId || m.id === clientMsgId) ? { ...m, status: 'failed' } : m));
    }
  };

  const handleRetryMessage = async (failedMsg: Message) => {
    if (!selectedConvId || !failedMsg.content) return;
    const clientMsgId = failedMsg.client_msg_id || failedMsg.id;
    setMessages(prev => prev.map(m => (m.id === failedMsg.id || m.client_msg_id === clientMsgId) ? { ...m, status: 'sending' } : m));

    try {
      const sentMsg = await dmApi.sendMessage(selectedConvId, failedMsg.content, 'text', undefined, token || undefined, clientMsgId);
      setMessages(prev => prev.map(m => (m.client_msg_id === clientMsgId || m.id === failedMsg.id || m.id === sentMsg.id) ? sentMsg : m));
      setConversations(prev => prev.map(c => c.id === selectedConvId ? { ...c, last_message: sentMsg, last_message_at: sentMsg.created_at, updated_at: new Date().toISOString() } : c));
    } catch (err) {
      console.error('Failed to retry sending message:', err);
      setMessages(prev => prev.map(m => (m.id === failedMsg.id || m.client_msg_id === clientMsgId) ? { ...m, status: 'failed' } : m));
    }
  };

  const handleStartNewConversation = async (targetUserId: string) => {
    if (!currentOrg?.id) return;
    try {
      const conv = await dmApi.getOrCreatePrivateConversation(targetUserId, currentOrg.id, currentWorkspace?.id, token || undefined);
      setConversations(prev => {
        const exists = prev.some(c => c && c.id === conv.id);
        if (exists) {
          return prev.map(c => c && c.id === conv.id ? { ...c, ...conv } : c);
        }
        return [conv, ...prev];
      });
      setSelectedConvId(conv.id);
      loadMessages(conv.id);
      loadConversations();
    } catch (err) {
      console.error('Failed to create private conversation:', err);
    }
  };

  const handleCreateGroupSubmit = async (data: {
    name: string;
    description: string;
    type: 'group' | 'project_channel';
    visibility: 'public' | 'private' | 'read_only' | 'announcement';
    memberUserIds: string[];
  }) => {
    if (!currentOrg?.id) return;
    if (data.type === 'group') {
      const group = await groupsApi.createGroup({
        name: data.name,
        description: data.description,
        organization_id: currentOrg.id,
        workspace_id: currentWorkspace?.id,
        visibility: data.visibility,
        member_user_ids: data.memberUserIds
      }, token || undefined);
      await loadConversations();
      setSelectedConvId(group.id);
    } else {
      const channel = await groupsApi.createChannel({
        name: data.name,
        description: data.description,
        organization_id: currentOrg.id,
        workspace_id: currentWorkspace?.id,
        type: 'project_channel',
        visibility: data.visibility
      }, token || undefined);
      await loadConversations();
      setSelectedConvId(channel.id);
    }
  };

  const handleTogglePin = async () => {
    if (!selectedConvId) return;
    await groupsApi.togglePinConversation(selectedConvId, token || undefined);
    setConversations(prev => prev.map(c => c.id === selectedConvId ? { ...c, is_pinned: !c.is_pinned } : c));
  };

  const handleAddMember = async (userId: string) => {
    if (!selectedConvId) return;
    await groupsApi.addGroupMember(selectedConvId, userId, 'member', token || undefined);
    loadActiveConversationDetails(selectedConvId);
  };

  const handleRemoveMember = async (userId: string) => {
    if (!selectedConvId) return;
    try {
      await groupsApi.removeGroupMember(selectedConvId, userId, token || undefined);
      if (isSameId(userId, user?.id)) {
        setIsDrawerOpen(false);
        const remaining = conversations.filter(c => !isSameId(c.id, selectedConvId));
        setSelectedConvId(remaining[0]?.id || null);
        setMessages([]);
        loadConversations();
      } else {
        loadActiveConversationDetails(selectedConvId);
      }
    } catch (err: any) {
      alert(err.message || 'Failed to remove member.');
    }
  };

  const handleDeleteGroup = async () => {
    if (!selectedConvId) return;
    try {
      const targetId = selectedConvId;
      await groupsApi.deleteGroup(targetId, token || undefined);
      setIsDrawerOpen(false);
      const remaining = conversations.filter(c => !isSameId(c.id, targetId));
      setSelectedConvId(remaining[0]?.id || null);
      setMessages([]);
      loadConversations();
    } catch (err: any) {
      alert(err.message || 'Failed to delete group.');
    }
  };

  const handleUpdateGroup = async (name: string, description?: string) => {
    if (!selectedConvId) return;
    try {
      await groupsApi.updateGroup(selectedConvId, { name, description }, token || undefined);
      loadActiveConversationDetails(selectedConvId);
      loadConversations();
    } catch (err: any) {
      alert(err.message || 'Failed to update group.');
    }
  };

  const handleUpdateRole = async (userId: string, role: string) => {
    if (!selectedConvId) return;
    await groupsApi.updateMemberRole(selectedConvId, userId, role, token || undefined);
    loadActiveConversationDetails(selectedConvId);
  };

  const handleArchiveGroup = async () => {
    if (!selectedConvId) return;
    await groupsApi.toggleArchiveGroup(selectedConvId, token || undefined);
    loadConversations();
  };

  const handleEditMessage = async (messageId: string, currentContent: string) => {
    const newContent = prompt('Edit message:', currentContent);
    if (newContent && newContent.trim() !== currentContent) {
      await dmApi.editMessage(messageId, newContent.trim(), token || undefined);
      setMessages(prev => prev.map(m => m.id === messageId ? { ...m, content: newContent.trim(), edited: true } : m));
    }
  };

  const handleDeleteMessage = async (messageId: string) => {
    if (confirm('Are you sure you want to delete this message?')) {
      await dmApi.deleteMessage(messageId, token || undefined);
      setMessages(prev => prev.map(m => m.id === messageId ? { ...m, deleted: true, content: 'This message was deleted' } : m));
    }
  };

  return (
    <div className="flex-1 min-h-0 h-full w-full flex bg-bgPrimary text-textPrimary overflow-hidden rounded-2xl border border-borderColor shadow-lg">
      {/* Left Panel: Sidebar (Hidden on mobile when conversation selected) */}
      <div className={`w-full md:w-80 shrink-0 h-full min-h-0 ${selectedConvId ? 'hidden md:flex' : 'flex'}`}>
        <ConversationSidebar
          conversations={conversations}
          selectedId={selectedConvId}
          onSelectConversation={setSelectedConvId}
          orgMembers={orgMembers}
          onStartNewConversation={handleStartNewConversation}
          onOpenCreateGroupModal={() => setIsGroupModalOpen(true)}
        />
      </div>

      {/* Main Chat Panel */}
      <div className={`flex-1 flex flex-col h-full min-h-0 bg-bgPrimary min-w-0 ${!selectedConvId ? 'hidden md:flex' : 'flex'}`}>
        {activeConversation ? (
          <>
            {/* Mobile Back Header */}
            <div className="md:hidden shrink-0 p-2 bg-bgHeader border-b border-borderColor flex items-center gap-2">
              <button 
                onClick={() => setSelectedConvId(null)}
                className="px-2.5 py-1 bg-bgTertiary text-textSecondary hover:text-textPrimary text-xs rounded-lg font-semibold flex items-center gap-1"
              >
                ← Back
              </button>
              <span className="text-xs font-semibold truncate text-textPrimary">
                {activeConversation.type === 'private' ? activeConversation.participant.full_name : activeConversation.name}
              </span>
            </div>

            {/* Group / Channel Header */}
            <GroupHeader
              conversation={activeConversation}
              onTogglePin={handleTogglePin}
              onToggleDrawer={() => setIsDrawerOpen(prev => !prev)}
              isPinned={activeConversation.is_pinned}
            />

            {/* Source Message Deleted / Missing Fallback Notice (AUTO-11B) */}
            {sourceMessageMissing && (
              <div className="bg-amber-500/10 border-b border-amber-500/30 px-4 py-2 flex items-center justify-between text-xs text-amber-300 shrink-0">
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
                  <span>Original source message is no longer available.</span>
                </div>
                <button
                  onClick={() => setSourceMessageMissing(false)}
                  className="text-amber-400 hover:text-amber-200 text-xs font-bold cursor-pointer"
                >
                  Dismiss
                </button>
              </div>
            )}

            {/* Message Stream Container */}
            <div className="flex-1 relative min-h-0 flex flex-col overflow-hidden">
              <div 
                ref={scrollContainerRef}
                onScroll={handleScroll}
                className="flex-1 overflow-y-auto p-3 space-y-1.5"
              >
                {isLoadingMessages ? (
                  <div className="flex items-center justify-center h-full text-textMuted text-xs">
                    <Loader2 className="w-5 h-5 animate-spin mr-2 text-accentText" />
                    Loading messages...
                  </div>
                ) : messagesError ? (
                  <div className="flex flex-col items-center justify-center h-full text-textMuted text-xs space-y-3 p-4">
                    <p className="text-red-400 font-medium">{messagesError}</p>
                    <button
                      onClick={() => selectedConvId && loadMessages(selectedConvId)}
                      className="px-3 py-1.5 bg-accent text-white rounded-lg text-xs font-semibold hover:bg-accent/90 transition-colors"
                    >
                      Retry Loading Messages
                    </button>
                  </div>
                ) : messages.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full text-textMuted text-xs space-y-2">
                    <MessageSquare className="w-8 h-8 text-textMuted" />
                    <p>No messages yet. Send a message to start the conversation!</p>
                  </div>
                ) : (
                  messages.map((msg) => (
                    <MessageBubble
                      key={msg.id}
                      message={msg}
                      currentUserId={user?.id || ''}
                      isTargetHighlighted={isSameId(msg.id, highlightedMessageId)}
                      onEdit={handleEditMessage}
                      onDelete={handleDeleteMessage}
                      onRetry={handleRetryMessage}
                      onPreviewAttachment={setPreviewAttachment}
                    />
                  ))
                )}
                <div ref={messageEndRef} />
              </div>

              {/* Floating "New Messages ↓" Indicator */}
              {showNewMessageIndicator && (
                <button
                  onClick={() => scrollToBottom('smooth')}
                  className="absolute bottom-3 left-1/2 -translate-x-1/2 bg-accent text-white px-3.5 py-1.5 rounded-full shadow-lg hover:bg-accent/90 transition-all flex items-center gap-1.5 text-xs font-semibold z-20 cursor-pointer border border-white/20 animate-bounce"
                  aria-label="Scroll to latest message"
                >
                  <span>New Messages</span>
                  <ArrowDown className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            {/* Typing Indicator */}
            {typingUser && <TypingIndicator userName={typingUser} />}

            {/* Message Composer */}
            <MessageComposer
              conversationId={selectedConvId || undefined}
              onSendMessage={handleSendMessage}
              disabled={activeConversation.is_archived}
              onTypingStart={() => {
                if (selectedConvId && activeConversation?.participant?.id) {
                  sendTypingStart(selectedConvId, activeConversation.participant.id);
                }
              }}
              onTypingStop={() => {
                if (selectedConvId && activeConversation?.participant?.id) {
                  sendTypingStop(selectedConvId, activeConversation.participant.id);
                }
              }}
            />
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center p-4">
            <EmptyState
              title="No conversations yet"
              description="Start a direct conversation with a teammate or create a group chat."
              icon={MessageSquare}
              variant="card"
              primaryAction={{
                label: "New Message",
                onClick: () => {
                  const btn = document.querySelector('button[title*="Start Direct Message"], button:has(svg)') as HTMLButtonElement;
                  if (btn) btn.click();
                },
                icon: Plus
              }}
              secondaryAction={{
                label: "Invite Team Member",
                onClick: () => setIsGroupModalOpen(true),
                icon: UserPlus
              }}
            />
          </div>
        )}
      </div>

      {/* Right Drawer: Group Details & Members */}
      {activeConversation && activeConversation.type !== 'private' && (
        <MemberListDrawer
          isOpen={isDrawerOpen}
          onClose={() => setIsDrawerOpen(false)}
          conversation={activeConversation}
          currentUserId={user?.id || ''}
          orgMembers={orgMembers}
          onAddMember={handleAddMember}
          onRemoveMember={handleRemoveMember}
          onUpdateRole={handleUpdateRole}
          onArchiveGroup={handleArchiveGroup}
          onDeleteGroup={handleDeleteGroup}
          onUpdateGroup={handleUpdateGroup}
        />
      )}

      {/* Modal: Create Group / Channel */}
      <GroupModal
        isOpen={isGroupModalOpen}
        onClose={() => setIsGroupModalOpen(false)}
        onSubmit={handleCreateGroupSubmit}
        orgMembers={orgMembers}
      />

      {/* Modal: File Preview Overlay */}
      {previewAttachment && (
        <FilePreviewModal
          item={previewAttachment as any}
          onClose={() => setPreviewAttachment(null)}
        />
      )}
    </div>
  );
}
