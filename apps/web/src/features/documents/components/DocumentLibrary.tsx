import React, { useState, useMemo } from 'react';
import { Document } from '../types';
import DocumentGrid from './DocumentGrid';
import DocumentTable from './DocumentTable';
import EmptyState from './EmptyState';
import { Search, LayoutGrid, List, ArrowUpDown, Filter, Loader2 } from 'lucide-react';

interface DocumentLibraryProps {
  documents: Document[];
  selectedIds: string[];
  loading?: boolean;
  onToggleSelect: (id: string) => void;
  onSelectDoc: (id: string) => void;
  onUploadTrigger: () => void;
  onRename?: (doc: Document) => void;
  onDelete?: (doc: Document) => void;
  onRestore?: (doc: Document) => void;
  onDownload?: (doc: Document) => void;
  isTrashView?: boolean;
}

export type FilterCategory = 'all' | 'documents' | 'images' | 'code' | 'archives' | 'pdf' | 'word' | 'excel' | 'powerpoint' | 'text' | 'other';
export type SortOption = 'newest' | 'oldest' | 'name_asc' | 'name_desc' | 'largest' | 'smallest' | 'modified';

export const DocumentLibrary: React.FC<DocumentLibraryProps> = ({
  documents,
  selectedIds,
  loading = false,
  onToggleSelect,
  onSelectDoc,
  onUploadTrigger,
  onRename,
  onDelete,
  onRestore,
  onDownload,
  isTrashView = false
}) => {
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState<FilterCategory>('all');
  const [sortBy, setSortBy] = useState<SortOption>('newest');

  // Filter & Search Logic
  const filteredDocs = useMemo(() => {
    return documents.filter((doc) => {
      const title = (doc.title || '').toLowerCase();
      const filename = (doc.filename || '').toLowerCase();
      const ext = (doc.extension || filename.split('.').pop() || '').toLowerCase();
      const author = (doc.uploaded_by || '').toLowerCase();
      const q = search.trim().toLowerCase();

      // Search match: title, filename, extension, or author
      const matchesSearch = !q || title.includes(q) || filename.includes(q) || ext.includes(q) || author.includes(q);
      if (!matchesSearch) return false;

      // Category filter
      if (category === 'all') return true;
      if (category === 'pdf') return ext === 'pdf';
      if (category === 'word') return ['doc', 'docx'].includes(ext);
      if (category === 'excel') return ['xls', 'xlsx', 'csv'].includes(ext);
      if (category === 'powerpoint') return ['ppt', 'pptx'].includes(ext);
      if (category === 'text') return ['txt', 'md'].includes(ext);
      if (category === 'documents') return ['pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'txt', 'md'].includes(ext);
      if (category === 'images') return ['png', 'jpg', 'jpeg', 'webp', 'gif', 'svg'].includes(ext);
      if (category === 'code') return ['js', 'ts', 'java', 'cpp', 'html', 'css', 'json', 'csv', 'py', 'xml'].includes(ext);
      if (category === 'archives') return ['zip', 'tar', 'gz', 'rar', '7z'].includes(ext);
      if (category === 'other') return !['pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'txt', 'md', 'png', 'jpg', 'jpeg', 'webp', 'gif', 'svg', 'js', 'ts', 'java', 'cpp', 'html', 'css', 'json', 'csv', 'zip'].includes(ext);

      return true;
    });
  }, [documents, search, category]);

  // Sorting Logic
  const sortedDocs = useMemo(() => {
    const list = [...filteredDocs];
    return list.sort((a, b) => {
      const aName = (a.title || a.filename || '').toLowerCase();
      const bName = (b.title || b.filename || '').toLowerCase();
      const aDate = new Date(a.created_at || 0).getTime();
      const bDate = new Date(b.created_at || 0).getTime();
      const aMod = new Date(a.updated_at || a.created_at || 0).getTime();
      const bMod = new Date(b.updated_at || b.created_at || 0).getTime();
      const aSize = a.size || a.size_bytes || 0;
      const bSize = b.size || b.size_bytes || 0;

      switch (sortBy) {
        case 'newest': return bDate - aDate;
        case 'oldest': return aDate - bDate;
        case 'name_asc': return aName.localeCompare(bName);
        case 'name_desc': return bName.localeCompare(aName);
        case 'largest': return bSize - aSize;
        case 'smallest': return aSize - bSize;
        case 'modified': return bMod - aMod;
        default: return bDate - aDate;
      }
    });
  }, [filteredDocs, sortBy]);

  return (
    <div className="flex-1 flex flex-col space-y-3.5 font-outfit">
      {/* Control Bar */}
      <div className="flex flex-col md:flex-row justify-between items-stretch md:items-center gap-3 bg-bgCard border border-borderColor p-3 rounded-2xl backdrop-blur-xl">
        {/* Search */}
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-2.5 w-4 h-4 text-textMuted" />
          <input
            id="doc-lib-search-input"
            type="text"
            placeholder="Search filename, extension, uploaded by..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-bgInput border border-borderColor rounded-xl pl-9 pr-3 py-1.5 text-xs text-textPrimary placeholder-textMuted focus:outline-none focus:border-accent transition"
          />
        </div>

        {/* Filters & Actions */}
        <div className="flex flex-wrap items-center gap-2 justify-between md:justify-end">
          {/* Category Filter Dropdown */}
          <div className="flex items-center gap-1.5 bg-bgInput border border-borderColor px-2.5 py-1 rounded-xl text-xs">
            <Filter size={13} className="text-textMuted" />
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value as FilterCategory)}
              className="bg-transparent text-xs text-textPrimary outline-none cursor-pointer font-medium"
            >
              <option value="all">All Categories</option>
              <option value="documents">Documents</option>
              <option value="images">Images</option>
              <option value="code">Code</option>
              <option value="archives">Archives</option>
              <option value="pdf">PDF</option>
              <option value="word">Word (DOC/X)</option>
              <option value="excel">Excel / CSV</option>
              <option value="powerpoint">PowerPoint</option>
              <option value="text">Text / Markdown</option>
              <option value="other">Other</option>
            </select>
          </div>

          {/* Sort Dropdown */}
          <div className="flex items-center gap-1.5 bg-bgInput border border-borderColor px-2.5 py-1 rounded-xl text-xs">
            <ArrowUpDown size={13} className="text-textMuted" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortOption)}
              className="bg-transparent text-xs text-textPrimary outline-none cursor-pointer font-medium"
            >
              <option value="newest">Sort: Newest First</option>
              <option value="oldest">Sort: Oldest First</option>
              <option value="name_asc">Sort: Name (A-Z)</option>
              <option value="name_desc">Sort: Name (Z-A)</option>
              <option value="largest">Sort: Largest Size</option>
              <option value="smallest">Sort: Smallest Size</option>
              <option value="modified">Sort: Recently Modified</option>
            </select>
          </div>

          {/* View Mode Toggle */}
          <div className="flex bg-bgTertiary border border-borderMuted p-0.5 rounded-xl">
            <button
              type="button"
              onClick={() => setViewMode('grid')}
              className={`p-1.5 rounded-lg transition ${
                viewMode === 'grid' ? 'bg-accent text-white' : 'text-textMuted hover:text-textPrimary'
              }`}
              title="Grid View"
            >
              <LayoutGrid size={15} />
            </button>
            <button
              type="button"
              onClick={() => setViewMode('table')}
              className={`p-1.5 rounded-lg transition ${
                viewMode === 'table' ? 'bg-accent text-white' : 'text-textMuted hover:text-textPrimary'
              }`}
              title="Table View"
            >
              <List size={15} />
            </button>
          </div>
        </div>
      </div>

      {/* Skeleton Loading State */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3.5">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-44 rounded-2xl bg-bgCard border border-borderColor p-4 animate-pulse space-y-3 flex flex-col items-center justify-center">
              <div className="w-12 h-12 rounded-xl bg-bgTertiary" />
              <div className="h-3 w-3/4 bg-bgTertiary rounded-full" />
              <div className="h-2 w-1/2 bg-bgTertiary rounded-full" />
            </div>
          ))}
        </div>
      ) : sortedDocs.length === 0 ? (
        <EmptyState
          title={isTrashView ? "Trash is Empty" : "No knowledge documents found"}
          description={
            search || category !== 'all'
              ? "No documents match your active search terms or category filters."
              : isTrashView
              ? "Deleted items will appear here before permanent deletion."
              : "Upload your first document to build your team's knowledge intelligence base."
          }
          onAction={isTrashView ? undefined : onUploadTrigger}
          actionLabel={isTrashView ? undefined : "Upload Document"}
        />
      ) : viewMode === 'grid' ? (
        <DocumentGrid
          documents={sortedDocs}
          selectedIds={selectedIds}
          onToggleSelect={onToggleSelect}
          onSelectDoc={onSelectDoc}
          onRename={onRename}
          onDelete={onDelete}
          onRestore={onRestore}
          onDownload={onDownload}
          isTrashView={isTrashView}
        />
      ) : (
        <DocumentTable
          documents={sortedDocs}
          selectedIds={selectedIds}
          onToggleSelect={onToggleSelect}
          onSelectDoc={onSelectDoc}
          onRename={onRename}
          onDelete={onDelete}
          onRestore={onRestore}
          onDownload={onDownload}
          isTrashView={isTrashView}
        />
      )}
    </div>
  );
};
export default DocumentLibrary;
