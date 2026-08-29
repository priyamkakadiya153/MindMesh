import React from 'react';
import { useAuth } from '../../features/auth/auth-provider';

interface ProtectedRouteProps {
  children: React.ReactNode;
  fallback: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, fallback }) => {
  const { isAuthenticated } = useAuth();
  
  if (!isAuthenticated) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};
