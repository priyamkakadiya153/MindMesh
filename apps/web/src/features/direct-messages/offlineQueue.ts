export interface QueuedMessage {
  tempId: string;
  conversationId: string;
  content: string;
  messageType: string;
  createdAt: string;
}

const STORAGE_KEY = 'mindmesh_offline_message_queue';

export function getOfflineQueue(): QueuedMessage[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (e) {
    return [];
  }
}

export function enqueueOfflineMessage(msg: Omit<QueuedMessage, 'tempId' | 'createdAt'>): QueuedMessage {
  const queue = getOfflineQueue();
  const queuedItem: QueuedMessage = {
    ...msg,
    tempId: `offline_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    createdAt: new Date().toISOString()
  };
  queue.push(queuedItem);
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(queue));
  } catch (e) {
    console.error('Failed to save offline queue:', e);
  }
  return queuedItem;
}

export function removeOfflineMessage(tempId: string) {
  const queue = getOfflineQueue().filter(item => item.tempId !== tempId);
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(queue));
  } catch (e) {
    console.error('Failed to update offline queue:', e);
  }
}

export function clearOfflineQueue() {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch (e) {}
}
