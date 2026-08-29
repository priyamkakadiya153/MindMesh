import React from 'react';
import { Grid, Layers, FileText, Users, Clock } from 'lucide-react';
import { Workspace } from '../../workspace/store';

interface WorkspaceCardProps {
  workspace: Workspace;
  isActive: boolean;
  projectsCount?: number;
  documentsCount?: number;
  membersCount?: number;
  onSelect: () => void;
}

export const WorkspaceCard = React.memo(function WorkspaceCard({
  workspace,
  isActive,
  projectsCount = 0,
  documentsCount = 0,
  membersCount = 1,
  onSelect
}: WorkspaceCardProps) {
  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '';
    try {
      return new Date(dateStr).toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });
    } catch (e) {
      return '';
    }
  };

  const formattedDate = formatDate(workspace.created_at);

  return (
    <div 
      role="button"
      tabIndex={0}
      onClick={onSelect}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onSelect();
        }
      }}
      aria-label={`Select workspace: ${workspace.name}${isActive ? ' (Active)' : ''}`}
      className={`glass-panel p-4 bg-bgCard hover:bg-bgCardHover border cursor-pointer group transition-all duration-300 rounded-2xl focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
        isActive 
          ? 'border-accent shadow-lg shadow-accent/5' 
          : 'border-borderColor hover:border-borderHover'
      }`}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-xl transition-all ${
            isActive 
              ? 'bg-accentSubtle text-accentText' 
              : 'bg-bgTertiary text-textMuted group-hover:text-textPrimary'
          }`} aria-hidden="true">
            <Grid size={16} />
          </div>
          <div>
            <h3 className="text-sm font-bold text-textPrimary group-hover:text-accentText transition-colors">
              {workspace.name}
            </h3>
            <span className="text-[9px] text-textMuted font-semibold uppercase tracking-wider block mt-0.5">
              slug: {workspace.slug}
            </span>
          </div>
        </div>
        {isActive && (
          <span className="text-[8px] uppercase tracking-widest font-bold bg-accent text-white px-2 py-0.5 rounded-full">
            Active
          </span>
        )}
      </div>

      <div className="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-borderMuted text-xs">
        <div className="flex items-center gap-1.5" title={`${projectsCount} Projects`}>
          <Layers size={12} className="text-accentText shrink-0" aria-hidden="true" />
          <span className="text-[11px] text-textSecondary font-semibold">{projectsCount} <span className="text-[9px] font-normal text-textMuted hidden sm:inline">Proj</span></span>
        </div>
        <div className="flex items-center gap-1.5" title={`${documentsCount} Documents`}>
          <FileText size={12} className="text-purple-400 shrink-0" aria-hidden="true" />
          <span className="text-[11px] text-textSecondary font-semibold">{documentsCount} <span className="text-[9px] font-normal text-textMuted hidden sm:inline">Docs</span></span>
        </div>
        <div className="flex items-center gap-1.5" title={`${membersCount} Members`}>
          <Users size={12} className="text-emerald-400 shrink-0" aria-hidden="true" />
          <span className="text-[11px] text-textSecondary font-semibold">{membersCount} <span className="text-[9px] font-normal text-textMuted hidden sm:inline">Mem</span></span>
        </div>
      </div>

      {formattedDate && (
        <div className="mt-2.5 pt-2 border-t border-borderMuted/50 flex items-center justify-between text-[9px] text-textMuted">
          <span className="flex items-center gap-1">
            <Clock size={10} /> Created {formattedDate}
          </span>
          <span className="font-medium">{workspace.status || 'Active'}</span>
        </div>
      )}
    </div>
  );
});
