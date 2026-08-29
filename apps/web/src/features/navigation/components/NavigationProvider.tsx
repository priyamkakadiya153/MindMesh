import React, { createContext, useContext, useState } from 'react';
import { useAuth } from '../../auth/auth-provider';
import { NavigationItem } from '../types';

interface NavigationContextType {
  getNavigation: () => NavigationItem[];
  getVisibleItems: () => NavigationItem[];
  changeOrganization: (orgId: string) => Promise<void>;
  refreshNavigation: () => void;
}

const NavigationContext = createContext<NavigationContextType | undefined>(undefined);

export const NavigationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { currentOrg, switchOrganization, organizations } = useAuth();
  const [, setTick] = useState(0);

  const getNavigation = (): NavigationItem[] => {
    return [
      { id: 'dashboard', label: 'Dashboard', permission: 'project.read' },
      { id: 'workspaces', label: 'Workspaces', permission: 'project.read' },
      { id: 'projects', label: 'Projects', permission: 'project.read' },
      { id: 'messages', label: 'Direct Messages', permission: 'chat.create' },
      { id: 'files', label: 'Shared Files', permission: 'document.upload' },
      { id: 'documents', label: 'Documents', permission: 'document.upload' },

      { id: 'search', label: 'Semantic Search', permission: 'project.read' },
      { id: 'action-inbox', label: 'Action Inbox', permission: 'project.read' },
      { id: 'chat', label: 'AI Chat Intelligence', permission: 'chat.create' },
      { id: 'action-history', label: 'Action History & Memory', permission: 'project.read' },
      { id: 'agents', label: 'Cognitive Agents', permission: 'project.read' },
      { id: 'organizations', label: 'Organizations', permission: 'project.read' },
      { id: 'settings', label: 'Settings', permission: 'project.read' }
    ];
  };

  const getVisibleItems = (): NavigationItem[] => {
    const items = getNavigation();
    if (!currentOrg) return items;
    
    const role = (currentOrg.role || 'OWNER').toUpperCase();
    if (role === 'SUPER_ADMIN' || role === 'ORG_ADMIN' || role === 'OWNER' || role === 'ADMIN' || role === 'MEMBER') {
      return items;
    }
    if (role === 'PROJECT_MANAGER') {
      return items.filter(i => i.id !== 'settings');
    }
    return items;
  };


  const changeOrganization = async (orgId: string) => {
    const org = organizations.find((o) => o.id === orgId);
    if (org) switchOrganization(org);
  };

  const refreshNavigation = () => {
    setTick(t => t + 1);
  };

  return (
    <NavigationContext.Provider value={{ getNavigation, getVisibleItems, changeOrganization, refreshNavigation }}>
      {children}
    </NavigationContext.Provider>
  );
};

export const useNavigation = () => {
  const context = useContext(NavigationContext);
  if (!context) {
    throw new Error('useNavigation must be used within a NavigationProvider');
  }
  return context;
};
export default NavigationProvider;
