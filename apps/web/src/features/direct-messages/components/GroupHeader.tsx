import React from 'react';
import { Conversation } from '../types';
import { OnlineBadge } from './OnlineBadge';
import { Users, Hash, Pin, ShieldCheck, UserPlus, Info } from 'lucide-react';

import { formatLastSeen } from '../utils/time';

interface GroupHeaderProps {
  conversation: Conversation;
  onTogglePin?: () => void;
  onToggleDrawer?: () => void;
  isPinned?: boolean;
}

export const GroupHeader: React.FC<GroupHeaderProps> = ({
  conversation,
  onTogglePin,
  onToggleDrawer,
  isPinned = false
}) => {
  const is1on1 = conversation.type === 'private';
  const isGroup = conversation.type === 'group';
  const isChannel = conversation.type === 'project_channel' || conversation.type === 'announcement';

  return (
    <div className="h-16 px-6 border-b border-borderMuted flex items-center justify-between bg-bgHeader backdrop-blur select-none">
      <div className="flex items-center space-x-3 min-w-0">
        {/* Avatar / Icon */}
        <div className="relative shrink-0">
          {is1on1 ? (
            <div className="w-10 h-10 rounded-full bg-bgTertiary border border-borderMuted text-accentText font-semibold text-sm flex items-center justify-center">
              {conversation.participant?.full_name?.charAt(0).toUpperCase() || 'U'}
            </div>
          ) : isGroup ? (
            <div className="w-10 h-10 rounded-xl bg-accentSubtle border border-accent/30 text-accentText font-semibold text-sm flex items-center justify-center">
              <Users className="w-5 h-5" />
            </div>
          ) : (
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-500 font-semibold text-sm flex items-center justify-center">
              <Hash className="w-5 h-5" />
            </div>
          )}

          {is1on1 && conversation.participant?.status && (
            <div className="absolute bottom-0 right-0">
              <OnlineBadge status={conversation.participant.status} size="sm" />
            </div>
          )}
        </div>

        {/* Title & Info */}
        <div className="min-w-0">
          <div className="flex items-center space-x-2">
            <h2 className="font-semibold text-textPrimary text-sm truncate">
              {is1on1 ? (conversation.participant?.full_name || 'Direct Message') : conversation.name}
            </h2>
            <span title="E2E Authenticated & Isolated">
              <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            </span>
            {conversation.is_archived && (
              <span className="bg-amber-500/20 text-amber-500 text-[10px] font-bold px-1.5 py-0.5 rounded border border-amber-500/30">
                ARCHIVED
              </span>
            )}
          </div>

          <p className="text-xs text-textMuted truncate flex items-center space-x-1">
            {is1on1 ? (
              conversation.participant?.status === 'online' ? (
                <span className="text-emerald-400 font-medium flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                  Online
                </span>
              ) : (
                <span className="text-textMuted">{formatLastSeen(conversation.participant?.last_seen)}</span>
              )
            ) : (
              <span>{conversation.description || `${conversation.member_count || 1} members`}</span>
            )}
          </p>
        </div>
      </div>

      {/* Header Actions */}
      <div className="flex items-center space-x-2 shrink-0">
        {onTogglePin && (
          <button
            onClick={onTogglePin}
            className={`p-2 rounded-xl border transition-all ${
              isPinned
                ? 'bg-amber-500/20 border-amber-500/40 text-amber-500 shadow-sm shadow-amber-900/30'
                : 'bg-bgTertiary border-borderMuted text-textMuted hover:bg-bgHover hover:text-textPrimary'
            }`}
            title={isPinned ? 'Unpin Conversation' : 'Pin Conversation'}
          >
            <Pin className="w-4 h-4" />
          </button>
        )}

        {!is1on1 && onToggleDrawer && (
          <button
            onClick={onToggleDrawer}
            className="p-2 bg-bgTertiary hover:bg-bgHover border border-borderMuted text-textSecondary hover:text-textPrimary rounded-xl transition-all flex items-center space-x-1.5 text-xs"
            title="View Group Details & Members"
          >
            <Users className="w-4 h-4 text-accentText" />
            <span className="hidden sm:inline">Details</span>
          </button>
        )}
      </div>
    </div>
  );
};
