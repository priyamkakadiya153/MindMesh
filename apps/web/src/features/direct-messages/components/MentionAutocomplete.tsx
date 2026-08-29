import React from 'react';
import { AtSign } from 'lucide-react';

export interface MentionUser {
  id: string;
  user_id: string;
  user?: {
    id: string;
    email: string;
    first_name?: string;
    last_name?: string;
  };
}

interface MentionAutocompleteProps {
  users: MentionUser[];
  filterText: string;
  onSelectUser: (name: string) => void;
}

export const MentionAutocomplete: React.FC<MentionAutocompleteProps> = ({
  users,
  filterText,
  onSelectUser
}) => {
  const filtered = users.filter(m => {
    const name = m.user?.first_name ? `${m.user.first_name} ${m.user.last_name || ''}` : m.user?.email || '';
    return name.toLowerCase().includes(filterText.toLowerCase());
  });

  if (filtered.length === 0) return null;

  return (
    <div className="absolute bottom-full mb-2 left-0 w-64 bg-bgDialog border border-borderColor rounded-xl p-1.5 shadow-2xl z-50 select-none max-h-48 overflow-y-auto space-y-1">
      <div className="text-[10px] font-bold text-textMuted uppercase tracking-wider px-2 py-1 flex items-center space-x-1">
        <AtSign className="w-3 h-3 text-accentText" />
        <span>Mention Member</span>
      </div>
      {filtered.map(m => {
        const fullName = m.user?.first_name ? `${m.user.first_name} ${m.user.last_name || ''}` : m.user?.email || 'User';
        return (
          <button
            key={m.id}
            onClick={() => onSelectUser(fullName)}
            className="w-full flex items-center space-x-2.5 p-2 rounded-lg hover:bg-bgHover text-left transition-colors"
          >
            <div className="w-6 h-6 rounded-full bg-accentSubtle text-accentText font-semibold text-[10px] flex items-center justify-center border border-accent/30">
              {fullName.charAt(0).toUpperCase()}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-medium text-textPrimary truncate">{fullName}</p>
              <p className="text-[9px] text-textMuted truncate">{m.user?.email}</p>
            </div>
          </button>
        );
      })}
    </div>
  );
};
