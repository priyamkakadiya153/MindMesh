import React from 'react';
import { Star, Briefcase, FileText, MessageSquare } from 'lucide-react';
import { FavoriteItem } from '../types';

import { RecentListSkeleton, WidgetErrorCard } from './Skeletons';
import { EmptyState } from '../../../shared/components/EmptyState';

interface FavoriteListProps {
  favorites: FavoriteItem[];
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
}

export function FavoriteList({ favorites = [], loading, error, onRetry }: FavoriteListProps) {
  if (error) {
    return <WidgetErrorCard title="Unable to load starred items" message={error} onRetry={onRetry} />;
  }

  if (loading) {
    return <RecentListSkeleton title="Starred Items" count={3} />;
  }
  const getIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'project':
        return Briefcase;
      case 'document':
        return FileText;
      default:
        return MessageSquare;
    }
  };

  return (
    <div className="glass-panel p-3.5 bg-bgCard border border-borderColor h-full rounded-2xl">
      <div className="flex items-center justify-between mb-2.5 pb-1.5 border-b border-borderMuted">
        <h2 className="text-xs font-semibold text-textPrimary tracking-wide flex items-center gap-2">
          <Star size={15} className="text-accentText" aria-hidden="true" />
          <span>Starred Items</span>
        </h2>
        <span className="text-[9px] text-textMuted font-medium">Bookmarks</span>
      </div>

      <div className="space-y-1.5 max-h-[300px] overflow-y-auto pr-1">
        {favorites.length > 0 ? (
          favorites.map((fav) => {
            const Icon = getIcon(fav.item_type);
            return (
              <div 
                key={fav.id} 
                className="p-2.5 bg-bgTertiary border border-borderMuted rounded-xl flex items-center justify-between group hover:border-accent/20 transition-all"
              >
                <div className="flex items-center gap-2.5">
                  <div className="p-1.5 bg-amber-500/10 text-amber-500 rounded-lg" aria-hidden="true">
                    <Icon size={13} />
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-textPrimary group-hover:text-accentText transition-colors">
                      {fav.name}
                    </p>
                    <span className="text-[9px] text-textMuted font-medium capitalize">
                      {fav.item_type}
                    </span>
                  </div>
                </div>

                <div className="p-1 text-amber-500" aria-hidden="true">
                  <Star size={11} fill="currentColor" />
                </div>
              </div>
            );
          })
        ) : (
          <EmptyState
            title="No Starred Bookmarks"
            description="Star projects or documents across your workspace for quick access."
            icon={Star}
            variant="compact"
          />
        )}
      </div>
    </div>
  );
}
