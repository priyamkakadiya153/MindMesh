import React from 'react';
import { Plus } from 'lucide-react';

export interface ReactionItem {
  emoji: string;
  count: number;
  user_ids: string[];
  reacted_by_me?: boolean;
}

interface ReactionsBarProps {
  reactions?: ReactionItem[];
  currentUserId: string;
  onToggleReaction: (emoji: string) => void;
  onOpenPicker?: () => void;
}

export const ReactionsBar: React.FC<ReactionsBarProps> = ({
  reactions = [],
  currentUserId,
  onToggleReaction,
  onOpenPicker
}) => {
  if (!reactions || reactions.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-1 mt-1.5 select-none">
      {reactions.map(r => {
        const hasReacted = r.reacted_by_me || r.user_ids?.includes(currentUserId);
        return (
          <button
            key={r.emoji}
            onClick={() => onToggleReaction(r.emoji)}
            className={`flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs border transition-all ${
              hasReacted
                ? 'bg-accentSubtle border-accent/50 text-accentText shadow-sm font-semibold'
                : 'bg-bgTertiary border-borderMuted text-textSecondary hover:bg-bgHover'
            }`}
          >
            <span>{r.emoji}</span>
            <span className="text-[10px] text-textMuted">{r.count}</span>
          </button>
        );
      })}

      {onOpenPicker && (
        <button
          onClick={onOpenPicker}
          className="p-1 rounded-full bg-bgTertiary border border-borderMuted text-textMuted hover:text-textPrimary text-xs transition-colors"
          title="Add Reaction"
        >
          <Plus className="w-3 h-3" />
        </button>
      )}
    </div>
  );
};
