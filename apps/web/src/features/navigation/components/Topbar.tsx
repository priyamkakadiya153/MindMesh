import { Menu } from 'lucide-react';
import { useNavigationStore } from '../store';
import { OrganizationSwitcher } from './OrganizationSwitcher';
import { WorkspaceSwitcher } from './WorkspaceSwitcher';
import { GlobalSearchEntry } from './GlobalSearchEntry';
import { NotificationBell } from './NotificationBell';
import { UserMenu } from './UserMenu';

interface TopbarProps {
  onNotificationsClick: () => void;
  hasUnreadNotifications?: boolean;
  unreadCount?: number;
}

export function Topbar({
  onNotificationsClick,
  hasUnreadNotifications,
  unreadCount = 0
}: TopbarProps) {
  const { setActiveTab, toggleMobileOpen } = useNavigationStore();

  return (
    <header className="flex flex-col md:flex-row md:items-center justify-between mb-3 sm:mb-4 pb-2.5 sm:pb-3 border-b border-borderColor gap-2.5 sm:gap-3 transition-all duration-200 w-full min-w-0">
      {/* Top Main Row: Mobile Trigger + Selectors + Desktop Search + Controls */}
      <div className="flex items-center justify-between md:justify-start gap-3 sm:gap-4 md:gap-6 w-full min-w-0">
        {/* Left Side: Mobile Drawer Button & Selectors */}
        <div className="flex items-center gap-2.5 sm:gap-3.5 min-w-0 shrink-0">
          <button
            onClick={toggleMobileOpen}
            className="md:hidden p-2 rounded-xl border border-borderColor bg-bgCard hover:bg-bgHover text-textSecondary shrink-0 transition-colors"
            aria-label="Open mobile navigation drawer"
          >
            <Menu size={18} />
          </button>
          
          <div className="flex items-center gap-2 sm:gap-3 min-w-0">
            <OrganizationSwitcher />
            <span className="text-textMuted/40 font-light text-sm select-none hidden sm:inline-block">/</span>
            <WorkspaceSwitcher />
          </div>
        </div>

        {/* Desktop / Laptop Fluid Search Bar (Shrinks FIRST on narrow desktop/laptop width) */}
        <div className="hidden md:block flex-1 min-w-[200px] max-w-[540px] laptop:max-w-[440px] mx-2 md:mx-4 lg:mx-6">
          <GlobalSearchEntry />
        </div>

        {/* Right Side: Notifications & Profile Avatar (Always aligned and pinned) */}
        <div className="flex items-center gap-3 sm:gap-3.5 shrink-0 ml-auto md:ml-0">
          <NotificationBell 
            unreadCount={unreadCount}
            hasUnread={hasUnreadNotifications || unreadCount > 0} 
            onClick={onNotificationsClick} 
          />
          <UserMenu onNavigate={setActiveTab} />
        </div>
      </div>

      {/* Mobile / Tablet Full-Width Search Bar (Row 2 on small screens) */}
      <div className="w-full md:hidden pt-1">
        <GlobalSearchEntry />
      </div>
    </header>
  );
}
export default Topbar;
