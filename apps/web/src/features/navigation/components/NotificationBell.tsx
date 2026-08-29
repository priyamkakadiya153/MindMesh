import React from 'react';
import { Bell } from 'lucide-react';

interface NotificationBellProps {
  hasUnread?: boolean;
  unreadCount?: number;
  onClick: () => void;
}

export function NotificationBell({ hasUnread, unreadCount = 0, onClick }: NotificationBellProps) {
  const count = unreadCount || (hasUnread ? 1 : 0);
  
  return (
    <button 
      type="button"
      onClick={onClick}
      aria-label={count > 0 ? `Notifications (${count} unread)` : 'Notifications'}
      title="Open notifications drawer"
      className="relative flex items-center justify-center h-11 w-11 sm:h-10 sm:w-10 md:h-9 md:w-9 rounded-xl bg-bgCard hover:bg-bgHover border border-borderColor text-textSecondary hover:text-textPrimary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent transition-all duration-150 active:scale-95 shrink-0"
    >
      <Bell size={18} className="sm:w-4 sm:h-4" aria-hidden="true" />
      {count > 0 && (
        <span 
          aria-live="polite" 
          aria-atomic="true"
          className="absolute -top-1 -right-1 flex items-center justify-center min-w-[18px] h-[18px] px-1 text-[10px] font-bold text-white bg-accent border-2 border-bgSidebar rounded-full shadow-sm animate-pulse"
        >
          {count > 99 ? '99+' : count}
        </span>
      )}
    </button>
  );
}
export default NotificationBell;
