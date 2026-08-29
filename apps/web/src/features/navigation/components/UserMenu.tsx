import React, { useState, useEffect } from 'react';
import { useAuth } from '../../auth/auth-provider';
import { LogOut, Settings } from 'lucide-react';

interface UserMenuProps {
  onNavigate: (tab: string) => void;
}

export function UserMenu({ onNavigate }: UserMenuProps) {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && open) {
        setOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [open]);

  return (
    <div className="relative shrink-0 inline-block">
      <button 
        type="button"
        onClick={() => setOpen(!open)}
        aria-label="User account menu"
        aria-haspopup="menu"
        aria-expanded={open}
        title="User account menu"
        className="flex items-center justify-center min-h-[44px] min-w-[44px] sm:min-h-0 sm:min-w-0 rounded-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent transition-transform duration-150 active:scale-95 cursor-pointer"
      >
        <div className="h-10 w-10 sm:h-9 sm:w-9 rounded-full bg-accentSubtle flex items-center justify-center text-accentText font-bold text-xs sm:text-xs border border-accent/30 shadow-sm transition-all hover:border-accent">
          {user?.username?.charAt(0).toUpperCase() || 'U'}
        </div>
      </button>

      {open && (
        <>
          <div 
            className="fixed inset-0 z-40 bg-transparent" 
            onClick={() => setOpen(false)} 
            aria-hidden="true" 
          />
          <div 
            role="menu" 
            aria-label="User menu options"
            className="absolute right-0 mt-2 w-52 min-w-[190px] max-w-[240px] rounded-xl bg-bgDialog border border-borderColor text-textPrimary shadow-2xl py-1.5 z-50 animate-in fade-in slide-in-from-top-2 duration-150"
          >
            <div className="px-3.5 py-2 border-b border-borderMuted">
              <p className="text-xs font-semibold text-textPrimary truncate">{user?.username || 'User'}</p>
              <p className="text-[10px] text-textMuted truncate mt-0.5">{user?.email || ''}</p>
            </div>

            <div className="py-1">
              <button 
                type="button"
                role="menuitem"
                onClick={() => {
                  onNavigate('settings');
                  setOpen(false);
                }}
                className="w-full flex items-center gap-2.5 px-3.5 py-2 text-xs font-medium text-textSecondary hover:text-textPrimary hover:bg-bgHover focus-visible:bg-bgHover focus-visible:outline-none text-left transition-colors whitespace-nowrap cursor-pointer"
              >
                <Settings size={14} className="shrink-0 text-textMuted" aria-hidden="true" />
                <span>Settings</span>
              </button>

              <button 
                type="button"
                role="menuitem"
                onClick={() => {
                  logout();
                  setOpen(false);
                }}
                className="w-full flex items-center gap-2.5 px-3.5 py-2 text-xs font-medium text-dangerText hover:bg-dangerBg focus-visible:bg-dangerBg focus-visible:outline-none text-left transition-colors whitespace-nowrap cursor-pointer"
              >
                <LogOut size={14} className="shrink-0 text-dangerText" aria-hidden="true" />
                <span>Log Out</span>
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
export default UserMenu;

