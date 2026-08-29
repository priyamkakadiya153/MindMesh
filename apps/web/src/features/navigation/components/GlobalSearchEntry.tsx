import React from 'react';
import { Search } from 'lucide-react';
import { useNavigationStore } from '../store';

export function GlobalSearchEntry() {
  const { setActiveTab } = useNavigationStore();

  const handleOpen = () => {
    window.dispatchEvent(new CustomEvent('open-universal-search'));
  };

  return (
    <button
      type="button"
      onClick={handleOpen}
      aria-label="Open search dialog (Command K)"
      title="Open search dialog (Command K)"
      className="relative w-full min-w-0 min-h-[44px] sm:min-h-[38px] flex items-center justify-between pl-9 pr-3 py-2 bg-bgInput hover:bg-bgHover border border-borderColor hover:border-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent rounded-xl text-xs text-textSecondary hover:text-textPrimary transition-all duration-150 text-left group active:scale-[0.99]"
    >
      <Search className="absolute left-3 top-3 sm:top-2.5 h-4 w-4 text-textMuted group-hover:text-accentText transition-colors shrink-0" aria-hidden="true" />
      <span className="truncate font-medium min-w-0 pr-2">Search conversations, files, decisions...</span>
      <kbd className="hidden lg:inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] text-textMuted bg-bgTertiary border border-borderMuted rounded font-mono shrink-0" aria-hidden="true">
        ⌘K
      </kbd>
    </button>
  );
}
export default GlobalSearchEntry;
