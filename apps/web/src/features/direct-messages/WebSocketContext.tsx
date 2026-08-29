import React, { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react';
import { useAuth } from '../auth/auth-provider';
import { getOfflineQueue, removeOfflineMessage, QueuedMessage } from './offlineQueue';
import * as dmApi from './api';

export type ConnectionState = 'connected' | 'connecting' | 'disconnected' | 'reconnecting';

type EventCallback = (data: any) => void;

interface WebSocketContextType {
  connectionState: ConnectionState;
  sendEvent: (event: string, payload: Record<string, any>) => void;
  subscribe: (event: string, callback: EventCallback) => () => void;
  queuedCount: number;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { token, currentOrg } = useAuth();
  const [connectionState, setConnectionState] = useState<ConnectionState>('disconnected');
  const [queuedCount, setQueuedCount] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);
  const listenersRef = useRef<Map<string, Set<EventCallback>>>(new Map());
  const reconnectAttemptRef = useRef(0);
  const heartbeatTimerRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);

  const subscribe = useCallback((event: string, callback: EventCallback) => {
    if (!listenersRef.current.has(event)) {
      listenersRef.current.set(event, new Set());
    }
    listenersRef.current.get(event)!.add(callback);

    return () => {
      const set = listenersRef.current.get(event);
      if (set) {
        set.delete(callback);
        if (set.size === 0) listenersRef.current.delete(event);
      }
    };
  }, []);

  const sendEvent = useCallback((event: string, payload: Record<string, any>) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ event, ...payload }));
    }
  }, []);

  // Flush pending offline queue
  const flushOfflineQueue = useCallback(async () => {
    const queue = getOfflineQueue();
    setQueuedCount(queue.length);
    if (queue.length === 0 || !token) return;

    for (const msg of queue) {
      try {
        await dmApi.sendMessage(msg.conversationId, msg.content, msg.messageType, undefined, token);
        removeOfflineMessage(msg.tempId);
      } catch (err) {
        console.error('Failed flushing queued offline message:', err);
      }
    }
    setQueuedCount(getOfflineQueue().length);
  }, [token]);

  const connect = useCallback(() => {
    if (!token) return;
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    setConnectionState(reconnectAttemptRef.current > 0 ? 'reconnecting' : 'connecting');

    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = window.location.host;
    const wsUrl = `${wsProtocol}//${wsHost}/ws/chat?token=${encodeURIComponent(token)}`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnectionState('connected');
      reconnectAttemptRef.current = 0;

      // Start Heartbeat interval
      if (heartbeatTimerRef.current) clearInterval(heartbeatTimerRef.current);
      heartbeatTimerRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ event: 'ping' }));
        }
      }, 30000);

      // Flush offline messages
      flushOfflineQueue();
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const evtType = data.event;

        if (evtType && listenersRef.current.has(evtType)) {
          listenersRef.current.get(evtType)!.forEach(cb => cb(data));
        }
      } catch (e) {
        console.error('WS JSON decode error:', e);
      }
    };

    ws.onclose = () => {
      setConnectionState('disconnected');
      if (heartbeatTimerRef.current) clearInterval(heartbeatTimerRef.current);

      // Schedule Exponential Backoff Reconnection (1s, 2s, 4s, 8s, max 30s)
      const delay = Math.min(1000 * Math.pow(2, reconnectAttemptRef.current), 30000);
      reconnectAttemptRef.current += 1;

      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = setTimeout(() => {
        connect();
      }, delay);
    };

    ws.onerror = (err) => {
      console.error('WebSocket Error:', err);
    };
  }, [token, flushOfflineQueue]);

  useEffect(() => {
    if (token) {
      connect();
    } else {
      if (wsRef.current) wsRef.current.close();
    }

    return () => {
      if (heartbeatTimerRef.current) clearInterval(heartbeatTimerRef.current);
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [token, connect]);

  return (
    <WebSocketContext.Provider value={{ connectionState, sendEvent, subscribe, queuedCount }}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = () => {
  const ctx = useContext(WebSocketContext);
  if (!ctx) throw new Error('useWebSocket must be used within WebSocketProvider');
  return ctx;
};
