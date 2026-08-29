import React from 'react';
import { AuthProvider } from '../features/auth/auth-provider';
import { NavigationProvider } from '../navigation/NavigationProvider';
import { ThemeProvider } from '../design-system/theme/ThemeProvider';

export const RootLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <ThemeProvider>
      <AuthProvider>
        <NavigationProvider>
          {children}
        </NavigationProvider>
      </AuthProvider>
    </ThemeProvider>
  );
};

