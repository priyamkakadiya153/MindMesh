import React from 'react';
import { Briefcase, FileText, MessageSquare, Grid, Activity } from 'lucide-react';
import { Stats } from '../types';
import { StatsSkeleton, WidgetErrorCard } from './Skeletons';

interface DashboardStatsProps {
  stats: Stats;
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
}

export function DashboardStats({ stats, loading, error, onRetry }: DashboardStatsProps) {
  if (error) {
    return <WidgetErrorCard title="Unable to load statistics" message={error} onRetry={onRetry} />;
  }

  if (loading || !stats) {
    return <StatsSkeleton />;
  }
  const cards = [
    {
      label: 'Workspaces',
      count: stats.workspaces_count || 0,
      trend: stats.workspaces_count === 1 ? '1 workspace' : `${stats.workspaces_count || 0} workspaces`,
      status: stats.workspaces_count > 0 ? 'Active' : 'Empty',
      icon: Grid,
      color: 'indigo'
    },
    {
      label: 'Indexed Projects',
      count: stats.projects_count || 0,
      trend: (stats.projects_pending_count || 0) > 0 
        ? `${stats.projects_pending_count} pending indexing` 
        : (stats.projects_count || 0) > 0 
          ? `${stats.projects_indexed_count ?? stats.projects_count} indexed` 
          : 'No projects',
      status: (stats.projects_pending_count || 0) > 0 
        ? 'Indexing' 
        : (stats.projects_count || 0) > 0 
          ? 'Active' 
          : 'Pending',
      icon: Briefcase,
      color: 'purple'
    },
    {
      label: 'Knowledge Chunks',
      count: stats.chunks_count ?? 0,
      trend: stats.documents_count === 0 
        ? 'No documents indexed yet' 
        : `${stats.documents_indexed_count ?? 0} / ${stats.documents_count} documents indexed`,
      status: stats.documents_count === 0 
        ? 'Pending' 
        : (stats.indexing_status === 'INDEXING' ? 'Indexing' : stats.indexing_status === 'COMPLETED' ? 'Completed' : 'Active'),
      icon: FileText,
      color: 'emerald'
    },
    {
      label: 'Conversations',
      count: stats.chats_count || 0,
      trend: (stats.messages_today_count || 0) > 0 
        ? `${stats.messages_today_count} messages today` 
        : 'No activity today',
      status: stats.chats_count > 0 ? 'Active' : 'Offline',
      icon: MessageSquare,
      color: 'blue'
    }
  ];

  return (
    <div className="grid grid-cols-[repeat(auto-fit,minmax(min(100%,200px),1fr))] gap-3 mb-3.5">
      {cards.map((card, i) => {
        const Icon = card.icon;
        return (
          <div key={i} className="glass-panel p-3.5 bg-bgCard hover:bg-bgCardHover border border-borderColor hover:border-accent/20 transition-all duration-300 flex flex-col justify-between group rounded-xl">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-[10px] text-textMuted uppercase tracking-widest font-semibold">{card.label}</p>
                <h3 className="text-2xl font-extrabold text-textPrimary tracking-tight mt-1 leading-none">
                  {card.count}
                </h3>
              </div>
              <div className="p-1.5 rounded-lg bg-accentSubtle text-accentText group-hover:scale-110 transition-transform duration-300">
                <Icon size={16} />
              </div>
            </div>
            
            <div className="flex items-center justify-between mt-2.5 pt-2 border-t border-borderMuted text-[10px]">
              <span className="text-textMuted flex items-center gap-1">
                <Activity size={10} className="text-accentText" />
                {card.trend}
              </span>
              <span className="text-accentText font-semibold uppercase tracking-wider text-[9px]">{card.status}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
export default DashboardStats;

