export type PresenceStatus = 'online' | 'away' | 'busy' | 'offline';
export type MessageStatus = 'sending' | 'sent' | 'delivered' | 'read' | 'failed';

export interface Participant {
  id: string;
  full_name: string;
  email: string;
  avatar_url?: string | null;
  status: PresenceStatus;
  last_seen?: string | null;
}

export interface MessageSummary {
  id: string;
  sender_id: string;
  content: string;
  status: MessageStatus;
  created_at: string;
  edited: boolean;
  deleted: boolean;
}

export interface Conversation {
  id: string;
  organization_id: string;
  workspace_id?: string | null;
  type: string; // 'private' | 'group' | 'project_channel'
  name?: string;
  description?: string;
  visibility?: string;
  members?: any[];
  member_count?: number;
  is_pinned?: boolean;
  is_archived?: boolean;
  participant: Participant;
  last_message?: MessageSummary | null;
  last_message_at?: string | null;
  unread_count: number;
  created_at: string;
}

export interface AttachmentItem {
  id: string;
  original_filename: string;
  storage_filename?: string;
  mime_type: string;
  file_size: number;
  preview_url: string;
  download_url: string;
  uploader_name?: string;
  created_at?: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  sender_id: string;
  sender_name?: string;
  sender: {
    id: string;
    full_name: string;
    email: string;
    avatar_url?: string | null;
  };
  message_type: string; // 'text'
  content: string;
  reply_to_id?: string | null;
  client_msg_id?: string | null;
  status: MessageStatus;
  edited: boolean;
  deleted: boolean;
  attachments?: AttachmentItem[];
  created_at: string;
  updated_at: string;
}

export interface WSEventPayload {
  event: string;
  conversation_id?: string;
  group_id?: string;
  message?: Message;
  user_id?: string;
  user_name?: string;
  is_typing?: boolean;
  status?: PresenceStatus;
  read_by_user_id?: string;
}
