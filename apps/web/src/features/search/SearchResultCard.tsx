import React from 'react';
import {
  FileText,
  FolderKanban,
  CheckSquare,
  MessageSquare,
  BookOpen,
  User,
  Workflow,
  Building2,
  FileCode,
  Calendar,
  Layers,
  Tag,
  CheckCircle2,
  Users,
  ChevronRight,
} from 'lucide-react';
import { UniversalSearchResultItem } from './types';

interface SearchResultCardProps {
  item: UniversalSearchResultItem;
  query?: string;
  onSelect?: (item: UniversalSearchResultItem) => void;
}

export function SearchResultCard({ item, query = '', onSelect }: SearchResultCardProps) {
  const getEntityIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'document':
      case 'file':
        return <FileText className="w-4 h-4 text-emerald-400" />;
      case 'project':
        return <FolderKanban className="w-4 h-4 text-indigo-400" />;
      case 'task':
        return <CheckSquare className="w-4 h-4 text-amber-400" />;
      case 'chat':
      case 'message':
      case 'conversation':
        return <MessageSquare className="w-4 h-4 text-sky-400" />;
      case 'knowledge':
        return <BookOpen className="w-4 h-4 text-purple-400" />;
      case 'user':
        return <User className="w-4 h-4 text-blue-400" />;
      case 'workflow':
        return <Workflow className="w-4 h-4 text-pink-400" />;
      case 'workspace':
      case 'organization':
        return <Building2 className="w-4 h-4 text-cyan-400" />;
      case 'meeting':
        return <Calendar className="w-4 h-4 text-violet-400" />;
      case 'decision':
        return <CheckCircle2 className="w-4 h-4 text-teal-400" />;
      case 'team':
        return <Users className="w-4 h-4 text-indigo-300" />;
      case 'collection':
        return <Layers className="w-4 h-4 text-amber-300" />;
      default:
        return <Tag className="w-4 h-4 text-textMuted" />;
    }
  };

  const getBadgeColor = (type: string) => {
    switch (type.toLowerCase()) {
      case 'document':
      case 'file':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'project':
        return 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20';
      case 'task':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
      case 'chat':
        return 'bg-sky-500/10 text-sky-400 border-sky-500/20';
      case 'knowledge':
        return 'bg-purple-500/10 text-purple-400 border-purple-500/20';
      case 'user':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
      case 'workflow':
        return 'bg-pink-500/10 text-pink-400 border-pink-500/20';
      default:
        return 'bg-bgTertiary text-textMuted border-borderMuted';
    }
  };

  const formatDate = (isoString?: string) => {
    if (!isoString) return '';
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
    } catch {
      return '';
    }
  };

  // Highlight matched terms in title or snippet
  const renderHighlightedText = (text: string) => {
    if (!query || !query.trim()) return text;
    const words = query.trim().split(/\s+/).filter(Boolean);
    if (words.length === 0) return text;

    const regex = new RegExp(`(${words.map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`, 'gi');
    const parts = text.split(regex);

    return parts.map((part, i) =>
      words.some((w) => w.toLowerCase() === part.toLowerCase()) ? (
        <mark key={i} className="bg-accentSubtle text-accentText px-0.5 rounded font-medium">
          {part}
        </mark>
      ) : (
        part
      )
    );
  };

  return (
    <div
      onClick={() => onSelect && onSelect(item)}
      className="group p-4 bg-bgCard hover:bg-bgCardHover border border-borderColor hover:border-accent/30 rounded-xl transition-all duration-200 cursor-pointer flex flex-col justify-between gap-2"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="p-2 rounded-lg bg-bgTertiary border border-borderMuted shrink-0">
            {getEntityIcon(item.entity_type)}
          </div>
          <div className="min-w-0">
            <h4 className="text-sm font-semibold text-textPrimary group-hover:text-accentText transition-colors truncate">
              {renderHighlightedText(item.title)}
            </h4>
            <div className="flex flex-wrap items-center gap-2 mt-1 text-[11px] text-textMuted">
              <span className={`px-2 py-0.5 rounded-md text-[10px] font-medium border uppercase tracking-wider ${getBadgeColor(item.entity_type)}`}>
                {item.entity_type}
              </span>
              {item.workspace_name && (
                <span className="bg-bgTertiary text-textMuted px-2 py-0.5 rounded-md border border-borderMuted truncate max-w-[140px]">
                  {item.workspace_name}
                </span>
              )}
              {item.updated_at && (
                <span className="text-textMuted">Updated {formatDate(item.updated_at)}</span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {item.score > 1.0 && (
            <span className="text-[10px] bg-accentSubtle text-accentText px-2 py-0.5 rounded-full border border-accent/20 font-medium">
              {(item.score * 10).toFixed(0)}% Match
            </span>
          )}
          <ChevronRight className="w-4 h-4 text-textMuted group-hover:text-accentText group-hover:translate-x-0.5 transition-all" />
        </div>
      </div>

      {item.snippet && (
        <p className="text-xs text-textSecondary line-clamp-2 leading-relaxed pl-11">
          {renderHighlightedText(item.snippet)}
        </p>
      )}

      {item.tags && item.tags.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5 pl-11 pt-1">
          {item.tags.slice(0, 4).map((tag, idx) => (
            <span key={idx} className="text-[10px] bg-bgTertiary text-textMuted border border-borderMuted px-2 py-0.5 rounded-md">
              #{tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
