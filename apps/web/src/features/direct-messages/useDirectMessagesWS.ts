import { useEffect, useRef, useCallback } from 'react';
import { WSEventPayload } from './types';
import { useWebSocket } from './WebSocketContext';

interface UseDirectMessagesWSOptions {
  token: string | null;
  onMessageReceived?: (event: WSEventPayload) => void;
  onTypingStatusChanged?: (event: WSEventPayload) => void;
  onPresenceUpdated?: (event: WSEventPayload) => void;
  onGroupUpdated?: (event: WSEventPayload) => void;
  onProactiveActionDetected?: (event: WSEventPayload) => void;
}

export function useDirectMessagesWS({
  token,
  onMessageReceived,
  onTypingStatusChanged,
  onPresenceUpdated,
  onGroupUpdated,
  onProactiveActionDetected
}: UseDirectMessagesWSOptions) {
  const { connectionState, sendEvent, subscribe } = useWebSocket();

  const callbacksRef = useRef({ onMessageReceived, onTypingStatusChanged, onPresenceUpdated, onGroupUpdated, onProactiveActionDetected });
  useEffect(() => {
    callbacksRef.current = { onMessageReceived, onTypingStatusChanged, onPresenceUpdated, onGroupUpdated, onProactiveActionDetected };
  });

  useEffect(() => {
    if (!token) return;

    // Subscribe to all relevant real-time DM & group events
    const unsubMessage = subscribe('new_message', (payload: WSEventPayload) => {
      callbacksRef.current.onMessageReceived?.(payload);
    });
    const unsubEdit = subscribe('message_edited', (payload: WSEventPayload) => {
      callbacksRef.current.onMessageReceived?.(payload);
    });
    const unsubDelete = subscribe('message_deleted', (payload: WSEventPayload) => {
      callbacksRef.current.onMessageReceived?.(payload);
    });
    const unsubRead = subscribe('messages_read', (payload: WSEventPayload) => {
      callbacksRef.current.onMessageReceived?.(payload);
    });

    const unsubProactive = subscribe('proactive_action_detected', (payload: WSEventPayload) => {
      callbacksRef.current.onProactiveActionDetected?.(payload);
    });

    const unsubTyping = subscribe('user_typing', (payload: WSEventPayload) => {
      callbacksRef.current.onTypingStatusChanged?.(payload);
    });
    const unsubPresence = subscribe('presence_updated', (payload: WSEventPayload) => {
      callbacksRef.current.onPresenceUpdated?.(payload);
    });

    const unsubGroupCreated = subscribe('group_created', (payload: WSEventPayload) => {
      callbacksRef.current.onGroupUpdated?.(payload);
    });
    const unsubGroupAdded = subscribe('group_member_added', (payload: WSEventPayload) => {
      callbacksRef.current.onGroupUpdated?.(payload);
    });
    const unsubGroupRemoved = subscribe('group_member_removed', (payload: WSEventPayload) => {
      callbacksRef.current.onGroupUpdated?.(payload);
    });
    const unsubGroupUpdated = subscribe('group_updated', (payload: WSEventPayload) => {
      callbacksRef.current.onGroupUpdated?.(payload);
    });
    const unsubGroupDeleted = subscribe('group_deleted', (payload: WSEventPayload) => {
      callbacksRef.current.onGroupUpdated?.(payload);
    });
    const unsubGroupDeletedDot = subscribe('group.deleted', (payload: WSEventPayload) => {
      callbacksRef.current.onGroupUpdated?.(payload);
    });
    const unsubConvCreated = subscribe('conversation_created', (payload: WSEventPayload) => {
      callbacksRef.current.onGroupUpdated?.(payload);
    });

    return () => {
      unsubMessage();
      unsubEdit();
      unsubDelete();
      unsubRead();
      unsubProactive();
      unsubTyping();
      unsubPresence();
      unsubGroupCreated();
      unsubGroupAdded();
      unsubGroupRemoved();
      unsubGroupUpdated();
      unsubConvCreated();
    };
  }, [token, subscribe]);

  const sendTypingStart = useCallback((conversationId: string, recipientId: string) => {
    sendEvent('typing_start', {
      conversation_id: conversationId,
      recipient_id: recipientId
    });
  }, [sendEvent]);

  const sendTypingStop = useCallback((conversationId: string, recipientId: string) => {
    sendEvent('typing_stop', {
      conversation_id: conversationId,
      recipient_id: recipientId
    });
  }, [sendEvent]);

  return {
    isConnected: connectionState === 'connected',
    sendTypingStart,
    sendTypingStop
  };
}
