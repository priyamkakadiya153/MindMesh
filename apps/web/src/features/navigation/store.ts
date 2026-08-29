import { create } from 'zustand';
import { ThemeType } from './types';

interface NavigationState {
  collapsed: boolean;
  mobileOpen: boolean;
  activeTab: string;
  theme: ThemeType;
  commandPaletteOpen: boolean;
  globalSearchQuery: string;
  history: string[];
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setMobileOpen: (open: boolean) => void;
  toggleMobileOpen: () => void;
  setActiveTab: (tab: string) => void;
  setTheme: (theme: ThemeType) => void;
  setCommandPaletteOpen: (open: boolean) => void;
  setGlobalSearchQuery: (query: string) => void;
  pushHistory: (path: string) => void;
}

const getInitialTheme = (): ThemeType => {
  if (typeof window !== 'undefined') {
    const saved = localStorage.getItem('mindmesh_theme') as ThemeType;
    if (saved && (saved === 'light' || saved === 'dark' || saved === 'system')) {
      return saved;
    }
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  return 'dark';
};

const getInitialCollapsed = (): boolean => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('mindmesh_sidebar_collapsed') === 'true';
  }
  return false;
};

export const useNavigationStore = create<NavigationState>((set) => ({
  collapsed: getInitialCollapsed(),
  mobileOpen: false,
  activeTab: 'dashboard',
  theme: getInitialTheme(),
  commandPaletteOpen: false,
  globalSearchQuery: '',
  history: ['dashboard'],
  toggleSidebar: () => set((state) => {
    const next = !state.collapsed;
    localStorage.setItem('mindmesh_sidebar_collapsed', String(next));
    return { collapsed: next };
  }),
  setSidebarCollapsed: (collapsed) => {
    localStorage.setItem('mindmesh_sidebar_collapsed', String(collapsed));
    set({ collapsed });
  },
  setMobileOpen: (open) => set({ mobileOpen: open }),
  toggleMobileOpen: () => set((state) => ({ mobileOpen: !state.mobileOpen })),
  setActiveTab: (tab) => set((state) => ({ 
    activeTab: tab,
    mobileOpen: false,
    history: [...state.history.filter(h => h !== tab), tab]
  })),
  setTheme: (theme) => {
    set({ theme });
    localStorage.setItem('mindmesh_theme', theme);

    const docEl = document.documentElement;
    let effectiveTheme = theme;
    if (theme === 'system') {
      effectiveTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    if (effectiveTheme === 'dark') {
      docEl.classList.add('dark');
      docEl.classList.remove('light');
      docEl.style.colorScheme = 'dark';
    } else {
      docEl.classList.remove('dark');
      docEl.classList.add('light');
      docEl.style.colorScheme = 'light';
    }

    // Asynchronously sync theme to backend profile if user is authenticated
    const token = localStorage.getItem('mindmesh_token') || localStorage.getItem('token');
    if (token) {
      import('../auth/api').then((authApi) => {
        authApi.updateUserProfile(token, { theme }).catch(() => {});
      }).catch(() => {});
    }
  },
  setCommandPaletteOpen: (open) => set({ commandPaletteOpen: open }),
  setGlobalSearchQuery: (query) => set({ globalSearchQuery: query }),
  pushHistory: (path) => set((state) => ({ 
    history: [...state.history.filter(h => h !== path), path] 
  }))
}));
