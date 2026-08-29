import { create } from 'zustand';
import * as api from './api';

export interface MemberDirectoryItem {
  user_id: string;
  username: string;
  email: string;
  avatar_url?: string | null;
  status: string;
  last_login_at?: string | null;
  joined_at?: string | null;
  org_role?: string | null;
  workspace_role?: string | null;
  project_role?: string | null;
}

export interface InvitationItem {
  id: string;
  organization_id: string;
  workspace_id?: string | null;
  project_id?: string | null;
  email: string;
  role: string;
  token: string;
  status: string;
  expires_at: string;
  org_name?: string | null;
  workspace_name?: string | null;
  project_name?: string | null;
}

export interface JoinRequestItem {
  id: string;
  organization_id: string;
  workspace_id?: string | null;
  project_id?: string | null;
  user_id: string;
  username?: string | null;
  email?: string | null;
  message?: string | null;
  status: string;
  created_at: string;
}

interface MemberState {
  members: MemberDirectoryItem[];
  invitations: InvitationItem[];
  joinRequests: JoinRequestItem[];
  permissionMatrix: any[];
  loading: boolean;
  error: string | null;
  fetchDirectory: (token: string, orgId: string, workspaceId?: string, projectId?: string, search?: string, role?: string) => Promise<void>;
  fetchInvitations: (token: string, orgId: string) => Promise<void>;
  fetchJoinRequests: (token: string, orgId: string) => Promise<void>;
  fetchPermissionMatrix: (token: string, orgId: string) => Promise<void>;
  issueInvitation: (token: string, orgId: string, payload: any) => Promise<void>;
  cancelInvitation: (token: string, orgId: string, inviteId: string) => Promise<void>;
  approveJoinRequest: (token: string, orgId: string, requestId: string) => Promise<void>;
  rejectJoinRequest: (token: string, orgId: string, requestId: string) => Promise<void>;
  updateMemberAction: (token: string, orgId: string, userId: string, payload: any) => Promise<void>;
  removeMember: (token: string, orgId: string, userId: string, level?: string, workspaceId?: string, projectId?: string) => Promise<void>;
}

export const useMemberStore = create<MemberState>((set, get) => ({
  members: [],
  invitations: [],
  joinRequests: [],
  permissionMatrix: [],
  loading: false,
  error: null,
  fetchDirectory: async (token, orgId, workspaceId, projectId, search, role) => {
    set({ loading: true, error: null });
    try {
      const members = await api.getMembersDirectory(token, orgId, workspaceId, projectId, search, role);
      set({ members, loading: false });
    } catch (err: any) {
      set({ error: err.message, loading: false });
    }
  },
  fetchInvitations: async (token, orgId) => {
    try {
      const invitations = await api.getPendingInvitations(token, orgId);
      set({ invitations });
    } catch (err: any) {
      set({ error: err.message });
    }
  },
  fetchJoinRequests: async (token, orgId) => {
    try {
      const joinRequests = await api.getJoinRequests(token, orgId);
      set({ joinRequests });
    } catch (err: any) {
      set({ error: err.message });
    }
  },
  fetchPermissionMatrix: async (token, orgId) => {
    try {
      const permissionMatrix = await api.getPermissionMatrix(token, orgId);
      set({ permissionMatrix });
    } catch (err: any) {
      set({ error: err.message });
    }
  },
  issueInvitation: async (token, orgId, payload) => {
    await api.issueInvitation(token, orgId, payload);
    await get().fetchInvitations(token, orgId);
  },
  cancelInvitation: async (token, orgId, inviteId) => {
    await api.cancelInvitation(token, orgId, inviteId);
    await get().fetchInvitations(token, orgId);
  },
  approveJoinRequest: async (token, orgId, requestId) => {
    await api.approveJoinRequest(token, orgId, requestId);
    await get().fetchJoinRequests(token, orgId);
    await get().fetchDirectory(token, orgId);
  },
  rejectJoinRequest: async (token, orgId, requestId) => {
    await api.rejectJoinRequest(token, orgId, requestId);
    await get().fetchJoinRequests(token, orgId);
  },
  updateMemberAction: async (token, orgId, userId, payload) => {
    await api.updateMemberAction(token, orgId, userId, payload);
    await get().fetchDirectory(token, orgId);
  },
  removeMember: async (token, orgId, userId, level, workspaceId, projectId) => {
    await api.removeMember(token, orgId, userId, level, workspaceId, projectId);
    await get().fetchDirectory(token, orgId, workspaceId, projectId);
  }
}));
