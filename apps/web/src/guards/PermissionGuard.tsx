import React from 'react';
import { useAuth } from '../features/auth/auth-provider';

const ROLE_PERMISSIONS: Record<string, string[]> = {
  SUPER_ADMIN: [
    'project.read', 'project.create', 'project.update', 'project.delete',
    'chat.read', 'chat.create',
    'document.upload', 'analytics.read', 'admin.manage'
  ],
  ORG_ADMIN: [
    'project.read', 'project.create', 'project.update',
    'chat.read', 'chat.create',
    'document.upload', 'analytics.read'
  ],
  PROJECT_MANAGER: [
    'project.read', 'project.create', 'project.update',
    'chat.read', 'chat.create',
    'document.upload'
  ],
  MEMBER: [
    'project.read', 'chat.read', 'chat.create', 'document.upload'
  ],
  GUEST: [
    'project.read', 'chat.read'
  ]
};

interface PermissionGuardProps {
  permission: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export const PermissionGuard: React.FC<PermissionGuardProps> = ({ permission, children, fallback = null }) => {
  const { currentOrg } = useAuth();
  
  if (!currentOrg) return <>{fallback}</>;

  const role = currentOrg.role || 'GUEST';
  const permissions = ROLE_PERMISSIONS[role] || ROLE_PERMISSIONS.GUEST;

  const hasPermission = role === 'SUPER_ADMIN' || permissions.includes(permission);

  if (!hasPermission) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};
