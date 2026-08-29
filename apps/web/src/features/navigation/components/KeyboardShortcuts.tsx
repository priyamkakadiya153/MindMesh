import React from 'react';
import { Keyboard } from 'lucide-react';

export function KeyboardShortcuts() {
  const shortcuts = [
    { keys: ['Ctrl', 'K'], label: 'Open Command Palette' },
    { keys: ['Ctrl', '/'], label: 'Focus Global Search' },
    { keys: ['Ctrl', 'D'], label: 'Navigate to Dashboard' },
    { keys: ['Ctrl', 'P'], label: 'Navigate to Projects' },
    { keys: ['Ctrl', 'Shift', 'U'], label: 'Upload Document' }
  ];

  return (
    <div className="glass-panel p-4 bg-bgCard border border-borderColor space-y-3">
      <div className="flex items-center gap-2 text-xs font-semibold text-textPrimary">
        <Keyboard size={14} className="text-accentText" />
        <span>Keyboard Shortcuts</span>
      </div>

      <div className="space-y-2">
        {shortcuts.map((s, idx) => (
          <div key={idx} className="flex justify-between items-center text-[10px]">
            <span className="text-textSecondary">{s.label}</span>
            <div className="flex gap-1">
              {s.keys.map((k, i) => (
                <kbd key={i} className="px-1.5 py-0.5 bg-bgTertiary border border-borderMuted rounded text-textMuted font-semibold font-mono">
                  {k}
                </kbd>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
export default KeyboardShortcuts;
