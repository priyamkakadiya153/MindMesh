import React from 'react';
import { Search, X } from 'lucide-react';

export interface FAQSearchBarProps {
  query: string;
  onQueryChange: (q: string) => void;
}

export const FAQSearchBar: React.FC<FAQSearchBarProps> = ({
  query,
  onQueryChange,
}) => {
  return (
    <div className="relative w-full max-w-2xl mx-auto">
      <div className="relative flex items-center w-full rounded-ds-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 focus-within:border-indigo-500/50 shadow-ds-medium transition-all overflow-hidden">
        <div className="pl-4 text-indigo-600 dark:text-indigo-400">
          <Search className="w-5 h-5" />
        </div>
        <input
          type="text"
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          placeholder="Search questions (e.g. 'pricing', 'security', 'RAG', 'workspaces', 'SSO')..."
          className="w-full py-3.5 pl-3 pr-10 bg-transparent text-xs sm:text-sm font-medium text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none"
        />
        {query && (
          <button
            type="button"
            onClick={() => onQueryChange('')}
            className="pr-4 text-slate-400 hover:text-slate-600 dark:hover:text-white"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>

  );
};
