import React from 'react';
import { Search, Bell, Menu } from 'lucide-react';
import { OrganizationSwitcher } from '../../../components/auth/OrganizationSwitcher';
import { WorkspaceSwitcher } from '../../../navigation/WorkspaceSwitcher';

interface DashboardHeaderProps {
  activeTab: string;
  organizationName?: string;
  onSearch: (query: string) => void;
  onOpenSearchModal?: () => void;
  unreadNotificationsCount: number;
  onNotificationsClick: () => void;
}

export function DashboardHeader({
  activeTab,
  organizationName = 'Personal',
  onSearch,
  onOpenSearchModal,
  unreadNotificationsCount,
  onNotificationsClick
}: DashboardHeaderProps) {
  return (
    <header className="flex flex-col md:flex-row md:items-center justify-between mb-8 pb-4 border-b border-borderColor gap-4">
      <div>
        <h2 className="title-display text-2xl font-bold tracking-tight text-textPrimary capitalize">
          {activeTab}
        </h2>
        <p className="text-xs text-textMuted mt-1">
          Active Tenant: <span className="text-accentText font-semibold">{organizationName}</span>
        </p>
      </div>
      
      <div className="flex flex-wrap items-center gap-4">
        <OrganizationSwitcher />
        <WorkspaceSwitcher />

        {/* Universal Search Bar Trigger */}
        <button
          onClick={onOpenSearchModal}
          className="relative w-full md:w-64 flex items-center justify-between pl-9 pr-3 py-2 bg-bgInput hover:bg-bgHover border border-borderColor hover:border-accent/30 rounded-xl text-xs text-textMuted hover:text-textPrimary transition-all text-left group"
        >
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-textMuted group-hover:text-accentText transition-colors" />
          <span className="truncate">Universal Search...</span>
          <kbd className="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] text-textMuted bg-bgTertiary border border-borderMuted rounded font-mono">
            ⌘K
          </kbd>
        </button>
        
        {/* Action Bar notifications trigger */}
        <button 
          onClick={onNotificationsClick}
          className="relative p-2 rounded-xl bg-bgInput hover:bg-bgHover border border-borderColor text-textMuted hover:text-textPrimary transition-all shrink-0"
        >
          <Bell size={16} />
          {unreadNotificationsCount > 0 && (
            <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-accent animate-pulse"></span>
          )}
        </button>
      </div>
    </header>
  );
}

