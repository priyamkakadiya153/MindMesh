import React from 'react';
import { useAuth } from '../features/auth/auth-provider';

interface RoleGuardProps {
  roles: string[];
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export const RoleGuard: React.FC<RoleGuardProps> = ({ roles, children, fallback = null }) => {
  const { currentOrg } = useAuth();
  
  if (!currentOrg) return <>{fallback}</>;

  const hasRole = roles.includes(currentOrg.role);

  if (!hasRole) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};
