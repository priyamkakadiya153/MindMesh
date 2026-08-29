import { useState, useEffect, useCallback } from 'react';
import { useWebSocket } from './WebSocketContext';

export interface UserPresenceState {
  status: 'online' | 'away' | 'busy' | 'offline';
  custom_status?: string | null;
  last_seen?: string;
}

export function usePresence() {
  const { sendEvent, subscribe } = useWebSocket();
  const [presence, setPresence] = useState<UserPresenceState>({ status: 'online' });

  useEffect(() => {
    const unsub = subscribe('presence_updated', (data) => {
      if (data.presence) {
        setPresence({
          status: data.presence.status,
          custom_status: data.presence.custom_status,
          last_seen: data.presence.last_seen
        });
      }
    });
    return unsub;
  }, [subscribe]);

  const updateStatus = useCallback((status: 'online' | 'away' | 'busy' | 'offline', customStatus?: string) => {
    sendEvent('update_status', { status, custom_status: customStatus });
    setPresence({ status, custom_status: customStatus });
  }, [sendEvent]);

  return {
    presence,
    updateStatus
  };
}
