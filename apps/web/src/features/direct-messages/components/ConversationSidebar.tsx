import React, { useState } from 'react';
import { Conversation } from '../types';
import { OnlineBadge } from './OnlineBadge';
import { EmptyState } from '../../../shared/components/EmptyState';
import { Search, Plus, UserPlus, MessageSquare, Users, Hash, Pin } from 'lucide-react';

interface OrgMemberItem {
  id?: string;
  user_id: string;
  username?: string;
  email?: string;
  first_name?: string | null;
  last_name?: string | null;
  display_name?: string | null;
  full_name?: string | null;
  avatar_url?: string | null;
  user?: {
    id?: string;
    email?: string;
    username?: string;
    first_name?: string | null;
    last_name?: string | null;
    display_name?: string | null;
    full_name?: string | null;
    avatar_url?: string | null;
  };
}

interface ConversationSidebarProps {
  conversations: Conversation[];
  selectedId: string | null;
  onSelectConversation: (id: string) => void;
  orgMembers?: OrgMemberItem[];
  onStartNewConversation?: (targetUserId: string) => void;
  onOpenCreateGroupModal?: () => void;
}

export const ConversationSidebar: React.FC<ConversationSidebarProps> = ({
  conversations,
  selectedId,
  onSelectConversation,
  orgMembers = [],
  onStartNewConversation,
  onOpenCreateGroupModal
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState<'all' | 'direct' | 'groups' | 'channels'>('all');
  const [showMemberModal, setShowMemberModal] = useState(false);

  const filteredConversations = (conversations || []).filter(c => {
    if (!c) return false;
    const name = c.type === 'private' ? (c.participant?.full_name || 'Direct Message') : (c.name || 'Group');
    const matchesSearch = name.toLowerCase().includes(searchQuery.toLowerCase());
    if (!matchesSearch) return false;

    if (activeTab === 'direct') return c.type === 'private';
    if (activeTab === 'groups') return c.type === 'group';
    if (activeTab === 'channels') return c.type === 'project_channel' || c.type === 'announcement';
    return true;
  });

  const pinnedConversations = filteredConversations.filter(c => c.is_pinned);
  const unpinnedConversations = filteredConversations.filter(c => !c.is_pinned);

  const renderConvItem = (conv: Conversation) => {
    const isSelected = conv.id === selectedId;
    const is1on1 = conv.type === 'private';
    const isGroup = conv.type === 'group';

    return (
      <button
        key={conv.id}
        onClick={() => onSelectConversation(conv.id)}
        className={`w-full flex items-center space-x-3 p-2.5 rounded-xl transition-all text-left ${
          isSelected
            ? 'bg-accentSubtle border border-accent/30 text-textPrimary'
            : 'hover:bg-bgHover text-textSecondary'
        }`}
      >
        {/* Avatar with Status */}
        <div className="relative shrink-0">
          {is1on1 ? (
            <div className="w-10 h-10 rounded-full bg-bgTertiary text-textPrimary font-semibold text-sm flex items-center justify-center border border-borderMuted">
              {conv.participant?.full_name?.charAt(0).toUpperCase() || 'U'}
            </div>
          ) : isGroup ? (
            <div className="w-10 h-10 rounded-xl bg-accentSubtle text-accentText font-semibold text-sm flex items-center justify-center border border-accent/30">
              <Users className="w-5 h-5" />
            </div>
          ) : (
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 text-purple-500 font-semibold text-sm flex items-center justify-center border border-purple-500/20">
              <Hash className="w-5 h-5" />
            </div>
          )}

          {is1on1 && conv.participant?.status && (
            <div className="absolute bottom-0 right-0">
              <OnlineBadge status={conv.participant.status} size="sm" />
            </div>
          )}
        </div>

        {/* Name & Last Message */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-0.5">
            <span className="font-medium text-xs truncate text-textPrimary">
              {is1on1 ? (conv.participant?.full_name || 'Direct Message') : conv.name}
            </span>
            {conv.last_message_at && (
              <span className="text-[10px] text-textMuted shrink-0">
                {new Date(
                  typeof conv.last_message_at === 'string' && !conv.last_message_at.endsWith('Z') && !/[+-]\d{2}:?\d{2}$/.test(conv.last_message_at)
                    ? `${conv.last_message_at}Z`
                    : conv.last_message_at
                ).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            )}
          </div>
          <p className="text-[11px] text-textMuted truncate">
            {conv.last_message ? conv.last_message.content : 'No messages yet'}
          </p>
        </div>

        {/* Badges */}
        <div className="flex items-center space-x-1">
          {conv.is_pinned && <Pin className="w-3 h-3 text-amber-400 fill-amber-400" />}
          {conv.unread_count > 0 && (
            <span className="bg-accent text-white text-[10px] font-bold px-2 py-0.5 rounded-full">
              {conv.unread_count}
            </span>
          )}
        </div>
      </button>
    );
  };

  return (
    <div className="w-full md:w-80 shrink-0 bg-bgSidebar border-r border-borderColor flex flex-col h-full select-none">
      {/* Sidebar Header */}
      <div className="p-4 border-b border-borderMuted flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <MessageSquare className="w-5 h-5 text-accentText" />
          <h2 className="font-semibold text-textPrimary text-base">Conversations</h2>
        </div>
        <div className="flex items-center space-x-1">
          <button
            onClick={() => setShowMemberModal(true)}
            className="p-1.5 bg-bgTertiary hover:bg-bgHover text-textSecondary rounded-lg transition-colors border border-borderMuted"
            title="New Direct Message"
          >
            <UserPlus className="w-4 h-4" />
          </button>
          {onOpenCreateGroupModal && (
            <button
              onClick={onOpenCreateGroupModal}
              className="p-1.5 bg-accentSubtle hover:bg-accent/20 text-accentText rounded-lg transition-colors border border-accent/30"
              title="Create Group or Channel"
            >
              <Plus className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Category Tabs */}
      <div className="px-3 pt-3 flex items-center space-x-1 border-b border-borderMuted overflow-x-auto no-scrollbar">
        {(['all', 'direct', 'groups', 'channels'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-3 py-1.5 text-xs font-medium rounded-t-lg transition-colors whitespace-nowrap capitalize ${
              activeTab === tab
                ? 'bg-bgPrimary text-accentText border-t-2 border-accent font-semibold'
                : 'text-textMuted hover:text-textPrimary'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Search Input */}
      <div className="p-3">
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-textMuted" />
          <input
            type="text"
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-bgTertiary border border-borderMuted rounded-xl pl-9 pr-3 py-1.5 text-xs text-textPrimary placeholder:text-textMuted focus:outline-none focus:border-accent"
          />
        </div>
      </div>

      {/* Conversation Stream List */}
      <div className="flex-1 overflow-y-auto px-3 pb-3 space-y-1">
        {filteredConversations.length === 0 ? (
          <div className="py-8 text-center text-textMuted text-xs">
            No conversations match filter.
          </div>
        ) : (
          <>
            {pinnedConversations.length > 0 && (
              <div className="mb-2">
                <div className="px-2.5 py-1 text-[10px] font-semibold text-textMuted uppercase tracking-wider flex items-center space-x-1">
                  <Pin className="w-3 h-3 text-amber-400" />
                  <span>Pinned</span>
                </div>
                {pinnedConversations.map(renderConvItem)}
              </div>
            )}

            {unpinnedConversations.length > 0 && (
              <div>
                {pinnedConversations.length > 0 && (
                  <div className="px-2.5 py-1 text-[10px] font-semibold text-textMuted uppercase tracking-wider">
                    All Conversations
                  </div>
                )}
                {unpinnedConversations.map(renderConvItem)}
              </div>
            )}
          </>
        )}
      </div>

      {/* Direct Message New Chat Selection Modal */}
      {showMemberModal && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-bgDialog border border-borderColor rounded-2xl w-full max-w-md overflow-hidden shadow-2xl">
            <div className="p-4 border-b border-borderMuted flex items-center justify-between">
              <h3 className="font-semibold text-textPrimary text-sm">Start Direct Message</h3>
              <button
                onClick={() => setShowMemberModal(false)}
                className="text-textMuted hover:text-textPrimary text-xs font-semibold"
              >
                ✕
              </button>
            </div>
            <div className="p-3 max-h-80 overflow-y-auto space-y-1">
              {orgMembers.length === 0 ? (
                <div className="p-4 text-center text-textMuted text-xs">
                  No other organization members available.
                </div>
              ) : (
                orgMembers.map((member) => {
                  const mUser = member.user;
                  const uId = member.user_id || mUser?.id || member.id;

                  // Priority: 1. display_name, 2. full_name, 3. username, 4. email, 5. "User"
                  const displayName =
                    member.display_name?.trim() ||
                    mUser?.display_name?.trim() ||
                    member.full_name?.trim() ||
                    mUser?.full_name?.trim() ||
                    (member.first_name || mUser?.first_name
                      ? `${member.first_name || mUser?.first_name || ''} ${member.last_name || mUser?.last_name || ''}`.trim()
                      : '') ||
                    member.username?.trim() ||
                    mUser?.username?.trim() ||
                    member.email?.trim() ||
                    mUser?.email?.trim() ||
                    'User';

                  const email = member.email || mUser?.email || '';
                  const initial = displayName.charAt(0).toUpperCase() || 'U';

                  return (
                    <button
                      key={uId}
                      onClick={() => {
                        if (uId && onStartNewConversation) {
                          onStartNewConversation(uId);
                          setShowMemberModal(false);
                        }
                      }}
                      className="w-full flex items-center space-x-3 p-2.5 hover:bg-bgHover rounded-xl text-left transition-colors"
                    >
                      <div className="w-8 h-8 rounded-full bg-accentSubtle border border-accent/30 text-accentText font-semibold text-xs flex items-center justify-center">
                        {initial}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-xs font-medium text-textPrimary truncate">{displayName}</p>
                        {email && <p className="text-[10px] text-textMuted truncate">{email}</p>}
                      </div>
                    </button>
                  );
                })
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
