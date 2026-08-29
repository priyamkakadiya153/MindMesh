'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../features/auth/auth-provider';
import { useWorkspaceStore } from '../../features/workspace/store';
import {
  AttachmentItem,
  listFiles,
  renameFile,
  softDeleteFile,
  promoteFileToDocument,
  PaginatedFilesResponse
} from '../../features/files/files-api';
import { FileUploadModal } from '../../features/files/components/FileUploadModal';
import { FilePreviewModal } from '../../features/files/components/FilePreviewModal';
import { MoveFolderModal } from '../../features/files/components/MoveFolderModal';
import { VersionHistoryModal } from '../../features/files/components/VersionHistoryModal';
import { AuditLogModal } from '../../features/files/components/AuditLogModal';
import { StorageStatsModal } from '../../features/files/components/StorageStatsModal';
import { EmptyState } from '../../shared/components/EmptyState';
import {
  Share2,
  Search,
  Grid,
  List as ListIcon,
  Image as ImageIcon,
  FileText,
  FileCode,
  Film,
  Archive,
  Download,
  Eye,
  Trash2,
  Edit2,
  Loader2,
  Upload,
  FolderPlus,
  Folder,
  GitBranch,
  ShieldCheck,
  ChevronRight,
  ChevronLeft,
  BarChart3,
  Users,
  MessageSquare,
  Sparkles,
  CheckCircle2,
  Layers,
  Clock,
  ArrowUpRight
} from 'lucide-react';

interface FolderItem {
  id: string;
  name: string;
  parent_id?: string | null;
}

export function SharedFilesPage() {
  const { token, currentOrg } = useAuth();
  const { currentWorkspace } = useWorkspaceStore();

  // File list & pagination state
  const [files, setFiles] = useState<AttachmentItem[]>([]);
  const [totalFiles, setTotalFiles] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pageSize] = useState<number>(25);
  const [isLoading, setIsLoading] = useState(true);

  // Folder & Breadcrumbs State
  const [folders, setFolders] = useState<FolderItem[]>([]);
  const [folderPath, setFolderPath] = useState<FolderItem[]>([]);
  const [currentFolderId, setCurrentFolderId] = useState<string | null>(null);

  // Sharing provenance filter state
  const [sharingFilter, setSharingFilter] = useState<string>('all'); // all, shared_with_me, shared_by_me, recent, conversations, projects

  // Filter & Search & Sort State
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('newest');
  const [dateFilter, setDateFilter] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  // Promoting state
  const [promotingId, setPromotingId] = useState<string | null>(null);
  const [promotionToast, setPromotionToast] = useState<{ message: string; docId?: string } | null>(null);

  // Modal States
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isStorageStatsOpen, setIsStorageStatsOpen] = useState(false);
  const [previewItem, setPreviewItem] = useState<AttachmentItem | null>(null);
  const [moveItem, setMoveItem] = useState<AttachmentItem | null>(null);
  const [versionItem, setVersionItem] = useState<AttachmentItem | null>(null);
  const [auditItem, setAuditItem] = useState<AttachmentItem | null>(null);

  const loadSharedFiles = useCallback(async () => {
    if (!currentOrg?.id) return;
    try {
      setIsLoading(true);
      const res: PaginatedFilesResponse = await listFiles(
        currentOrg.id,
        currentWorkspace?.id,
        currentFolderId || undefined,
        undefined,
        activeCategory,
        searchQuery.trim() || undefined,
        sortBy,
        dateFilter,
        currentPage,
        pageSize,
        sharingFilter,
        token || undefined
      );
      setFiles(res.items);
      setTotalFiles(res.total);
      setTotalPages(res.total_pages || 1);
    } catch (err) {
      console.error('Failed to load shared files:', err);
    } finally {
      setIsLoading(false);
    }
  }, [
    currentOrg?.id,
    currentWorkspace?.id,
    currentFolderId,
    activeCategory,
    sharingFilter,
    searchQuery,
    sortBy,
    dateFilter,
    currentPage,
    pageSize,
    token
  ]);

  const loadFolders = useCallback(async () => {
    if (!currentWorkspace?.id) return;
    try {
      const res = await fetch(`/api/v1/folders?workspace_id=${currentWorkspace.id}`, {
        headers: { Authorization: `Bearer ${token || localStorage.getItem('token') || ''}` }
      });
      if (res.ok) {
        const data = await res.json();
        setFolders(data);
      }
    } catch (err) {
      console.error('Failed to load folders:', err);
    }
  }, [currentWorkspace?.id, token]);

  useEffect(() => {
    loadSharedFiles();
  }, [loadSharedFiles]);

  useEffect(() => {
    loadFolders();
  }, [loadFolders]);

  const handleNavigateFolder = (folder: FolderItem | null) => {
    if (!folder) {
      setCurrentFolderId(null);
      setFolderPath([]);
    } else {
      setCurrentFolderId(folder.id);
      setFolderPath((prev) => {
        const idx = prev.findIndex((f) => f.id === folder.id);
        if (idx !== -1) return prev.slice(0, idx + 1);
        return [...prev, folder];
      });
    }
    setCurrentPage(1);
  };

  const handleUploadSuccess = (item: AttachmentItem) => {
    setFiles((prev) => [item, ...prev.filter((f) => f.id !== item.id)]);
    setTotalFiles((prev) => prev + 1);
  };

  const handleCreateFolder = async () => {
    const folderName = prompt('Enter new folder name:');
    if (folderName && folderName.trim() && currentWorkspace?.id) {
      try {
        const res = await fetch('/api/v1/folders', {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token || localStorage.getItem('token') || ''}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ name: folderName.trim(), workspace_id: currentWorkspace.id })
        });
        if (res.ok) {
          const newFolder = await res.json();
          setFolders((prev) => [newFolder, ...prev]);
        }
      } catch (err: any) {
        alert(err.message || 'Failed to create folder');
      }
    }
  };

  const handleRename = async (item: AttachmentItem) => {
    const newName = prompt('Enter new filename:', item.original_filename);
    if (newName && newName.trim() !== item.original_filename) {
      try {
        const updated = await renameFile(item.id, newName.trim(), token || undefined);
        setFiles((prev) => prev.map((f) => (f.id === item.id ? updated : f)));
      } catch (err: any) {
        alert(err.message || 'Failed to rename file');
      }
    }
  };

  const handleDelete = async (item: AttachmentItem) => {
    if (confirm(`Are you sure you want to delete "${item.original_filename}"?`)) {
      try {
        await softDeleteFile(item.id, token || undefined);
        setFiles((prev) => prev.filter((f) => f.id !== item.id));
        setTotalFiles((prev) => Math.max(0, prev - 1));
      } catch (err: any) {
        alert(err.message || 'Failed to delete file');
      }
    }
  };

  const handlePromoteToDocument = async (item: AttachmentItem) => {
    try {
      setPromotingId(item.id);
      const res = await promoteFileToDocument(
        item.id,
        { workspace_id: currentWorkspace?.id },
        token || undefined
      );
      setFiles((prev) =>
        prev.map((f) =>
          f.id === item.id
            ? { ...f, is_promoted_to_document: true, promoted_document_id: res.document_id }
            : f
        )
      );
      setPromotionToast({
        message: `"${item.original_filename}" added to Documents knowledge workspace.`,
        docId: res.document_id
      });
      setTimeout(() => setPromotionToast(null), 5000);
    } catch (err: any) {
      alert(err.message || 'Failed to promote file to Documents');
    } finally {
      setPromotingId(null);
    }
  };

  const getFileIcon = (mimeType: string, filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase() || '';
    if (mimeType.startsWith('image/')) return <ImageIcon className="w-5 h-5 text-emerald-400" />;
    if (mimeType.includes('pdf') || ext === 'pdf') return <FileText className="w-5 h-5 text-rose-400" />;
    if (
      mimeType.includes('json') ||
      mimeType.includes('javascript') ||
      mimeType.includes('typescript') ||
      mimeType.includes('python') ||
      ['py', 'js', 'ts', 'tsx', 'java', 'cpp', 'c', 'json', 'md', 'html', 'css'].includes(ext)
    ) {
      return <FileCode className="w-5 h-5 text-purple-400" />;
    }
    if (mimeType.startsWith('video/') || mimeType.startsWith('audio/')) return <Film className="w-5 h-5 text-blue-400" />;
    if (mimeType.includes('zip') || mimeType.includes('tar') || mimeType.includes('rar') || ext === '7z') {
      return <Archive className="w-5 h-5 text-amber-400" />;
    }
    return <FileText className="w-5 h-5 text-slate-400" />;
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-bgPrimary text-textPrimary overflow-hidden select-none">
      {/* Top Header */}
      <div className="p-3.5 sm:p-4 border-b border-borderMuted bg-bgHeader backdrop-blur flex items-center justify-between">
        <div>
          <h1 className="text-base font-bold text-textPrimary flex items-center space-x-2">
            <Share2 className="w-5 h-5 text-accentText" />
            <span>Shared Files</span>
          </h1>
          <p className="text-[11px] text-textMuted mt-0.5">
            Files shared with you and your teams across conversations, direct messages, and project discussions.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsStorageStatsOpen(true)}
            className="px-3 py-1.5 rounded-xl border border-borderColor hover:bg-bgHover text-textPrimary text-xs font-semibold flex items-center space-x-1.5 transition-all"
            title="Storage Usage Analytics"
          >
            <BarChart3 className="w-4 h-4 text-purple-400" />
            <span className="hidden md:inline">Storage Usage</span>
          </button>

          <button
            onClick={handleCreateFolder}
            className="px-3 py-1.5 rounded-xl border border-borderColor hover:bg-bgHover text-textPrimary text-xs font-semibold flex items-center space-x-1.5 transition-all"
          >
            <FolderPlus className="w-4 h-4 text-amber-400" />
            <span className="hidden sm:inline">New Folder</span>
          </button>

          <button
            onClick={() => setIsUploadOpen(true)}
            className="px-3.5 py-1.5 rounded-xl bg-accent hover:bg-accentHover text-white text-xs font-semibold flex items-center space-x-1.5 transition-all shadow-md"
          >
            <Upload className="w-4 h-4" />
            <span>Share File</span>
          </button>
        </div>
      </div>

      {/* Promotion Toast */}
      {promotionToast && (
        <div className="mx-4 mt-3 p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl flex items-center justify-between text-xs text-emerald-300">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{promotionToast.message}</span>
          </div>
          <a
            href="/documents"
            className="text-[11px] font-semibold text-emerald-400 underline hover:text-emerald-300 flex items-center space-x-1"
          >
            <span>View in Documents</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </a>
        </div>
      )}

      {/* Breadcrumb Navigation Trail */}
      <div className="px-4 py-2 border-b border-borderMuted bg-bgSecondary/60 flex items-center space-x-1.5 text-xs text-textMuted overflow-x-auto">
        <button
          onClick={() => handleNavigateFolder(null)}
          className={`hover:text-accentText flex items-center space-x-1 transition-colors ${
            currentFolderId === null ? 'font-semibold text-textPrimary' : ''
          }`}
        >
          <Share2 className="w-3.5 h-3.5" />
          <span>All Shared Files</span>
        </button>

        {folderPath.map((folder, idx) => (
          <React.Fragment key={folder.id}>
            <ChevronRight className="w-3.5 h-3.5 shrink-0 text-textMuted" />
            <button
              onClick={() => handleNavigateFolder(folder)}
              className={`hover:text-accentText transition-colors flex items-center space-x-1 ${
                idx === folderPath.length - 1 ? 'font-semibold text-textPrimary' : ''
              }`}
            >
              <Folder className="w-3.5 h-3.5 text-amber-400" />
              <span>{folder.name}</span>
            </button>
          </React.Fragment>
        ))}
      </div>

      {/* Collaboration Provenance Tabs (Who Shared What) */}
      <div className="px-3.5 py-2 border-b border-borderMuted bg-bgSecondary/40 flex items-center space-x-1.5 overflow-x-auto text-xs">
        {[
          { id: 'all', label: 'All Shared Files', icon: Share2 },
          { id: 'shared_with_me', label: 'Shared With Me', icon: Users },
          { id: 'shared_by_me', label: 'Shared By Me', icon: Upload },
          { id: 'recent', label: 'Recent Shares', icon: Clock },
          { id: 'conversations', label: 'From Conversations', icon: MessageSquare },
          { id: 'projects', label: 'From Projects', icon: Layers }
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = sharingFilter === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => {
                setSharingFilter(tab.id);
                setCurrentPage(1);
              }}
              className={`px-3 py-1.5 rounded-xl font-medium flex items-center space-x-1.5 transition-all shrink-0 ${
                isActive
                  ? 'bg-accent text-white shadow-sm font-semibold'
                  : 'text-textMuted hover:text-textPrimary hover:bg-bgHover'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Control Bar: Categories, Search, Filters, Sorting */}
      <div className="p-2.5 sm:p-3 border-b border-borderMuted bg-bgTertiary flex flex-col sm:flex-row items-center justify-between gap-3">
        {/* Category Tabs */}
        <div className="flex space-x-1 overflow-x-auto w-full sm:w-auto">
          {[
            { id: 'all', label: 'All Types' },
            { id: 'image', label: 'Images' },
            { id: 'document', label: 'Docs' },
            { id: 'code', label: 'Code' },
            { id: 'media', label: 'Media' },
            { id: 'archive', label: 'Archives' },
            { id: 'pdf', label: 'PDF' },
            { id: 'office', label: 'Office' },
            { id: 'text', label: 'Text' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => {
                setActiveCategory(tab.id);
                setCurrentPage(1);
              }}
              className={`px-2.5 py-1 rounded-xl text-[11px] font-medium transition-all shrink-0 ${
                activeCategory === tab.id
                  ? 'bg-accentSubtle border border-accent/40 text-accentText font-semibold'
                  : 'text-textMuted hover:text-textPrimary hover:bg-bgHover'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Search, Date Filter & Sorting Toggles */}
        <div className="flex items-center space-x-2 w-full sm:w-auto">
          {/* Date Filter */}
          <select
            value={dateFilter}
            onChange={(e) => {
              setDateFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="bg-bgInput text-textPrimary text-xs rounded-xl px-2.5 py-1.5 border border-borderColor focus:outline-none focus:border-accent"
          >
            <option value="all">All Time</option>
            <option value="today">Today</option>
            <option value="yesterday">Yesterday</option>
            <option value="last_7_days">Last 7 Days</option>
            <option value="this_month">This Month</option>
          </select>

          {/* Sorting */}
          <select
            value={sortBy}
            onChange={(e) => {
              setSortBy(e.target.value);
              setCurrentPage(1);
            }}
            className="bg-bgInput text-textPrimary text-xs rounded-xl px-2.5 py-1.5 border border-borderColor focus:outline-none focus:border-accent"
          >
            <option value="newest">Newest First</option>
            <option value="oldest">Oldest First</option>
            <option value="name_asc">Name (A–Z)</option>
            <option value="name_desc">Name (Z–A)</option>
            <option value="size_desc">Largest First</option>
            <option value="size_asc">Smallest First</option>
            <option value="recently_modified">Recently Modified</option>
          </select>

          {/* Search Input */}
          <div className="relative flex-1 sm:w-48">
            <Search className="w-3.5 h-3.5 text-textMuted absolute left-3 top-2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setCurrentPage(1);
              }}
              placeholder="Search shared files..."
              className="w-full bg-bgInput text-textPrimary placeholder-textMuted text-xs rounded-xl pl-8 pr-3 py-1.5 border border-borderColor focus:outline-none focus:border-accent"
            />
          </div>

          {/* View Toggles */}
          <div className="flex items-center bg-bgInput border border-borderColor rounded-xl p-0.5 shrink-0">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-1 rounded-lg transition-colors ${
                viewMode === 'grid' ? 'bg-bgCard text-accentText' : 'text-textMuted hover:text-textPrimary'
              }`}
              title="Grid View"
            >
              <Grid className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-1 rounded-lg transition-colors ${
                viewMode === 'list' ? 'bg-bgCard text-accentText' : 'text-textMuted hover:text-textPrimary'
              }`}
              title="List View"
            >
              <ListIcon className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Display Area */}
      <div className="flex-1 overflow-y-auto p-3.5">
        {isLoading ? (
          <div className="flex items-center justify-center h-full text-textMuted text-xs">
            <Loader2 className="w-6 h-6 animate-spin mr-2 text-accentText" />
            Loading shared files...
          </div>
        ) : files.length === 0 ? (
          <EmptyState
            title={
              sharingFilter === 'shared_with_me'
                ? 'No files shared with you yet'
                : sharingFilter === 'shared_by_me'
                ? 'You haven’t shared any files yet'
                : 'No shared files found'
            }
            description={
              sharingFilter === 'shared_with_me'
                ? 'When team members attach files in direct messages or discussions with you, they will appear here.'
                : 'Share files, designs, and code with team members in conversations and projects.'
            }
            icon={Share2}
            variant="card"
            primaryAction={{
              label: 'Share File',
              onClick: () => setIsUploadOpen(true),
              icon: Upload
            }}
            secondaryAction={{
              label: 'Create Folder',
              onClick: handleCreateFolder,
              icon: FolderPlus
            }}
          />
        ) : viewMode === 'grid' ? (
          /* Grid View */
          <div className="grid grid-cols-[repeat(auto-fill,minmax(min(100%,280px),1fr))] gap-4">
            {files.map((file) => (
              <div
                key={file.id}
                className="bg-bgCard border border-borderColor hover:border-borderHover rounded-2xl p-4 transition-all group flex flex-col justify-between shadow-sm hover:shadow-md"
              >
                <div>
                  {/* Thumbnail / Preview Box */}
                  {file.mime_type.startsWith('image/') ? (
                    <div
                      onClick={() => setPreviewItem(file)}
                      className="w-full aspect-video rounded-xl bg-bgTertiary overflow-hidden mb-3 cursor-pointer border border-borderMuted group-hover:opacity-90 transition-opacity"
                    >
                      <img src={file.preview_url} alt={file.original_filename} className="w-full h-full object-cover" />
                    </div>
                  ) : (
                    <div
                      onClick={() => setPreviewItem(file)}
                      className="w-full aspect-video rounded-xl bg-bgTertiary border border-borderMuted mb-3 flex items-center justify-center cursor-pointer group-hover:bg-bgHover transition-colors"
                    >
                      {getFileIcon(file.mime_type, file.original_filename)}
                    </div>
                  )}

                  <div className="flex items-start justify-between space-x-2">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center space-x-1.5">
                        <h4 className="font-semibold text-xs text-textPrimary truncate" title={file.original_filename}>
                          {file.original_filename}
                        </h4>
                        {file.version > 1 && (
                          <span className="px-1.5 py-0.5 bg-purple-500/20 text-purple-400 rounded text-[9px] font-bold shrink-0">
                            v{file.version}
                          </span>
                        )}
                      </div>

                      {/* Collaboration Provenance Badge */}
                      <div className="mt-1 flex flex-wrap items-center gap-1.5 text-[10px] text-textMuted">
                        <span className="inline-flex items-center space-x-1 px-1.5 py-0.5 rounded-md bg-bgTertiary border border-borderMuted">
                          <Users className="w-3 h-3 text-accentText" />
                          <span className="truncate max-w-[120px]" title={file.uploader_name || 'Member'}>
                            {file.uploader_name || 'Member'}
                          </span>
                        </span>

                        {file.source_title && (
                          <span className="inline-flex items-center space-x-1 px-1.5 py-0.5 rounded-md bg-bgTertiary border border-borderMuted">
                            <MessageSquare className="w-3 h-3 text-blue-400" />
                            <span className="truncate max-w-[110px]" title={file.source_title}>
                              {file.source_title}
                            </span>
                          </span>
                        )}
                      </div>

                      <p className="text-[10px] text-textMuted mt-1.5">
                        {formatSize(file.file_size)} • {new Date(file.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Knowledge Promotion & Actions Bar */}
                <div className="pt-3 mt-3 border-t border-borderMuted flex flex-col space-y-2">
                  <div className="flex items-center justify-between">
                    {file.is_promoted_to_document ? (
                      <span className="px-2 py-0.5 rounded-md text-[10px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/25 flex items-center space-x-1">
                        <Sparkles className="w-3 h-3" />
                        <span>In Documents</span>
                      </span>
                    ) : (
                      <button
                        onClick={() => handlePromoteToDocument(file)}
                        disabled={promotingId === file.id}
                        className="px-2 py-0.5 rounded-md text-[10px] font-medium bg-accentSubtle hover:bg-accent/25 text-accentText border border-accent/30 flex items-center space-x-1 transition-all"
                        title="Add this file into workspace Knowledge Documents for intelligence processing"
                      >
                        {promotingId === file.id ? (
                          <Loader2 className="w-3 h-3 animate-spin" />
                        ) : (
                          <Sparkles className="w-3 h-3" />
                        )}
                        <span>Add to Documents</span>
                      </button>
                    )}

                    <div className="flex items-center space-x-1">
                      <button
                        onClick={() => setPreviewItem(file)}
                        className="p-1 hover:bg-bgHover text-textMuted hover:text-textPrimary rounded"
                        title="Preview"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                      <a
                        href={file.download_url}
                        download={file.original_filename}
                        className="p-1 hover:bg-bgHover text-textMuted hover:text-accentText rounded"
                        title="Download"
                      >
                        <Download className="w-3.5 h-3.5" />
                      </a>
                      <button
                        onClick={() => setVersionItem(file)}
                        className="p-1 hover:bg-bgHover text-textMuted hover:text-purple-400 rounded"
                        title="Version History"
                      >
                        <GitBranch className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => setAuditItem(file)}
                        className="p-1 hover:bg-bgHover text-textMuted hover:text-blue-400 rounded"
                        title="Audit Log"
                      >
                        <ShieldCheck className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => setMoveItem(file)}
                        className="p-1 hover:bg-bgHover text-textMuted hover:text-amber-400 rounded"
                        title="Move Folder"
                      >
                        <Folder className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => handleRename(file)}
                        className="p-1 hover:bg-bgHover text-textMuted hover:text-indigo-400 rounded"
                        title="Rename"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => handleDelete(file)}
                        className="p-1 hover:bg-bgHover text-textMuted hover:text-dangerText rounded"
                        title="Delete"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          /* List View */
          <div className="space-y-2">
            {files.map((file) => (
              <div
                key={file.id}
                className="flex items-center justify-between p-3 bg-bgCard border border-borderColor hover:border-borderHover rounded-xl text-xs transition-colors shadow-sm"
              >
                <div className="flex items-center space-x-3 min-w-0 flex-1">
                  <div className="p-2 rounded-lg bg-bgTertiary shrink-0">
                    {getFileIcon(file.mime_type, file.original_filename)}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center space-x-2">
                      <p className="font-semibold text-textPrimary truncate">{file.original_filename}</p>
                      {file.version > 1 && (
                        <span className="px-1.5 py-0.5 bg-purple-500/20 text-purple-400 rounded text-[9px] font-bold">
                          v{file.version}
                        </span>
                      )}
                      {file.is_promoted_to_document && (
                        <span className="px-1.5 py-0.5 bg-emerald-500/15 text-emerald-400 rounded text-[9px] font-medium border border-emerald-500/30">
                          In Documents
                        </span>
                      )}
                    </div>
                    <p className="text-[10px] text-textMuted flex items-center space-x-2 mt-0.5">
                      <span>Shared by <strong className="text-textPrimary font-medium">{file.uploader_name || 'Member'}</strong></span>
                      {file.source_title && (
                        <>
                          <span>•</span>
                          <span>In <span className="text-accentText">{file.source_title}</span></span>
                        </>
                      )}
                      <span>•</span>
                      <span>{formatSize(file.file_size)}</span>
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-3 sm:space-x-4 text-textMuted shrink-0">
                  <span className="hidden md:inline text-[10px]">{new Date(file.created_at).toLocaleDateString()}</span>
                  
                  {!file.is_promoted_to_document && (
                    <button
                      onClick={() => handlePromoteToDocument(file)}
                      disabled={promotingId === file.id}
                      className="px-2 py-1 rounded-lg text-[10px] font-medium bg-accentSubtle hover:bg-accent/25 text-accentText border border-accent/30 hidden sm:flex items-center space-x-1 transition-all"
                      title="Add to Documents Knowledge Workspace"
                    >
                      {promotingId === file.id ? (
                        <Loader2 className="w-3 h-3 animate-spin" />
                      ) : (
                        <Sparkles className="w-3 h-3" />
                      )}
                      <span>Add to Docs</span>
                    </button>
                  )}

                  <div className="flex items-center space-x-1">
                    <button
                      onClick={() => setPreviewItem(file)}
                      className="p-1.5 hover:bg-bgHover text-textMuted hover:text-textPrimary rounded-lg"
                      title="Preview"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                    <a
                      href={file.download_url}
                      download={file.original_filename}
                      className="p-1.5 hover:bg-bgHover text-textMuted hover:text-accentText rounded-lg"
                      title="Download"
                    >
                      <Download className="w-4 h-4" />
                    </a>
                    <button
                      onClick={() => setVersionItem(file)}
                      className="p-1.5 hover:bg-bgHover text-textMuted hover:text-purple-400 rounded-lg"
                      title="Version History"
                    >
                      <GitBranch className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => setAuditItem(file)}
                      className="p-1.5 hover:bg-bgHover text-textMuted hover:text-blue-400 rounded-lg"
                      title="Audit Log"
                    >
                      <ShieldCheck className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => setMoveItem(file)}
                      className="p-1.5 hover:bg-bgHover text-textMuted hover:text-amber-400 rounded-lg"
                      title="Move"
                    >
                      <Folder className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleRename(file)}
                      className="p-1.5 hover:bg-bgHover text-textMuted hover:text-indigo-400 rounded-lg"
                      title="Rename"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(file)}
                      className="p-1.5 hover:bg-bgHover text-textMuted hover:text-dangerText rounded-lg"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Pagination Footer */}
      <div className="p-3 border-t border-borderMuted bg-bgSecondary flex items-center justify-between text-xs text-textMuted">
        <span>
          Showing {files.length} of {totalFiles} total shared files (Page {currentPage} of {totalPages})
        </span>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            disabled={currentPage <= 1}
            className="p-1.5 rounded-lg border border-borderColor hover:bg-bgHover disabled:opacity-40 disabled:hover:bg-transparent text-textPrimary"
            title="Previous Page"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="font-semibold text-textPrimary px-1">{currentPage}</span>
          <button
            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            disabled={currentPage >= totalPages}
            className="p-1.5 rounded-lg border border-borderColor hover:bg-bgHover disabled:opacity-40 disabled:hover:bg-transparent text-textPrimary"
            title="Next Page"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Upload / Share Modal */}
      <FileUploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUploadSuccess={handleUploadSuccess}
        organizationId={currentOrg?.id}
        workspaceId={currentWorkspace?.id}
        folderId={currentFolderId || undefined}
        token={token || undefined}
      />

      {/* Universal Preview Modal */}
      <FilePreviewModal item={previewItem} onClose={() => setPreviewItem(null)} />

      {/* Move Folder Modal */}
      <MoveFolderModal
        item={moveItem}
        isOpen={!!moveItem}
        onClose={() => setMoveItem(null)}
        onSuccess={(updated) => {
          setFiles((prev) => prev.map((f) => (f.id === updated.id ? updated : f)));
        }}
        token={token || undefined}
        workspaceId={currentWorkspace?.id}
      />

      {/* Version History Modal */}
      <VersionHistoryModal
        item={versionItem}
        isOpen={!!versionItem}
        onClose={() => setVersionItem(null)}
        onVersionChanged={(updated) => {
          setFiles((prev) => prev.map((f) => (f.id === updated.id ? updated : f)));
        }}
        token={token || undefined}
      />

      {/* Security Audit Log Modal */}
      <AuditLogModal
        item={auditItem}
        isOpen={!!auditItem}
        onClose={() => setAuditItem(null)}
        token={token || undefined}
      />

      {/* Storage Analytics Modal */}
      <StorageStatsModal
        isOpen={isStorageStatsOpen}
        onClose={() => setIsStorageStatsOpen(false)}
        onPreviewItem={(item) => setPreviewItem(item)}
        organizationId={currentOrg?.id}
        workspaceId={currentWorkspace?.id}
        token={token || undefined}
      />
    </div>
  );
}
