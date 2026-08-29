import React from 'react';
import { Briefcase, Star, ArrowRight, Plus } from 'lucide-react';
import { RecentProject } from '../types';
import { EmptyState } from '../../../shared/components/EmptyState';
import { RecentListSkeleton, WidgetErrorCard } from './Skeletons';

interface RecentProjectsProps {
  projects: RecentProject[];
  favorites: string[];
  onToggleFavorite: (id: string, name: string, slug: string) => void;
  onNavigateToProjects: () => void;
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
}

function RecentProjectsComponent({
  projects = [],
  favorites = [],
  onToggleFavorite,
  onNavigateToProjects,
  loading,
  error,
  onRetry
}: RecentProjectsProps) {
  if (error) {
    return <WidgetErrorCard title="Unable to load Recent Projects" message={error} onRetry={onRetry} />;
  }

  if (loading) {
    return <RecentListSkeleton title="Recent Projects" />;
  }
  return (
    <div className="bg-bgCard border border-borderColor text-textPrimary rounded-2xl p-3.5 shadow-sm flex flex-col justify-between h-full">
      <div>
        <div className="flex items-center justify-between mb-2.5 pb-1.5 border-b border-borderColor">
          <h2 className="text-xs font-semibold text-textPrimary tracking-wide flex items-center gap-2">
            <Briefcase size={15} className="text-accentText" aria-hidden="true" />
            <span>Recent Projects</span>
          </h2>
          <span className="text-[9px] bg-accentSubtle text-accentText border border-accent/20 px-2 py-0.5 rounded-full font-medium">
            {projects.length > 0 ? 'Active' : 'Empty'}
          </span>
        </div>

        <div className="space-y-1.5 max-h-[300px] overflow-y-auto pr-1">
          {projects.length > 0 ? (
            projects.map((proj) => {
              const isFav = favorites.includes(proj.id);
              return (
                <div 
                  key={proj.id} 
                  className="p-2.5 bg-bgTertiary border border-borderMuted hover:border-accent/30 rounded-xl flex items-center justify-between group transition-all"
                >
                  <div className="flex items-center gap-2.5">
                    <div className="p-1.5 bg-accentSubtle text-accentText rounded-lg" aria-hidden="true">
                      <Briefcase size={13} />
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-textPrimary group-hover:text-accentText transition-colors">
                        {proj.name}
                      </p>
                      <span className="text-[9px] text-textMuted font-medium">slug: {proj.slug}</span>
                    </div>
                  </div>

                  <button 
                    type="button"
                    onClick={() => onToggleFavorite(proj.id, proj.name, proj.slug)}
                    aria-label={isFav ? `Remove ${proj.name} from favorites` : `Add ${proj.name} to favorites`}
                    title={isFav ? "Remove from favorites" : "Add to favorites"}
                    className={`p-1 rounded-lg border transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
                      isFav 
                        ? 'bg-amber-500/10 text-amber-500 border-amber-500/30' 
                        : 'bg-transparent text-textMuted hover:text-textPrimary border-borderMuted'
                    }`}
                  >
                    <Star size={13} fill={isFav ? 'currentColor' : 'none'} aria-hidden="true" />
                  </button>
                </div>
              );
            })
          ) : (
            <EmptyState
              title="No Recent Projects"
              description="Create a project to start organizing team tasks and files."
              icon={Briefcase}
              variant="card"
              primaryAction={{
                label: "Create Project",
                onClick: onNavigateToProjects,
                icon: Plus
              }}
            />
          )}
        </div>
      </div>

      <div className="mt-3 pt-2 border-t border-borderColor flex justify-end">
        <button 
          type="button"
          onClick={onNavigateToProjects}
          className="text-xs font-semibold text-accentText hover:underline flex items-center gap-1 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent rounded"
        >
          <span>View All Projects</span>
          <ArrowRight size={13} aria-hidden="true" />
        </button>
      </div>

      <button 
        type="button"
        onClick={onNavigateToProjects}
        className="mt-2.5 w-full py-1.5 bg-accentSubtle text-accentText hover:bg-accent/20 text-xs font-semibold rounded-xl border border-accent/20 flex items-center justify-center gap-1.5 transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
      >
        <span>Manage Projects</span>
        <ArrowRight size={12} aria-hidden="true" />
      </button>
    </div>
  );
}

export const RecentProjects = React.memo(RecentProjectsComponent);
export default RecentProjects;
