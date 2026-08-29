import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useAuth } from '../auth/auth-provider';
import { apiClient } from '../../lib/api-client';
import { ShieldAlert } from 'lucide-react';

interface PermissionContextType {
  permissions: string[];
  loading: boolean;
  hasPermission: (permissionKey: string) => boolean;
  refreshPermissions: () => Promise<void>;
}

const PermissionContext = createContext<PermissionContextType>({
  permissions: [],
  loading: false,
  hasPermission: () => false,
  refreshPermissions: async () => {},
});

export const PermissionProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { token, currentOrg } = useAuth();
  const [permissions, setPermissions] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchPermissions = async () => {
    if (!token || !currentOrg) {
      setPermissions([]);
      return;
    }
    setLoading(true);
    try {
      const response = await apiClient({
        url: 'roles/me/permissions',
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Organization-ID': currentOrg.id,
        },
      });
      const data = response.data;
      setPermissions(data?.permissions || []);
    } catch (err) {
      console.error('Failed to load user permissions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPermissions();
  }, [token, currentOrg]);

  const hasPermission = (permissionKey: string): boolean => {
    if (permissions.includes('*')) return true;
    if (permissions.includes(permissionKey)) return true;

    const category = permissionKey.split('.')[0];
    if (category && permissions.includes(`${category}.*`)) return true;

    return false;
  };

  return (
    <PermissionContext.Provider
      value={{
        permissions,
        loading,
        hasPermission,
        refreshPermissions: fetchPermissions,
      }}
    >
      {children}
    </PermissionContext.Provider>
  );
};

export const usePermission = () => useContext(PermissionContext);

interface RequirePermissionProps {
  permission: string;
  fallback?: ReactNode;
  children: ReactNode;
}

export const RequirePermission: React.FC<RequirePermissionProps> = ({
  permission,
  fallback,
  children,
}) => {
  const { hasPermission, loading } = usePermission();

  if (loading) return null;

  if (!hasPermission(permission)) {
    if (fallback !== undefined) return <>{fallback}</>;
    return (
      <div className="flex items-center gap-2 rounded-xl border border-amber-500/20 bg-amber-500/10 p-3 text-xs text-amber-400">
        <ShieldAlert size={16} />
        <span>You do not have permission (<code>{permission}</code>) to access this feature.</span>
      </div>
    );
  }

  return <>{children}</>;
};
