import React, { useState, useEffect } from 'react';
import { Search } from 'lucide-react';
import { useNavigationStore } from '../store';
import { CommandItem } from './CommandItem';
import { CommandItemType } from '../types';

interface CommandPaletteProps {
  onNavigate: (tab: string) => void;
}

export function CommandPalette({ onNavigate }: CommandPaletteProps) {
  const { commandPaletteOpen, setCommandPaletteOpen, setActiveTab } = useNavigationStore();
  const [query, setQuery] = useState('');

  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setCommandPaletteOpen(false);
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [setCommandPaletteOpen]);

  if (!commandPaletteOpen) return null;

  const commands: CommandItemType[] = [
    {
      id: 'dashboard',
      label: 'Open Dashboard',
      category: 'navigation',
      shortcut: 'Ctrl + D',
      action: () => {
        setActiveTab('dashboard');
        onNavigate('dashboard');
        setCommandPaletteOpen(false);
      }
    },
    {
      id: 'workspaces',
      label: 'Manage Workspaces',
      category: 'navigation',
      action: () => {
        setActiveTab('workspaces');
        onNavigate('workspaces');
        setCommandPaletteOpen(false);
      }
    },
    {
      id: 'projects',
      label: 'Open Projects & Repositories',
      category: 'navigation',
      shortcut: 'Ctrl + P',
      action: () => {
        setActiveTab('projects');
        onNavigate('projects');
        setCommandPaletteOpen(false);
      }
    },
    {
      id: 'documents',
      label: 'Upload Knowledge Documents',
      category: 'create',
      shortcut: 'Ctrl + Shift + U',
      action: () => {
        setActiveTab('documents');
        onNavigate('documents');
        setCommandPaletteOpen(false);
      }
    },
    {
      id: 'chat',
      label: 'Launch AI Conversation Assistant',
      category: 'navigation',
      action: () => {
        setActiveTab('chat');
        onNavigate('chat');
        setCommandPaletteOpen(false);
      }
    },
    {
      id: 'search',
      label: 'Search Indexed Knowledge Base',
      category: 'search',
      shortcut: 'Ctrl + /',
      action: () => {
        setActiveTab('search');
        onNavigate('search');
        setCommandPaletteOpen(false);
      }
    },
    {
      id: 'settings',
      label: 'Open System Preferences',
      category: 'system',
      action: () => {
        setActiveTab('settings');
        onNavigate('settings');
        setCommandPaletteOpen(false);
      }
    }
  ];

  const filteredCommands = commands.filter((cmd) =>
    cmd.label.toLowerCase().includes(query.toLowerCase()) ||
    cmd.category.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div 
      role="dialog"
      aria-modal="true"
      aria-label="Command Palette"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-bgOverlay backdrop-blur-md animate-in fade-in duration-200"
    >
      <div 
        className="fixed inset-0" 
        onClick={() => setCommandPaletteOpen(false)} 
        aria-hidden="true"
      />
      
      <div className="relative w-full max-w-lg bg-bgDialog border border-borderColor text-textPrimary shadow-2xl p-4 overflow-hidden rounded-3xl animate-in fade-in slide-in-from-bottom-4 duration-300">
        <div className="flex items-center gap-3 px-3 py-2 border-b border-borderColor">
          <Search size={16} className="text-textMuted" aria-hidden="true" />
          <label htmlFor="cmd-palette-input" className="sr-only">Command Search</label>
          <input
            id="cmd-palette-input"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command to search... (Esc to close)"
            aria-label="Type a command to search"
            className="flex-1 bg-transparent border-0 text-sm text-textPrimary focus:outline-none placeholder-textMuted"
            autoFocus
          />
        </div>

        <div role="listbox" aria-label="Available commands" className="mt-3 space-y-1.5 max-h-[300px] overflow-y-auto pr-1">
          {filteredCommands.length > 0 ? (
            filteredCommands.map((cmd) => (
              <CommandItem
                key={cmd.id}
                label={cmd.label}
                category={cmd.category}
                shortcut={cmd.shortcut}
                onClick={cmd.action}
              />
            ))
          ) : (
            <p className="text-center text-xs text-textMuted py-8" role="status">
              No matching command shortcuts found
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
export default CommandPalette;
