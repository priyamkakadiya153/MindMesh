import React from 'react';

export interface NavigationLinkProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  href: string;
  active?: boolean;
  children: React.ReactNode;
}

export const NavigationLink: React.FC<NavigationLinkProps> = ({
  href,
  active = false,
  className = '',
  children,
  onClick,
  ...props
}) => {
  return (
    <a
      href={href}
      onClick={onClick}
      className={`
        relative text-sm font-medium transition-colors duration-200 focus-ring py-1 px-2 rounded-ds-sm
        ${
          active
            ? 'text-indigo-600 dark:text-indigo-400 font-semibold'
            : 'text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white'
        }
        ${className}
      `.trim()}
      {...props}
    >
      {children}
      {active && (
        <span className="absolute bottom-0 left-2 right-2 h-0.5 bg-indigo-600 dark:bg-indigo-400 rounded-full" />
      )}
    </a>
  );
};
