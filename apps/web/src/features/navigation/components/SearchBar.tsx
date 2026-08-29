import React from 'react';
import { Search } from 'lucide-react';

interface SearchBarProps {
  placeholder?: string;
  onChange: (val: string) => void;
}

export function SearchBar({
  placeholder = "Search anything... (Ctrl + /)",
  onChange
}: SearchBarProps) {
  return (
    <div className="relative w-full md:w-64">
      <Search className="absolute left-3 top-2.5 h-4 w-4 text-textMuted" />
      <input
        type="text"
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        className="w-full pl-9 pr-4 py-2 bg-bgInput border border-borderColor hover:border-borderHover rounded-xl text-xs text-textPrimary placeholder-textMuted focus:outline-none focus:border-accent transition-all"
      />
    </div>
  );
}
export default SearchBar;
