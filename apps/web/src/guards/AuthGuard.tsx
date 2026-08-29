import React from 'react';
import { useAuth } from '../features/auth/auth-provider';

export const AuthGuard: React.FC<{ children: React.ReactNode; fallback?: React.ReactNode }> = ({ children, fallback }) => {
  const { isAuthenticated } = useAuth();
  
  if (!isAuthenticated) {
    return fallback ? <>{fallback}</> : null;
  }
  return <>{children}</>;
};
