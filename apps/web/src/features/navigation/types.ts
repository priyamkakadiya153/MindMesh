export interface NavigationItem {
  id: string;
  label: string;
  permission: string;
  icon?: string;
}

export interface CommandItemType {
  id: string;
  label: string;
  category: 'navigation' | 'create' | 'search' | 'system';
  action: () => void;
  shortcut?: string;
}

export type ThemeType = 'light' | 'dark' | 'system';
