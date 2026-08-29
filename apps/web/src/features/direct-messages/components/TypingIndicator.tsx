import React from 'react';

interface TypingIndicatorProps {
  userName?: string;
}

export const TypingIndicator: React.FC<TypingIndicatorProps> = ({ userName = 'Someone' }) => {
  return (
    <div className="flex items-center space-x-2 text-xs text-textMuted italic px-4 py-1.5 bg-bgTertiary backdrop-blur border-t border-borderMuted animate-pulse">
      <div className="flex space-x-1 items-center">
        <span className="w-1.5 h-1.5 bg-accent rounded-full animate-bounce [animation-delay:-0.3s]"></span>
        <span className="w-1.5 h-1.5 bg-accent rounded-full animate-bounce [animation-delay:-0.15s]"></span>
        <span className="w-1.5 h-1.5 bg-accent rounded-full animate-bounce"></span>
      </div>
      <span>{userName} is typing...</span>
    </div>
  );
};
