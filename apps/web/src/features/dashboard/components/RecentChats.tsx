import React from 'react';
import { MessageSquare, ArrowRight, Bot, Plus } from 'lucide-react';
import { RecentChat } from '../types';
import { EmptyState } from '../../../shared/components/EmptyState';
import { RecentListSkeleton, WidgetErrorCard } from './Skeletons';

interface RecentChatsProps {
  chats: RecentChat[];
  onNavigateToChat: () => void;
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
}

export function RecentChats({
  chats = [],
  onNavigateToChat,
  loading,
  error,
  onRetry
}: RecentChatsProps) {
  if (error) {
    return <WidgetErrorCard title="Unable to load AI Chats" message={error} onRetry={onRetry} />;
  }

  if (loading) {
    return <RecentListSkeleton title="AI Chats" count={3} />;
  }
  return (
    <div className="glass-panel p-3.5 bg-bgCard border border-borderColor flex flex-col justify-between h-full rounded-2xl">
      <div>
        <div className="flex items-center justify-between mb-2.5 pb-1.5 border-b border-borderMuted">
          <h2 className="text-xs font-semibold text-textPrimary tracking-wide flex items-center gap-2">
            <MessageSquare size={15} className="text-accentText" aria-hidden="true" />
            <span>AI Chats</span>
          </h2>
          <span className="text-[9px] bg-accentSubtle text-accentText px-2 py-0.5 rounded-full font-medium">
            {chats.length > 0 ? 'Active' : 'Idle'}
          </span>
        </div>

        <div className="space-y-1.5 max-h-[300px] overflow-y-auto pr-1">
          {chats.length > 0 ? (
            chats.map((chat) => (
              <div 
                key={chat.id} 
                className="p-2.5 bg-bgTertiary border border-borderMuted hover:border-accent/20 rounded-xl flex items-center justify-between group transition-all"
              >
                <div className="flex items-center gap-2.5">
                  <div className="p-1.5 bg-accentSubtle text-accentText rounded-lg" aria-hidden="true">
                    <Bot size={13} />
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-textPrimary group-hover:text-accentText transition-colors">
                      {chat.name}
                    </p>
                    <span className="text-[9px] text-textMuted font-medium">
                      {chat.status || 'Active'}
                    </span>
                  </div>
                </div>

                <button 
                  type="button"
                  onClick={onNavigateToChat}
                  aria-label={`Resume chat: ${chat.name}`}
                  title="Resume chat"
                  className="p-1 px-2 text-[10px] rounded-lg bg-accentSubtle text-accentText hover:bg-accent hover:text-white border border-accent/20 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
                >
                  Resume
                </button>
              </div>
            ))
          ) : (
            <EmptyState
              title="Ask MindMesh AI"
              description="Use AI to summarize conversations, answer questions, and discover organizational knowledge."
              icon={Bot}
              variant="compact"
              primaryAction={{
                label: "Start AI Assistant",
                onClick: onNavigateToChat,
                icon: Plus
              }}
            />
          )}
        </div>
      </div>

      <button 
        type="button"
        onClick={onNavigateToChat}
        className="mt-2.5 w-full py-1.5 bg-accentSubtle text-accentText hover:bg-accent/20 text-xs font-semibold rounded-xl border border-accent/20 flex items-center justify-center gap-1.5 transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
      >
        <span>Launch Conversation Assistant</span>
        <ArrowRight size={12} aria-hidden="true" />
      </button>
    </div>
  );
}
