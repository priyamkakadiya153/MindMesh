import { create } from 'zustand';
import * as api from './api';
import { useAuthStore } from '../auth/auth-store';

export interface Workspace {
  id: string;
  name: string;
  slug: string;
  organization_id: string;
  created_at: string;
  updated_at?: string;
  status?: string;
  projects_count?: number;
  documents_count?: number;
  members_count?: number;
  storage_used?: number;
}

interface WorkspaceState {
  workspaces: Workspace[];
  currentWorkspace: Workspace | null;
  loading: boolean;
  error: string | null;
  fetchWorkspaces: (token: string, orgId: string) => Promise<void>;
  selectWorkspace: (ws: Workspace) => Promise<void>;
  createWorkspace: (token: string, orgId: string, name: string, slug: string) => Promise<Workspace>;
  updateWorkspace: (token: string, orgId: string, id: string, name: string, slug: string) => Promise<void>;
  deleteWorkspace: (token: string, orgId: string, id: string) => Promise<void>;
}

export const useWorkspaceStore = create<WorkspaceState>((set, get) => ({
  workspaces: [],
  currentWorkspace: null,
  loading: false,
  error: null,
  fetchWorkspaces: async (token, orgId) => {
    set({ loading: true, error: null });
    try {
      const workspaces = await api.getWorkspaces(token, orgId);
      set({ workspaces, loading: false });
      
      const user = useAuthStore.getState().user;
      const savedWsId = localStorage.getItem('mindmesh_current_ws_id');
      const preferred = (savedWsId && workspaces.find((w: Workspace) => w.id === savedWsId)) ||
        (user?.current_workspace_id ? workspaces.find((w: Workspace) => w.id === user.current_workspace_id) : null) ||
        null;
        
      if (preferred) {
        set({ currentWorkspace: preferred });
        localStorage.setItem('mindmesh_current_ws_id', preferred.id);
      } else if (workspaces.length > 0) {
        set({ currentWorkspace: workspaces[0] });
        localStorage.setItem('mindmesh_current_ws_id', workspaces[0].id);
      } else {
        set({ currentWorkspace: null });
        localStorage.removeItem('mindmesh_current_ws_id');
      }
    } catch (err: any) {
      set({ error: err.message, loading: false });
    }
  },
  selectWorkspace: async (ws) => {
    set({ currentWorkspace: ws });
    if (ws) {
      localStorage.setItem('mindmesh_current_ws_id', ws.id);
    } else {
      localStorage.removeItem('mindmesh_current_ws_id');
    }
    const token = useAuthStore.getState().token;
    if (token && ws) {
      try {
        const authApi = await import('../auth/api');
        await authApi.updateCurrentWorkspace(token, ws.id);
        
        const user = await authApi.getCurrentUser(token);
        useAuthStore.getState().setSession(token, useAuthStore.getState().refreshToken || '', user);
      } catch (err) {
        console.error("Failed to save workspace selection on backend:", err);
      }
    }
    if (typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('mindmesh:workspace-changed'));
  },

  createWorkspace: async (token, orgId, name, slug) => {
    set({ loading: true, error: null });
    try {
      const newWs = await api.createWorkspace(token, orgId, name, slug);
      set((state) => ({
        workspaces: [...state.workspaces, newWs],
        currentWorkspace: state.currentWorkspace || newWs,
        loading: false
      }));
      if (typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('mindmesh:workspace-changed'));
      return newWs;
    } catch (err: any) {
      set({ error: err.message, loading: false });
      throw err;
    }
  },
  updateWorkspace: async (token, orgId, id, name, slug) => {
    set({ loading: true, error: null });
    try {
      const updated = await api.updateWorkspace(token, orgId, id, name, slug);
      set((state) => ({
        workspaces: state.workspaces.map((w) => (w.id === id ? updated : w)),
        currentWorkspace: state.currentWorkspace?.id === id ? updated : state.currentWorkspace,
        loading: false
      }));
      if (typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('mindmesh:workspace-changed'));
    } catch (err: any) {
      set({ error: err.message, loading: false });
      throw err;
    }
  },
  deleteWorkspace: async (token, orgId, id) => {
    set({ loading: true, error: null });
    try {
      await api.deleteWorkspace(token, orgId, id);
      set((state) => {
        const remaining = state.workspaces.filter((w) => w.id !== id);
        return {
          workspaces: remaining,
          currentWorkspace: state.currentWorkspace?.id === id ? (remaining[0] || null) : state.currentWorkspace,
          loading: false
        };
      });
      if (typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('mindmesh:data-changed'));
    } catch (err: any) {
      set({ error: err.message, loading: false });
      throw err;
    }
  }
}));
