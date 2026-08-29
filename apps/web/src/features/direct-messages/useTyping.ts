import { useState, useEffect, useRef, useCallback } from 'react';
import { useWebSocket } from './WebSocketContext';

interface TypingUser {
  user_id: string;
  user_name: string;
}

export function useTyping(conversationId: string | null) {
  const { sendEvent, subscribe } = useWebSocket();
  const [typingUsers, setTypingUsers] = useState<TypingUser[]>([]);
  const isTypingRef = useRef(false);
  const stopTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!conversationId) return;

    const unsub = subscribe('user_typing', (data) => {
      if (data.conversation_id === conversationId) {
        if (Array.isArray(data.typing_users)) {
          setTypingUsers(data.typing_users);
        } else if (data.is_typing) {
          setTypingUsers(prev => {
            if (prev.some(u => u.user_id === data.user_id)) return prev;
            return [...prev, { user_id: data.user_id, user_name: data.user_name || 'Someone' }];
          });
        } else {
          setTypingUsers(prev => prev.filter(u => u.user_id !== data.user_id));
        }
      }
    });

    return () => {
      unsub();
      setTypingUsers([]);
    };
  }, [conversationId, subscribe]);

  const notifyTyping = useCallback(() => {
    if (!conversationId) return;

    if (!isTypingRef.current) {
      isTypingRef.current = true;
      sendEvent('typing_start', { conversation_id: conversationId });
    }

    if (stopTimeoutRef.current) clearTimeout(stopTimeoutRef.current);

    stopTimeoutRef.current = setTimeout(() => {
      isTypingRef.current = false;
      sendEvent('typing_stop', { conversation_id: conversationId });
    }, 3000);
  }, [conversationId, sendEvent]);

  const stopTypingNow = useCallback(() => {
    if (!conversationId || !isTypingRef.current) return;
    if (stopTimeoutRef.current) clearTimeout(stopTimeoutRef.current);
    isTypingRef.current = false;
    sendEvent('typing_stop', { conversation_id: conversationId });
  }, [conversationId, sendEvent]);

  return {
    typingUsers,
    notifyTyping,
    stopTypingNow
  };
}
