import { create } from 'zustand';
import * as api from './api';

export interface ProjectSettings {
  id: string;
  project_id: string;
  allow_external_sharing: boolean;
  default_view: string;
  enable_ai: boolean;
  notification_level: string;
}

export interface Project {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  icon?: string | null;
  color?: string | null;
  status: string;
  visibility: string;
  workspace_id: string;
  organization_id: string;
  owner_id?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
  settings?: ProjectSettings | null;
}

interface ProjectState {
  projects: Project[];
  currentProject: Project | null;
  loading: boolean;
  error: string | null;
  fetchProjects: (token: string, orgId: string, workspaceId?: string, status?: string, search?: string) => Promise<void>;
  selectProject: (project: Project | null) => void;
  createProject: (token: string, orgId: string, projectData: any) => Promise<Project>;
  updateProject: (token: string, orgId: string, id: string, projectData: any) => Promise<Project>;
  archiveProject: (token: string, orgId: string, id: string) => Promise<void>;
  restoreProject: (token: string, orgId: string, id: string) => Promise<void>;
  deleteProject: (token: string, orgId: string, id: string) => Promise<void>;
}

export const useProjectStore = create<ProjectState>((set, get) => ({
  projects: [],
  currentProject: null,
  loading: false,
  error: null,
  fetchProjects: async (token, orgId, workspaceId, status, search) => {
    set({ loading: true, error: null });
    try {
      const projects = await api.getProjects(token, orgId, workspaceId, status, search);
      const savedProjId = localStorage.getItem('mindmesh_current_proj_id');
      set((state) => {
        let active = state.currentProject ? projects.find((p: Project) => p.id === state.currentProject?.id) : null;
        if (!active && savedProjId) {
          active = projects.find((p: Project) => p.id === savedProjId) || null;
        }
        if (!active && projects.length > 0) {
          active = projects[0];
        }
        if (active) {
          localStorage.setItem('mindmesh_current_proj_id', active.id);
        } else {
          localStorage.removeItem('mindmesh_current_proj_id');
        }
        return {
          projects,
          currentProject: active || null,
          loading: false
        };
      });
    } catch (err: any) {
      set({ error: err.message, loading: false });
    }
  },
  selectProject: (project) => {
    set({ currentProject: project });
    if (project) {
      localStorage.setItem('mindmesh_current_proj_id', project.id);
    } else {
      localStorage.removeItem('mindmesh_current_proj_id');
    }
  },
  createProject: async (token, orgId, projectData) => {
    set({ loading: true, error: null });
    try {
      const newProj = await api.createProject(token, orgId, projectData);
      set((state) => ({
        projects: [newProj, ...state.projects],
        currentProject: newProj,
        loading: false
      }));
      if (typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('mindmesh:project-changed'));
      return newProj;
    } catch (err: any) {
      set({ error: err.message, loading: false });
      throw err;
    }
  },
  updateProject: async (token, orgId, id, projectData) => {
    set({ loading: true, error: null });
    try {
      const updated = await api.updateProject(token, orgId, id, projectData);
      set((state) => ({
        projects: state.projects.map((p) => (p.id === id ? updated : p)),
        currentProject: state.currentProject?.id === id ? updated : state.currentProject,
        loading: false
      }));
      if (typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('mindmesh:project-changed'));
      return updated;
    } catch (err: any) {
      set({ error: err.message, loading: false });
      throw err;
    }
  },
  archiveProject: async (token, orgId, id) => {
    set({ loading: true, error: null });
    try {
      const updated = await api.archiveProject(token, orgId, id);
      set((state) => ({
        projects: state.projects.map((p) => (p.id === id ? updated : p)),
        currentProject: state.currentProject?.id === id ? updated : state.currentProject,
        loading: false
      }));
      if (typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('mindmesh:project-changed'));
    } catch (err: any) {
      set({ error: err.message, loading: false });
      throw err;
    }
  },
  restoreProject: async (token, orgId, id) => {
    set({ loading: true, error: null });
    try {
      const updated = await api.restoreProject(token, orgId, id);
      set((state) => ({
        projects: state.projects.map((p) => (p.id === id ? updated : p)),
        currentProject: state.currentProject?.id === id ? updated : state.currentProject,
        loading: false
      }));
      if (typeof window !== 'undefined') window.dispatchEvent(new CustomEvent('mindmesh:project-changed'));
    } catch (err: any) {
      set({ error: err.message, loading: false });
      throw err;
    }
  },
  deleteProject: async (token, orgId, id) => {
    set({ loading: true, error: null });
    try {
      await api.deleteProject(token, orgId, id);
      set((state) => {
        const filtered = state.projects.filter((p) => p.id !== id);
        return {
          projects: filtered,
          currentProject: state.currentProject?.id === id ? filtered[0] || null : state.currentProject,
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
