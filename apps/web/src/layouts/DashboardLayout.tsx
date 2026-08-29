import React from 'react';

interface DashboardLayoutProps {
  sidebar: React.ReactNode;
  children: React.ReactNode;
  theme: string;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({ sidebar, children }) => {
  return (
    <div className="h-screen max-h-screen flex bg-bgPrimary text-textPrimary transition-colors duration-300 font-sans overflow-hidden relative">
      <a 
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:px-4 focus:py-2 focus:bg-accent focus:text-white focus:rounded-xl focus:font-semibold focus:shadow-lg focus:outline-none"
      >
        Skip to main content
      </a>
      {sidebar}
      <div className="flex-1 flex flex-col min-w-0 w-full h-full min-h-0 overflow-hidden">
        <main id="main-content" className="flex-1 flex flex-col min-w-0 w-full max-w-[1920px] mx-auto p-2.5 xs:p-3 sm:p-4 lg:px-6 lg:py-4 h-full min-h-0 overflow-y-auto" tabIndex={-1}>
          {children}
        </main>
      </div>
    </div>
  );
};
