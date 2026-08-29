import React from 'react';
import { useAuth } from '../features/auth/auth-provider';

export const OrganizationGuard: React.FC<{ children: React.ReactNode; fallback?: React.ReactNode }> = ({ children, fallback = null }) => {
  const { currentOrg } = useAuth();
  
  if (!currentOrg) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};
