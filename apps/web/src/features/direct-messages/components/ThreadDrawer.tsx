import React, { useState, useEffect, useRef } from 'react';
import { Message } from '../types';
import { MessageBubble } from './MessageBubble';
import { MessageComposer } from './MessageComposer';
import { getMessageThread, replyToMessage } from '../advanced-api';
import { MessageSquare, X, Loader2 } from 'lucide-react';

interface ThreadDrawerProps {
  parentMessage: Message | null;
  onClose: () => void;
  currentUserId: string;
  token?: string;
}

export const ThreadDrawer: React.FC<ThreadDrawerProps> = ({
  parentMessage,
  onClose,
  currentUserId,
  token
}) => {
  const [replies, setReplies] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const repliesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!parentMessage) return;
    setIsLoading(true);
    getMessageThread(parentMessage.id, token)
      .then(res => setReplies(res))
      .catch(err => console.error('Failed fetching thread replies:', err))
      .finally(() => setIsLoading(false));
  }, [parentMessage, token]);

  useEffect(() => {
    repliesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [replies]);

  if (!parentMessage) return null;

  const handleSendReply = async (content: string) => {
    try {
      const replyMsg = await replyToMessage(parentMessage.id, content, token);
      setReplies(prev => [...prev, replyMsg]);
    } catch (err) {
      console.error('Failed sending thread reply:', err);
    }
  };

  return (
    <div className="w-96 bg-bgSidebar border-l border-borderColor flex flex-col h-full z-40 select-none">
      {/* Header */}
      <div className="p-4 border-b border-borderMuted flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <MessageSquare className="w-5 h-5 text-purple-500" />
          <h3 className="font-semibold text-textPrimary text-sm">Thread Discussion</h3>
        </div>
        <button onClick={onClose} className="p-1 text-textMuted hover:text-textPrimary rounded-lg">
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Main Content Stream */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Parent Message Header Card */}
        <div className="bg-bgCard border border-borderColor rounded-xl p-3.5 space-y-2">
          <div className="flex items-center justify-between text-xs text-textMuted">
            <span className="font-semibold text-textPrimary">{parentMessage.sender_name || 'User'}</span>
            <span>{new Date(parentMessage.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
          </div>
          <p className="text-xs text-textPrimary leading-relaxed">{parentMessage.content}</p>
        </div>

        <div className="flex items-center space-x-2 my-2">
          <div className="flex-1 h-px bg-borderMuted" />
          <span className="text-[10px] font-bold text-textMuted uppercase tracking-wider">
            {replies.length} {replies.length === 1 ? 'Reply' : 'Replies'}
          </span>
          <div className="flex-1 h-px bg-borderMuted" />
        </div>

        {/* Thread Replies List */}
        {isLoading ? (
          <div className="flex items-center justify-center py-8 text-xs text-textMuted">
            <Loader2 className="w-4 h-4 animate-spin mr-2 text-accentText" />
            Loading thread...
          </div>
        ) : (
          replies.map(msg => (
            <MessageBubble
              key={msg.id}
              message={msg}
              currentUserId={currentUserId}
            />
          ))
        )}
        <div ref={repliesEndRef} />
      </div>

      {/* Thread Message Composer */}
      <MessageComposer
        onSendMessage={handleSendReply}
        placeholder="Reply in thread..."
      />
    </div>
  );
};
