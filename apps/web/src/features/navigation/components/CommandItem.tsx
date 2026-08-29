import React from 'react';
import { Sparkles } from 'lucide-react';

interface CommandItemProps {
  label: string;
  category: string;
  onClick: () => void;
  shortcut?: string;
}

export const CommandItem = React.memo(function CommandItem({
  label,
  category,
  onClick,
  shortcut
}: CommandItemProps) {
  return (
    <button
      type="button"
      role="option"
      onClick={onClick}
      aria-label={label}
      className="w-full flex items-center justify-between p-2.5 hover:bg-accentSubtle border border-transparent hover:border-accent/20 rounded-xl text-left text-xs transition-all group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
    >
      <div className="flex items-center gap-2.5">
        <Sparkles size={12} className="text-accentText group-hover:scale-110 transition-transform" aria-hidden="true" />
        <div>
          <p className="font-semibold text-textPrimary group-hover:text-accentText transition-colors">{label}</p>
          <span className="text-[9px] text-textMuted font-semibold uppercase tracking-wider">{category}</span>
        </div>
      </div>

      {shortcut && (
        <span className="text-[9px] text-textMuted font-semibold px-2 py-0.5 bg-bgTertiary border border-borderMuted rounded-lg" aria-hidden="true">
          {shortcut}
        </span>
      )}
    </button>
  );
});
export default CommandItem;
