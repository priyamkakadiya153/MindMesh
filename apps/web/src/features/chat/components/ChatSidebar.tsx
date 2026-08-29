import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom';
import {
  MessageSquare,
  Plus,
  Search,
  Pin,
  PinOff,
  Trash2,
  Edit2,
  Download,
  MoreVertical,
  Check,
  X,
  FileText,
  ChevronDown,
  Clock,
  Sparkles,
  MessageSquareDashed,
  AlertTriangle
} from 'lucide-react';
import { ConversationItem } from '../chat-api';

interface ChatSidebarProps {
  conversations: ConversationItem[];
  activeConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onNewChat: () => void;
  onRenameConversation: (id: string, newTitle: string) => void;
  onDeleteConversation: (id: string) => void;
  onTogglePin: (id: string, isPinned: boolean) => void;
  onExportConversation: (id: string, format: 'markdown' | 'json') => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  loading: boolean;
  hasMore?: boolean;
  onLoadMore?: () => void;
  onCloseMobileDrawer?: () => void;
}

export const ChatSidebar: React.FC<ChatSidebarProps> = ({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewChat,
  onRenameConversation,
  onDeleteConversation,
  onTogglePin,
  onExportConversation,
  searchQuery,
  onSearchChange,
  loading,
  hasMore,
  onLoadMore,
  onCloseMobileDrawer
}) => {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [menuOpenId, setMenuOpenId] = useState<string | null>(null);
  const [menuPosition, setMenuPosition] = useState<{ top?: number; bottom?: number; right: number } | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const pinned = conversations.filter(c => c.is_pinned);
  const recent = conversations.filter(c => !c.is_pinned);

  // Close open menu on Escape key press or page scroll
  useEffect(() => {
    if (!menuOpenId) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setMenuOpenId(null);
        setMenuPosition(null);
      }
    };

    const handleScroll = () => {
      setMenuOpenId(null);
      setMenuPosition(null);
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('scroll', handleScroll, true);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('scroll', handleScroll, true);
    };
  }, [menuOpenId]);

  const handleOpenMenu = (c: ConversationItem, e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    if (menuOpenId === c.id) {
      setMenuOpenId(null);
      setMenuPosition(null);
      return;
    }

    const rect = e.currentTarget.getBoundingClientRect();
    const spaceBelow = window.innerHeight - rect.bottom;
    const menuHeight = 210; // Approx height for menu options
    const rightMargin = Math.max(12, window.innerWidth - rect.right);

    if (spaceBelow < menuHeight && rect.top > menuHeight) {
      // Open upward if near bottom edge
      setMenuPosition({
        bottom: window.innerHeight - rect.top + 6,
        right: rightMargin
      });
    } else {
      // Open downward
      setMenuPosition({
        top: rect.bottom + 6,
        right: rightMargin
      });
    }
    setMenuOpenId(c.id);
  };

  const startRename = (c: ConversationItem, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingId(c.id);
    setEditTitle(c.title);
    setMenuOpenId(null);
    setMenuPosition(null);
  };

  const saveRename = (id: string, e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (editTitle.trim()) {
      onRenameConversation(id, editTitle.trim());
    }
    setEditingId(null);
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '';
    try {
      const d = new Date(dateStr);
      if (isNaN(d.getTime())) return '';

      const now = new Date();
      const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      const yesterday = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
      const target = new Date(d.getFullYear(), d.getMonth(), d.getDate());

      if (target.getTime() === today.getTime()) {
        return 'Today';
      }

      if (target.getTime() === yesterday.getTime()) {
        return 'Yesterday';
      }

      if (d.getFullYear() === now.getFullYear()) {
        return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
      }

      return d.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });
    } catch {
      return '';
    }
  };

  const activeMenuConv = conversations.find(c => c.id === menuOpenId);

  return (
    <div className="w-full md:w-64 lg:w-72 shrink-0 bg-bgSidebar border-b md:border-b-0 md:border-r border-borderColor flex flex-col select-none overflow-hidden">
      {/* 1. Sidebar Header */}
      <div className="p-3 sm:p-3.5 border-b border-borderColor/70 flex items-center justify-between shrink-0 bg-bgSidebar/80 backdrop-blur-sm">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-accentSubtle text-accentText border border-accent/20">
            <Sparkles size={15} />
          </div>
          <div>
            <h3 className="font-semibold text-xs text-textPrimary tracking-tight">AI Conversations</h3>
            <p className="text-[10px] text-textMuted">{conversations.length} total threads</p>
          </div>
        </div>
      </div>

      {/* 2. Main Actions Container: New Conversation & Search Bar */}
      <div className="p-3 sm:p-3.5 space-y-2.5 sm:space-y-3 shrink-0 border-b border-borderMuted/60 bg-bgSidebar">
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-accent hover:bg-accentHover text-white rounded-xl text-xs font-semibold shadow-md shadow-accent/20 transition-all duration-150 active:scale-[0.98] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
        >
          <Plus size={16} className="shrink-0" />
          <span>New Conversation</span>
        </button>

        <div className="relative">
          <Search size={14} className="absolute left-3 top-3 text-textMuted pointer-events-none transition-colors group-focus-within:text-accentText" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search conversations..."
            className="w-full pl-9 pr-8 py-2 bg-bgInput hover:bg-bgHover/60 focus:bg-bgInput border border-borderColor focus:border-accent rounded-xl text-xs text-textPrimary placeholder-textMuted outline-none transition-all duration-150 focus:ring-2 focus:ring-accent/20"
          />
          {searchQuery && (
            <button
              onClick={() => onSearchChange('')}
              className="absolute right-2.5 top-2.5 p-0.5 text-textMuted hover:text-textPrimary rounded-md"
            >
              <X size={13} />
            </button>
          )}
        </div>
      </div>

      {/* 3. Conversation List Scroll Container */}
      <div className="max-h-60 md:max-h-none md:flex-1 overflow-y-auto p-2.5 space-y-4 custom-scrollbar">
        {loading && conversations.length === 0 && (
          <div className="flex flex-col items-center justify-center py-8 text-center text-xs text-textMuted space-y-2">
            <div className="h-5 w-5 rounded-full border-2 border-accent/30 border-t-accent animate-spin" />
            <p>Loading conversations...</p>
          </div>
        )}

        {!loading && conversations.length === 0 && (
          <div className="flex flex-col items-center justify-center py-6 px-3 text-center my-auto space-y-2 rounded-2xl border border-dashed border-borderColor/60 bg-bgCard/40 m-1">
            <div className="h-9 w-9 rounded-xl bg-accentSubtle/60 border border-accent/20 flex items-center justify-center text-accentText shadow-sm">
              <MessageSquareDashed size={18} />
            </div>
            <div className="space-y-0.5">
              <h4 className="text-xs font-semibold text-textPrimary">No AI conversations yet</h4>
              <p className="text-[10px] text-textMuted leading-relaxed max-w-[200px]">
                Start a new conversation to ask questions or summarize documents.
              </p>
            </div>
            <button
              onClick={onNewChat}
              className="mt-1 flex items-center gap-1.5 py-1 px-3 bg-accent/10 hover:bg-accent/20 text-accentText border border-accent/30 rounded-xl text-xs font-semibold transition-all active:scale-95"
            >
              <Plus size={12} />
              <span>Start Conversation</span>
            </button>
          </div>
        )}

        {pinned.length > 0 && (
          <div>
            <div className="flex items-center justify-between px-2 mb-1.5 text-[10px] font-bold tracking-wider uppercase text-amber-500">
              <span className="flex items-center gap-1.5">
                <Pin size={10} /> Pinned ({pinned.length})
              </span>
            </div>
            <div className="space-y-1">
              {pinned.map(c => renderChatItem(c))}
            </div>
          </div>
        )}

        {recent.length > 0 && (
          <div>
            <div className="flex items-center justify-between px-2 mb-1.5 text-[10px] font-bold tracking-wider uppercase text-textMuted">
              <span>Recent ({recent.length})</span>
            </div>
            <div className="space-y-1">
              {recent.map(c => renderChatItem(c))}
            </div>
          </div>
        )}

        {hasMore && (
          <div className="pt-2 text-center">
            <button
              onClick={onLoadMore}
              disabled={loading}
              className="text-xs text-accentText hover:underline font-medium py-1.5 px-3 bg-accentSubtle rounded-xl transition-colors inline-flex items-center gap-1 border border-accent/20 active:scale-95"
            >
              <ChevronDown size={14} /> Load More
            </button>
          </div>
        )}
      </div>

      {/* Floating Action Menu Portal (Rendered outside scroll container to eliminate clipping) */}
      {menuOpenId && menuPosition && activeMenuConv && ReactDOM.createPortal(
        <>
          <div
            className="fixed inset-0 z-40 bg-transparent"
            onClick={(e) => {
              e.stopPropagation();
              setMenuOpenId(null);
              setMenuPosition(null);
            }}
          />
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              position: 'fixed',
              top: menuPosition.top !== undefined ? `${menuPosition.top}px` : undefined,
              bottom: menuPosition.bottom !== undefined ? `${menuPosition.bottom}px` : undefined,
              right: `${menuPosition.right}px`
            }}
            className="w-44 bg-bgDialog border border-borderColor shadow-2xl rounded-2xl py-1 z-50 text-xs animate-in fade-in duration-150 space-y-0.5"
            role="menu"
            aria-label="Conversation actions menu"
          >
            <button
              onClick={(e) => startRename(activeMenuConv, e)}
              className="w-full flex items-center gap-2.5 px-3.5 py-2 text-textSecondary hover:bg-bgHover hover:text-textPrimary text-left transition-colors font-medium"
            >
              <Edit2 size={13} className="text-textMuted" /> Rename
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onTogglePin(activeMenuConv.id, !activeMenuConv.is_pinned);
                setMenuOpenId(null);
                setMenuPosition(null);
              }}
              className="w-full flex items-center gap-2.5 px-3.5 py-2 text-textSecondary hover:bg-bgHover hover:text-textPrimary text-left transition-colors font-medium"
            >
              {activeMenuConv.is_pinned ? (
                <>
                  <PinOff size={13} className="text-amber-500" /> Unpin
                </>
              ) : (
                <>
                  <Pin size={13} className="text-textMuted" /> Pin
                </>
              )}
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onExportConversation(activeMenuConv.id, 'markdown');
                setMenuOpenId(null);
                setMenuPosition(null);
              }}
              className="w-full flex items-center gap-2.5 px-3.5 py-2 text-textSecondary hover:bg-bgHover hover:text-textPrimary text-left transition-colors font-medium"
            >
              <Download size={13} className="text-textMuted" /> Export Markdown
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onExportConversation(activeMenuConv.id, 'json');
                setMenuOpenId(null);
                setMenuPosition(null);
              }}
              className="w-full flex items-center gap-2.5 px-3.5 py-2 text-textSecondary hover:bg-bgHover hover:text-textPrimary text-left transition-colors font-medium"
            >
              <FileText size={13} className="text-textMuted" /> Export JSON
            </button>

            <div className="my-1 border-t border-borderColor/60" />

            <button
              onClick={(e) => {
                e.stopPropagation();
                setDeletingId(activeMenuConv.id);
                setMenuOpenId(null);
                setMenuPosition(null);
              }}
              className="w-full flex items-center gap-2.5 px-3.5 py-2 text-dangerText hover:bg-dangerBg text-left transition-colors font-medium"
            >
              <Trash2 size={13} /> Delete
            </button>
          </div>
        </>,
        document.body
      )}

      {/* Destructive Delete Confirmation Modal */}
      {deletingId && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-bgDialog border border-borderColor rounded-2xl p-5 max-w-sm w-full space-y-4 shadow-2xl animate-in zoom-in-95 duration-150">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-dangerBg text-dangerText rounded-xl border border-dangerBorder shrink-0">
                <AlertTriangle size={20} />
              </div>
              <div>
                <h4 className="font-bold text-sm text-textPrimary">Delete conversation?</h4>
                <p className="text-xs text-textMuted mt-0.5 leading-relaxed">This action cannot be undone.</p>
              </div>
            </div>
            <div className="flex items-center justify-end gap-2.5 pt-2">
              <button
                type="button"
                onClick={() => setDeletingId(null)}
                className="px-4 py-2 rounded-xl border border-borderColor hover:bg-bgHover text-xs text-textSecondary font-medium transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => {
                  onDeleteConversation(deletingId);
                  setDeletingId(null);
                }}
                className="px-4 py-2 rounded-xl bg-dangerBg hover:bg-dangerBg/80 border border-dangerBorder text-xs text-dangerText font-semibold shadow-sm transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  function renderChatItem(c: ConversationItem) {
    const isActive = c.id === activeConversationId;
    const isEditing = c.id === editingId;

    return (
      <div
        key={c.id}
        onClick={() => {
          onSelectConversation(c.id);
          if (onCloseMobileDrawer) onCloseMobileDrawer();
        }}
        className={`group relative flex items-center justify-between px-3 py-2.5 rounded-xl text-xs cursor-pointer transition-all duration-150 ${
          isActive
            ? 'bg-accentSubtle text-accentText border border-accent/30 font-medium shadow-sm'
            : 'hover:bg-bgHover text-textSecondary hover:text-textPrimary border border-transparent'
        }`}
      >
        {isActive && (
          <div className="absolute left-0 top-2 bottom-2 w-1 bg-accent rounded-r-full" />
        )}

        <div className="flex items-center gap-2.5 min-w-0 flex-1 pl-1 pr-1">
          <MessageSquare
            size={15}
            className={`shrink-0 ${isActive ? 'text-accentText' : 'text-textMuted group-hover:text-accentText transition-colors'}`}
          />
          
          {isEditing ? (
            <form onSubmit={(e) => saveRename(c.id, e)} className="flex items-center gap-1 flex-1 min-w-0">
              <input
                type="text"
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                autoFocus
                onClick={(e) => e.stopPropagation()}
                className="w-full bg-bgInput border border-accent rounded-lg px-2 py-0.5 text-xs text-textPrimary focus:outline-none"
              />
              <button type="submit" onClick={(e) => e.stopPropagation()} className="text-successText hover:opacity-80 p-1">
                <Check size={13} />
              </button>
              <button type="button" onClick={(e) => { e.stopPropagation(); setEditingId(null); }} className="text-textMuted hover:text-textPrimary p-1">
                <X size={13} />
              </button>
            </form>
          ) : (
            <div className="min-w-0 flex-1">
              <span className="truncate block text-textPrimary font-medium text-xs leading-snug">{c.title}</span>
              <span className="text-[10px] text-textMuted flex items-center gap-1 mt-0.5">
                <Clock size={9} className="shrink-0" /> {formatDate(c.last_message_at || c.updated_at)}
              </span>
            </div>
          )}
        </div>

        {!isEditing && (
          <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onTogglePin(c.id, !c.is_pinned);
              }}
              title={c.is_pinned ? 'Unpin chat' : 'Pin chat'}
              className="p-1 hover:bg-bgCard rounded-lg text-textMuted hover:text-amber-500 transition-colors"
            >
              {c.is_pinned ? <PinOff size={13} /> : <Pin size={13} />}
            </button>

            <button
              onClick={(e) => handleOpenMenu(c, e)}
              aria-label="Conversation actions"
              title="Conversation actions"
              className="p-1 hover:bg-bgCard rounded-lg text-textMuted hover:text-textPrimary transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent"
            >
              <MoreVertical size={13} />
            </button>
          </div>
        )}
      </div>
    );
  }
};
