import React from 'react';
import { Sun, Moon, LogOut } from 'lucide-react';
import { useAuth } from '../../auth/auth-provider';

interface SidebarFooterProps {
  collapsed: boolean;
  theme: 'light' | 'dark' | 'system';
  onToggleTheme: () => void;
  onLogout: () => void;
}

export function SidebarFooter({
  collapsed,
  theme,
  onToggleTheme,
  onLogout
}: SidebarFooterProps) {
  const { user, currentOrg } = useAuth();

  return (
    <div className={`border-t border-borderMuted ${collapsed ? 'pt-2 space-y-1.5' : 'pt-3 space-y-2.5'}`}>
      {!collapsed && (
        <div className="flex items-center justify-between px-1">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="h-8 w-8 rounded-full bg-accentSubtle border border-accent/20 flex items-center justify-center text-accentText font-bold text-xs shrink-0">
              {user?.username?.charAt(0).toUpperCase() || 'U'}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold text-textPrimary truncate">{user?.username || 'User'}</p>
              <p className="text-[9px] text-accentText font-medium truncate uppercase tracking-wider">{currentOrg?.role || 'MEMBER'}</p>
            </div>
          </div>
        </div>
      )}

      <div className={`flex items-center ${collapsed ? 'flex-col gap-1.5 items-center' : 'justify-between px-1'}`}>
        <button 
          type="button"
          onClick={onToggleTheme} 
          aria-label={theme === 'dark' ? "Switch to light theme" : "Switch to dark theme"}
          className="h-8 w-8 sm:h-9 sm:w-9 rounded-xl hover:bg-bgHover text-textSecondary hover:text-textPrimary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent transition-colors flex items-center justify-center shrink-0"
          title="Toggle color theme"
        >
          {theme === 'dark' ? <Sun size={16} className="text-amber-400" aria-hidden="true" /> : <Moon size={16} className="text-accent" aria-hidden="true" />}
        </button>
        <button 
          type="button"
          onClick={onLogout} 
          aria-label="Log out of account"
          className="h-8 w-8 sm:h-9 sm:w-9 rounded-xl hover:bg-dangerBg text-dangerText focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-dangerText transition-colors flex items-center justify-center shrink-0" 
          title="Log Out"
        >
          <LogOut size={16} aria-hidden="true" />
        </button>
      </div>
    </div>
  );
}
export default SidebarFooter;
