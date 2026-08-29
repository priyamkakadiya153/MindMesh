import React from 'react';
import { useAuth } from '../../auth/auth-provider';
import { useNavigation } from './NavigationProvider';
import { useNavigationStore } from '../store';
import { SidebarItem } from './SidebarItem';
import { SidebarSection } from './SidebarSection';
import { SidebarFooter } from './SidebarFooter';
import { SidebarCollapse } from './SidebarCollapse';
import {
  LayoutDashboard,
  Briefcase,
  FolderOpen,
  Search,
  MessageSquare,
  Bot,
  Settings,
  Building,
  Grid,
  HardDrive,
  GitGraph,
  Zap,
  Inbox
} from 'lucide-react';

import { fetchPendingSuggestionsCount } from '../../proactive-intelligence/proactive-detection-api';

const ICONS: Record<string, any> = {
  dashboard: LayoutDashboard,
  workspaces: Grid,
  projects: Briefcase,
  messages: MessageSquare,
  files: HardDrive,
  documents: FolderOpen,
  search: Search,
  'action-inbox': Zap,
  chat: MessageSquare,
  graph: GitGraph,
  agents: Bot,
  organizations: Building,
  settings: Settings
};

interface SidebarProps {
  activeTab?: string;
  setActiveTab?: (tab: string) => void;
  theme?: string;
  toggleTheme?: () => void;
  backendStatus?: string;
  dbConnected?: boolean | null;
}

export function Sidebar(_props?: SidebarProps) {
  const { logout, token } = useAuth();
  const { getVisibleItems } = useNavigation();
  const { 
    collapsed, 
    mobileOpen,
    setSidebarCollapsed,
    setMobileOpen,
    toggleSidebar, 
    activeTab, 
    setActiveTab, 
    theme, 
    setTheme 
  } = useNavigationStore();

  const [pendingBadge, setPendingBadge] = React.useState<number>(0);

  React.useEffect(() => {
    if (!token) return;
    fetchPendingSuggestionsCount(token).then(setPendingBadge).catch(() => {});
    const interval = setInterval(() => {
      fetchPendingSuggestionsCount(token).then(setPendingBadge).catch(() => {});
    }, 8000);
    return () => clearInterval(interval);
  }, [token]);

  React.useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 768) {
        setSidebarCollapsed(false);
      } else if (window.innerWidth < 1280) {
        setSidebarCollapsed(true);
      } else {
        setSidebarCollapsed(false);
      }
    };
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [setSidebarCollapsed]);

  const visibleItems = getVisibleItems();

  const primaryItems = visibleItems.filter(i => ['dashboard', 'workspaces', 'projects', 'messages', 'files', 'documents'].includes(i.id));
  const aiItems = visibleItems.filter(i => ['search', 'action-inbox', 'chat', 'action-history', 'agents'].includes(i.id));
  const adminItems = visibleItems.filter(i => ['organizations', 'settings'].includes(i.id));

  const renderContent = (isMobileDrawer = false) => {
    const isCollapsed = isMobileDrawer ? false : collapsed;
    return (
      <nav aria-label="Main navigation" className="flex flex-col justify-between h-full min-h-0">
        <div className={`overflow-y-auto no-scrollbar ${isCollapsed ? 'space-y-0.5' : 'space-y-1'}`}>
          {isCollapsed ? (
            <div className="flex items-center justify-center w-full min-h-[44px] py-1 px-1 rounded-xl">
              {!isMobileDrawer && (
                <SidebarCollapse collapsed={isCollapsed} onToggle={toggleSidebar} isMobile={isMobileDrawer} />
              )}
            </div>
          ) : (
            <div className="flex items-center justify-between min-h-[44px] px-1 rounded-xl transition-colors">
              <div className="flex items-center gap-3">
                <div className="h-9 w-9 sm:h-10 sm:w-10 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center shadow-lg shadow-indigo-500/20 shrink-0">
                  <span className="text-white font-bold text-base">M</span>
                </div>
                <div>
                  <span className="title-display block font-bold text-base tracking-tight bg-gradient-to-r from-indigo-500 to-purple-500 bg-clip-text text-transparent">
                    MindMesh
                  </span>
                  <p className="text-[9px] text-textMuted uppercase tracking-widest font-semibold">Cognitive OS</p>
                </div>
              </div>

              {!isMobileDrawer && (
                <SidebarCollapse collapsed={isCollapsed} onToggle={toggleSidebar} isMobile={isMobileDrawer} />
              )}
              {isMobileDrawer && (
                <button 
                  type="button"
                  onClick={() => setMobileOpen(false)}
                  className="p-1.5 rounded-lg hover:bg-bgHover text-textMuted transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
                  aria-label="Close sidebar drawer"
                  title="Close sidebar drawer"
                >
                  ✕
                </button>
              )}
            </div>
          )}

          <div className={isCollapsed ? 'space-y-0.5' : 'space-y-0.5'}>
            {primaryItems.length > 0 && (
              <div className={isCollapsed ? 'space-y-0' : 'space-y-0'}>
                {primaryItems.map(item => {
                  const Icon = ICONS[item.id] || LayoutDashboard;
                  return (
                    <SidebarItem
                      key={item.id}
                      label={item.label}
                      icon={Icon}
                      isActive={activeTab === item.id}
                      collapsed={isCollapsed}
                      onClick={() => setActiveTab(item.id)}
                    />
                  );
                })}
              </div>
            )}

            {aiItems.length > 0 && (
              <SidebarSection title="AI Intelligence" collapsed={isCollapsed}>
                {aiItems.map(item => {
                  const Icon = ICONS[item.id] || LayoutDashboard;
                  return (
                    <SidebarItem
                      key={item.id}
                      label={item.label}
                      icon={Icon}
                      isActive={activeTab === item.id}
                      collapsed={isCollapsed}
                      badge={item.id === 'action-inbox' ? pendingBadge : undefined}
                      onClick={() => setActiveTab(item.id)}
                    />
                  );
                })}
              </SidebarSection>
            )}

            {adminItems.length > 0 && (
              <SidebarSection title="Administration" collapsed={isCollapsed}>
                {adminItems.map(item => {
                  const Icon = ICONS[item.id] || LayoutDashboard;
                  return (
                    <SidebarItem
                      key={item.id}
                      label={item.label}
                      icon={Icon}
                      isActive={activeTab === item.id}
                      collapsed={isCollapsed}
                      onClick={() => setActiveTab(item.id)}
                    />
                  );
                })}
              </SidebarSection>
            )}
          </div>
        </div>

        <div className={`mt-auto shrink-0 ${isCollapsed ? 'pt-0.5' : 'pt-1'}`}>
          <SidebarFooter
            collapsed={isCollapsed}
            theme={theme}
            onToggleTheme={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            onLogout={logout}
          />
        </div>
      </nav>
    );
  };

  return (
    <>
      {/* Mobile Drawer Overlay */}
      {mobileOpen && (
        <div 
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden transition-opacity"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Mobile Sidebar Drawer */}
      <div 
        className={`fixed top-0 bottom-0 left-0 z-50 w-72 bg-bgSidebar border-r border-borderColor p-4 md:hidden transition-transform duration-300 ease-in-out ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {renderContent(true)}
      </div>

      {/* Desktop / Tablet Inline Sidebar */}
      <aside 
        className={`hidden md:flex glass-panel border border-borderColor bg-bgSidebar text-textPrimary flex-col justify-between my-2 sm:my-3 ml-2 sm:ml-3 rounded-2xl transition-all duration-200 ease-in-out shrink-0 shadow-xl z-20 ${
          collapsed ? 'w-16 p-2.5' : 'w-60 xl:w-64 p-3.5 sm:p-4'
        }`}
      >
        {renderContent(false)}
      </aside>
    </>
  );
}
export default Sidebar;
