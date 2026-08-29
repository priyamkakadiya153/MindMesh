/**
 * Multi-Tab Synchronization Utility for MindMesh Conversations.
 * 
 * Uses BroadcastChannel to sync conversation message events across open browser tabs
 * without duplicating server messages.
 */

export interface ChatSyncEvent {
  type: 'MESSAGE_CREATED' | 'MESSAGE_UPDATED' | 'CONVERSATION_UPDATED';
  conversationId: string;
  messageId?: string;
  senderTabId: string;
  payload?: any;
}

const CHANNEL_NAME = 'mindmesh_chat_sync';
const TAB_ID = Math.random().toString(36).substring(2, 11);

let channel: BroadcastChannel | null = null;
if (typeof window !== 'undefined' && 'BroadcastChannel' in window) {
  channel = new BroadcastChannel(CHANNEL_NAME);
}

export function broadcastChatEvent(evt: Omit<ChatSyncEvent, 'senderTabId'>) {
  if (!channel) return;
  channel.postMessage({
    ...evt,
    senderTabId: TAB_ID
  });
}

export function subscribeToChatSync(callback: (evt: ChatSyncEvent) => void): () => void {
  if (!channel) return () => {};

  const handler = (event: MessageEvent<ChatSyncEvent>) => {
    if (event.data && event.data.senderTabId !== TAB_ID) {
      callback(event.data);
    }
  };

  channel.addEventListener('message', handler);
  return () => {
    channel?.removeEventListener('message', handler);
  };
}
