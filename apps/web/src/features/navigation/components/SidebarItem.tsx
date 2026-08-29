import React from 'react';
import { LucideIcon } from 'lucide-react';

interface SidebarItemProps {
  label: string;
  icon: LucideIcon;
  isActive: boolean;
  collapsed: boolean;
  badge?: number | string | null;
  onClick: () => void;
}

export const SidebarItem = React.memo(function SidebarItem({
  label,
  icon: Icon,
  isActive,
  collapsed,
  badge,
  onClick
}: SidebarItemProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      aria-current={isActive ? 'page' : undefined}
      className={`flex items-center rounded-xl text-xs font-medium transition-all duration-200 border border-transparent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
        collapsed ? 'h-9 w-9 sm:h-10 sm:w-10 mx-auto justify-center px-0 relative' : 'w-full h-9 sm:h-10 gap-3 px-3'
      } ${
        isActive
          ? 'bg-accentSubtle text-accentText border-accent/20 font-semibold shadow-sm'
          : 'text-textSecondary hover:text-textPrimary hover:bg-bgHover'
      }`}
      title={label}
    >
      <div className="w-4 h-4 sm:w-5 sm:h-5 flex items-center justify-center shrink-0">
        <Icon size={18} className={isActive ? 'text-accentText' : 'text-textMuted'} aria-hidden="true" />
      </div>

      {!collapsed && (
        <div className="flex items-center justify-between flex-1 min-w-0">
          <span className="truncate whitespace-nowrap">{label}</span>
          {badge !== undefined && badge !== null && Number(badge) > 0 && (
            <span className="px-1.5 py-0.5 text-[10px] font-bold rounded-full bg-amber-500 text-slate-950 shrink-0">
              {badge}
            </span>
          )}
        </div>
      )}

      {collapsed && badge !== undefined && badge !== null && Number(badge) > 0 && (
        <span className="absolute -top-1 -right-1 px-1 py-0.2 text-[9px] font-bold rounded-full bg-amber-500 text-slate-950">
          {badge}
        </span>
      )}
    </button>
  );
});
export default SidebarItem;

