import React from 'react';
import { Filter, SlidersHorizontal, RotateCcw, SortAsc, Calendar, FileType, Tag } from 'lucide-react';
import { SearchFilters } from './types';

interface SearchFilterPanelProps {
  filters: SearchFilters;
  onFilterChange: (updated: Partial<SearchFilters>) => void;
  facets?: Record<string, number>;
}

export function SearchFilterPanel({ filters, onFilterChange, facets = {} }: SearchFilterPanelProps) {
  const entityTypes = [
    { id: 'all', label: 'All Items' },
    { id: 'document', label: 'Documents' },
    { id: 'project', label: 'Projects' },
    { id: 'task', label: 'Tasks' },
    { id: 'chat', label: 'AI Chat' },
    { id: 'knowledge', label: 'Knowledge' },
    { id: 'user', label: 'Users' },
    { id: 'workflow', label: 'Workflows' },
    { id: 'workspace', label: 'Workspaces' },
  ];

  const handleReset = () => {
    onFilterChange({
      type: 'all',
      sort: 'most_relevant',
      status: undefined,
      file_type: undefined,
      tags: undefined,
      date_from: undefined,
      date_to: undefined,
      page: 1,
    });
  };

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-bgCard border border-borderColor rounded-xl text-xs text-textPrimary">
      {/* Category Type Pills */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 max-w-full scrollbar-none">
        {entityTypes.map((et) => {
          const isActive = (filters.type || 'all') === et.id;
          const count = facets[et.id] !== undefined ? facets[et.id] : null;
          return (
            <button
              key={et.id}
              onClick={() => onFilterChange({ type: et.id, page: 1 })}
              className={`px-3 py-1.5 rounded-lg font-medium transition-all whitespace-nowrap flex items-center gap-1.5 border ${
                isActive
                  ? 'bg-accentSubtle text-accentText border-accent/40 shadow-sm'
                  : 'bg-bgTertiary text-textMuted border-borderMuted hover:text-textPrimary hover:border-borderHover'
              }`}
            >
              {et.label}
              {count !== null && count > 0 && (
                <span
                  className={`px-1.5 py-0.2 rounded-full text-[10px] ${
                    isActive ? 'bg-accent/20 text-accentText' : 'bg-bgHover text-textMuted'
                  }`}
                >
                  {count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Dropdown Filters & Sorting */}
      <div className="flex flex-wrap items-center gap-2">
        {/* Sort Select */}
        <div className="flex items-center gap-1 bg-bgInput border border-borderColor rounded-lg px-2 py-1">
          <SortAsc className="w-3.5 h-3.5 text-textMuted" />
          <select
            value={filters.sort || 'most_relevant'}
            onChange={(e) => onFilterChange({ sort: e.target.value as any, page: 1 })}
            className="bg-transparent text-xs text-textPrimary focus:outline-none cursor-pointer"
          >
            <option value="most_relevant" className="bg-bgDialog text-textPrimary">
              Most Relevant
            </option>
            <option value="newest" className="bg-bgDialog text-textPrimary">
              Newest First
            </option>
            <option value="oldest" className="bg-bgDialog text-textPrimary">
              Oldest First
            </option>
            <option value="alphabetical" className="bg-bgDialog text-textPrimary">
              Alphabetical (A-Z)
            </option>
          </select>
        </div>

        {/* File Type Filter */}
        <div className="flex items-center gap-1 bg-bgInput border border-borderColor rounded-lg px-2 py-1">
          <FileType className="w-3.5 h-3.5 text-textMuted" />
          <select
            value={filters.file_type || ''}
            onChange={(e) => onFilterChange({ file_type: e.target.value || undefined, page: 1 })}
            className="bg-transparent text-xs text-textPrimary focus:outline-none cursor-pointer"
          >
            <option value="" className="bg-bgDialog text-textPrimary">
              All File Types
            </option>
            <option value="pdf" className="bg-bgDialog text-textPrimary">
              PDF Document
            </option>
            <option value="docx" className="bg-bgDialog text-textPrimary">
              Word (DOCX)
            </option>
            <option value="md" className="bg-bgDialog text-textPrimary">
              Markdown (.md)
            </option>
            <option value="png" className="bg-bgDialog text-textPrimary">
              Image File
            </option>
            <option value="json" className="bg-bgDialog text-textPrimary">
              JSON File
            </option>
          </select>
        </div>

        {/* Reset Filters */}
        <button
          onClick={handleReset}
          className="p-1.5 rounded-lg bg-bgTertiary hover:bg-bgHover border border-borderMuted text-textMuted hover:text-textPrimary transition-colors flex items-center gap-1"
          title="Reset all search filters"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span className="text-[11px] hidden sm:inline">Reset</span>
        </button>
      </div>
    </div>
  );
}
