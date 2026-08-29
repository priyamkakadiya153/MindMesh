import React from 'react';
import { Briefcase } from 'lucide-react';
import { RecentProject } from '../types';

interface ProjectWidgetProps {
  projects: RecentProject[];
}

export function ProjectWidget({ projects }: ProjectWidgetProps) {
  return (
    <div className="glass-panel p-5 bg-bgCard border border-borderColor h-full">
      <div className="flex items-center justify-between mb-4 pb-2 border-b border-borderMuted">
        <h3 className="text-sm font-semibold text-textPrimary tracking-wide flex items-center gap-2">
          <Briefcase size={16} className="text-accentText" />
          <span>Active Projects</span>
        </h3>
      </div>

      <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
        {projects.map((proj) => (
          <div key={proj.id} className="p-3 bg-bgTertiary border border-borderMuted rounded-xl flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-textPrimary">{proj.name}</p>
              <span className="text-[9px] text-textMuted font-medium">slug: {proj.slug}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
