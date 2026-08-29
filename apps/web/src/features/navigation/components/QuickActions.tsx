import React from 'react';
import { useNavigationStore } from '../store';
import { Sparkles, MessageSquare, Briefcase, Settings } from 'lucide-react';

export function QuickActions() {
  const { setActiveTab } = useNavigationStore();

  const actions = [
    { label: 'AI Chat', tab: 'chat', icon: MessageSquare },
    { label: 'Projects', tab: 'projects', icon: Briefcase },
    { label: 'Preferences', tab: 'settings', icon: Settings }
  ];

  return (
    <div className="flex gap-2">
      {actions.map((act, i) => {
        const Icon = act.icon;
        return (
          <button
            key={i}
            onClick={() => setActiveTab(act.tab)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-bgCard hover:bg-bgHover border border-borderColor text-[10px] text-textSecondary hover:text-textPrimary transition-all"
          >
            <Icon size={12} className="text-accentText" />
            <span>{act.label}</span>
          </button>
        );
      })}
    </div>
  );
}
export default QuickActions;
