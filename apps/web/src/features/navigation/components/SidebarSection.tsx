import React from 'react';

interface SidebarSectionProps {
  title: string;
  collapsed: boolean;
  children: React.ReactNode;
}

export function SidebarSection({ title, collapsed, children }: SidebarSectionProps) {
  return (
    <div className={`border-t border-borderMuted ${collapsed ? 'pt-0.5 space-y-0' : 'pt-1 space-y-0'}`}>
      {!collapsed && (
        <span className="px-3 text-[9px] font-bold text-textMuted uppercase tracking-widest block mb-0">
          {title}
        </span>
      )}
      <div className="space-y-0">{children}</div>
    </div>
  );
}
export default SidebarSection;
