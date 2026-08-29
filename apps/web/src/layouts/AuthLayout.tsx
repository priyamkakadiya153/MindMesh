import React from 'react';

interface AuthLayoutProps {
  children: React.ReactNode;
  theme: string;
  toggleTheme: () => void;
  sunIcon: React.ReactNode;
  moonIcon: React.ReactNode;
}

export const AuthLayout: React.FC<AuthLayoutProps> = ({
  children,
  theme,
  toggleTheme,
  sunIcon,
  moonIcon
}) => {
  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-bgPrimary text-textPrimary transition-colors duration-300 font-sans relative">
      <div className="absolute top-4 right-4">
        <button
          onClick={toggleTheme}
          className="p-2.5 rounded-xl border border-borderColor bg-bgCard text-accent hover:bg-bgHover transition-all shadow-sm"
          title="Toggle Color Theme"
        >
          {theme === 'dark' ? sunIcon : moonIcon}
        </button>
      </div>
      
      <div className="w-full max-w-md p-8 rounded-2xl shadow-2xl space-y-6 transition-all duration-300 glass-panel bg-bgCard border border-borderColor text-textPrimary">
        <div className="text-center space-y-2">
          <div className="inline-flex h-12 w-12 rounded-2xl bg-gradient-to-tr from-indigo-500 to-purple-500 items-center justify-center shadow-lg shadow-indigo-500/20 mb-2">
            <span className="text-white font-bold text-xl">M</span>
          </div>
          <h1 className="title-display text-2xl font-bold tracking-tight bg-gradient-to-r from-indigo-500 to-purple-500 bg-clip-text text-transparent">MindMesh</h1>
          <p className="text-xs text-textMuted font-medium">Cognitive OS & Organizational Memory</p>
        </div>

        {children}
      </div>
    </div>
  );
};
