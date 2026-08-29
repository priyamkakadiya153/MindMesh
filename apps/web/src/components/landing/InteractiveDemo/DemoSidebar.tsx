import React from 'react';
import {
  LayoutDashboard,
  FileText,
  FolderOpen,
  Bot,
  Search,
  Briefcase,
  Settings,
  ChevronDown,
  Sparkles,
} from 'lucide-react';
import { WorkspaceData } from './DemoDashboardView';

export interface DemoSidebarProps {
  activeTab: string;
  onSelectTab: (tabId: string) => void;
  currentWorkspace: WorkspaceData;
  workspaces: WorkspaceData[];
  onSelectWorkspace: (ws: WorkspaceData) => void;
}

const SIDEBAR_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard className="w-4 h-4" /> },
  { id: 'search', label: 'AI Search', icon: <Search className="w-4 h-4" /> },
  { id: 'chat', label: 'AI Chat Assistant', icon: <Bot className="w-4 h-4" /> },
  { id: 'documents', label: 'Knowledge Docs', icon: <FileText className="w-4 h-4" /> },
  { id: 'files', label: 'Shared Files', icon: <FolderOpen className="w-4 h-4" /> },
  { id: 'workspaces', label: 'Workspaces', icon: <Briefcase className="w-4 h-4" /> },
  { id: 'settings', label: 'Settings', icon: <Settings className="w-4 h-4" /> },
];

export const DemoSidebar: React.FC<DemoSidebarProps> = ({
  activeTab,
  onSelectTab,
  currentWorkspace,
  workspaces,
  onSelectWorkspace,
}) => {
  const [isDropdownOpen, setIsDropdownOpen] = React.useState(false);

  return (
    <aside className="w-full md:w-64 shrink-0 bg-slate-50 dark:bg-slate-950 border-b md:border-b-0 md:border-r border-slate-200 dark:border-slate-800 p-4 space-y-5 text-left">
      {/* Brand Logo Header */}
      <div className="flex items-center gap-2.5 px-2">
        <div className="w-7 h-7 rounded-ds-md bg-indigo-600 text-white flex items-center justify-center font-bold text-xs shadow-ds-soft">
          <Sparkles className="w-4 h-4" />
        </div>
        <span className="font-display font-extrabold text-sm text-slate-900 dark:text-white tracking-tight">
          Mind<span className="text-indigo-600 dark:text-indigo-400">Mesh</span>
        </span>
        <span className="ml-auto text-[9px] font-mono px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-600 dark:text-indigo-300">
          DEMO
        </span>
      </div>

      {/* Workspace Switcher Dropdown */}
      <div className="relative">
        <button
          type="button"
          onClick={() => setIsDropdownOpen(!isDropdownOpen)}
          className="w-full flex items-center justify-between p-2.5 rounded-ds-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 transition-all text-xs"
        >
          <div className="flex flex-col text-left">
            <span className="text-[10px] text-slate-400 dark:text-slate-500 uppercase font-semibold">Active Workspace</span>
            <span className="font-bold text-slate-800 dark:text-slate-200 line-clamp-1">{currentWorkspace.name}</span>
          </div>
          <ChevronDown className="w-4 h-4 text-slate-400" />
        </button>

        {isDropdownOpen && (
          <div className="absolute top-full left-0 right-0 mt-1 z-30 p-1 rounded-ds-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-ds-modal space-y-1">
            {workspaces.map((ws) => (
              <button
                key={ws.name}
                type="button"
                onClick={() => {
                  onSelectWorkspace(ws);
                  setIsDropdownOpen(false);
                }}
                className={`w-full text-left px-3 py-2 rounded-ds-md text-xs font-medium transition-colors ${
                  currentWorkspace.name === ws.name
                    ? 'bg-indigo-600 text-white font-bold'
                    : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
                }`}
              >
                {ws.name}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Navigation Items */}
      <nav className="space-y-1">
        {SIDEBAR_ITEMS.map((item) => {
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-ds-md text-xs font-semibold transition-all ${
                isActive
                  ? 'bg-indigo-600 text-white shadow-ds-soft'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200/60 dark:hover:bg-slate-900'
              }`}
            >
              {item.icon}
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>
    </aside>

  );
};
