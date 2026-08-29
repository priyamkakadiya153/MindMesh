import React from 'react';
import { Smile } from 'lucide-react';

interface EmojiPickerProps {
  onSelectEmoji: (emoji: string) => void;
  onClose?: () => void;
}

const POPULAR_EMOJIS = ['👍', '❤️', '🔥', '😂', '🎉', '🚀', '💡', '👀', '🙌', '💯', '👏', '✅'];

export const EmojiPicker: React.FC<EmojiPickerProps> = ({ onSelectEmoji, onClose }) => {
  return (
    <div className="bg-bgDialog border border-borderColor rounded-2xl p-3 shadow-2xl z-50 select-none space-y-2">
      <div className="flex items-center justify-between text-[11px] font-semibold text-textMuted border-b border-borderMuted pb-1.5 px-1">
        <span className="flex items-center space-x-1">
          <Smile className="w-3.5 h-3.5 text-amber-500" />
          <span>Quick Reactions</span>
        </span>
      </div>
      <div className="grid grid-cols-6 gap-1">
        {POPULAR_EMOJIS.map(emoji => (
          <button
            key={emoji}
            onClick={() => {
              onSelectEmoji(emoji);
              if (onClose) onClose();
            }}
            className="w-8 h-8 rounded-lg hover:bg-bgHover text-lg flex items-center justify-center transition-transform hover:scale-125"
          >
            {emoji}
          </button>
        ))}
      </div>
    </div>
  );
};
