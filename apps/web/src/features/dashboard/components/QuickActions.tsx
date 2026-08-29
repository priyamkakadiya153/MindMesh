import React from 'react';
import { Plus, FolderPlus, MessageSquare, UserPlus, Grid } from 'lucide-react';

interface QuickActionsProps {
  onNewProject: () => void;
  onUploadDoc: () => void;
  onNewChat: () => void;
  onInviteMember: () => void;
  onCreateWorkspace: () => void;
}

export function QuickActions({
  onNewProject,
  onUploadDoc,
  onNewChat,
  onInviteMember,
  onCreateWorkspace
}: QuickActionsProps) {
  const actions = [
    { label: 'New Project', icon: Plus, color: 'indigo', action: onNewProject },
    { label: 'Upload Document', icon: FolderPlus, color: 'purple', action: onUploadDoc },
    { label: 'Start AI Chat', icon: MessageSquare, color: 'emerald', action: onNewChat },
    { label: 'Invite Member', icon: UserPlus, color: 'blue', action: onInviteMember },
    { label: 'New Workspace', icon: Grid, color: 'pink', action: onCreateWorkspace }
  ];

  return (
    <div className="mb-3.5">
      <h2 className="text-[10px] text-textMuted uppercase tracking-widest font-semibold mb-2">Quick Actions</h2>
      <div className="flex flex-wrap gap-2">
        {actions.map((act, i) => {
          const Icon = act.icon;
          return (
            <button
              key={i}
              type="button"
              onClick={act.action}
              aria-label={act.label}
              title={act.label}
              className="px-3 py-1.5 bg-bgCard hover:bg-bgHover border border-borderColor hover:border-accent/40 text-textPrimary hover:text-accentText text-xs font-semibold rounded-xl flex items-center gap-2 group transition-all duration-300 shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            >
              <div className="p-1 rounded-lg bg-accentSubtle text-accentText group-hover:scale-110 transition-transform duration-300" aria-hidden="true">
                <Icon size={13} />
              </div>
              <span>{act.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
