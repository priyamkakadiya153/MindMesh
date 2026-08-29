import React, { useState, useRef } from 'react';
import { Send, Smile, Paperclip, X, Reply, FileText, Image as ImageIcon, Loader2, AlertCircle, Check } from 'lucide-react';
import { Message, AttachmentItem } from '../types';
import { EmojiPicker } from './EmojiPicker';
import { uploadAttachment } from '../api';

interface MessageComposerProps {
  conversationId?: string;
  onSendMessage: (content: string, attachmentIds?: string[]) => Promise<void>;
  onTypingStart?: () => void;
  onTypingStop?: () => void;
  replyingToMessage?: Message | null;
  onCancelReply?: () => void;
  placeholder?: string;
  disabled?: boolean;
}

interface PendingAttachment {
  file: File;
  attachmentItem?: AttachmentItem;
  status: 'uploading' | 'ready' | 'failed';
  error?: string;
}

export const MessageComposer: React.FC<MessageComposerProps> = ({
  conversationId,
  onSendMessage,
  onTypingStart,
  onTypingStop,
  replyingToMessage,
  onCancelReply,
  placeholder = "Send a direct message...",
  disabled = false
}) => {
  const [content, setContent] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [pendingAttachments, setPendingAttachments] = useState<PendingAttachment[]>([]);
  const typingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setContent(e.target.value);
    
    if (onTypingStart) {
      onTypingStart();
      if (typingTimerRef.current) clearTimeout(typingTimerRef.current);
      typingTimerRef.current = setTimeout(() => {
        if (onTypingStop) onTypingStop();
      }, 2500);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0 || !conversationId) return;

    const file = files[0];
    // Reset file input value so same file can be re-selected if needed
    e.target.value = '';

    // Enforce 50 MB client-side validation
    const maxSizeBytes = 50 * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      alert(`File "${file.name}" is too large. Maximum allowed size is 50 MB.`);
      return;
    }

    // Check executable extension
    const filename = file.name || '';
    const ext = filename.split('.').pop()?.toLowerCase() || '';
    const unsafeExts = ['exe', 'bat', 'cmd', 'sh', 'ps1', 'dll', 'scr', 'vbs', 'js', 'jar', 'com', 'msi', 'bin'];
    if (unsafeExts.includes(ext)) {
      alert(`File "${file.name}" is an executable or dangerous file type and cannot be attached.`);
      return;
    }

    const pendingItem: PendingAttachment = {
      file,
      status: 'uploading'
    };

    setPendingAttachments(prev => [...prev, pendingItem]);

    try {
      const uploadedItem = await uploadAttachment(file, conversationId);
      setPendingAttachments(prev => prev.map(item => 
        item.file === file
          ? { ...item, status: 'ready', attachmentItem: uploadedItem }
          : item
      ));
    } catch (err: any) {
      const errMsg = err.message || 'Upload failed';
      setPendingAttachments(prev => prev.map(item => 
        item.file === file
          ? { ...item, status: 'failed', error: errMsg }
          : item
      ));
    }
  };

  const handleRemoveAttachment = (index: number) => {
    setPendingAttachments(prev => prev.filter((_, i) => i !== index));
  };

  const handleRetryUpload = async (index: number) => {
    const item = pendingAttachments[index];
    if (!item || !conversationId) return;

    setPendingAttachments(prev => prev.map((it, i) => 
      i === index ? { ...it, status: 'uploading', error: undefined } : it
    ));

    try {
      const uploadedItem = await uploadAttachment(item.file, conversationId);
      setPendingAttachments(prev => prev.map((it, i) => 
        i === index ? { ...it, status: 'ready', attachmentItem: uploadedItem } : it
      ));
    } catch (err: any) {
      const errMsg = err.message || 'Upload failed';
      setPendingAttachments(prev => prev.map((it, i) => 
        i === index ? { ...it, status: 'failed', error: errMsg } : it
      ));
    }
  };

  const readyAttachmentIds = pendingAttachments
    .filter(a => a.status === 'ready' && a.attachmentItem)
    .map(a => a.attachmentItem!.id);

  const hasUploading = pendingAttachments.some(a => a.status === 'uploading');
  const canSend = (content.trim().length > 0 || readyAttachmentIds.length > 0) && !hasUploading && !isSubmitting && !disabled;

  const handleSubmit = async () => {
    if (!canSend) return;
    setIsSubmitting(true);
    if (typingTimerRef.current) clearTimeout(typingTimerRef.current);
    if (onTypingStop) onTypingStop();

    try {
      await onSendMessage(
        content.trim(),
        readyAttachmentIds.length > 0 ? readyAttachmentIds : undefined
      );
      setContent('');
      setPendingAttachments([]);
      if (onCancelReply) onCancelReply();
    } catch (err) {
      console.error('Failed to send message:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="p-3 bg-bgCard border-t border-borderColor relative select-none">
      {/* Quoted Reply Banner */}
      {replyingToMessage && (
        <div className="mb-2 bg-accentSubtle border-l-4 border-accent rounded-r-xl p-2 flex items-center justify-between text-xs">
          <div className="min-w-0 flex items-center space-x-2">
            <Reply className="w-3.5 h-3.5 text-accentText shrink-0" />
            <div className="min-w-0">
              <span className="font-semibold text-accentText">Replying to {replyingToMessage.sender_name || 'User'}</span>
              <p className="text-textMuted truncate">{replyingToMessage.content}</p>
            </div>
          </div>
          <button onClick={onCancelReply} className="p-1 text-textMuted hover:text-textPrimary">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Pending Attachments Banner */}
      {pendingAttachments.length > 0 && (
        <div className="mb-2.5 flex flex-wrap gap-2">
          {pendingAttachments.map((att, idx) => {
            const isImg = att.file.type.startsWith('image/');
            return (
              <div
                key={idx}
                className="flex items-center space-x-2 p-2 bg-bgInput border border-borderColor rounded-xl text-xs max-w-xs shadow-sm relative group"
              >
                <div className="p-1.5 rounded-lg bg-bgTertiary text-accentText shrink-0">
                  {isImg ? <ImageIcon className="w-4 h-4 text-emerald-400" /> : <FileText className="w-4 h-4 text-accentText" />}
                </div>

                <div className="min-w-0 flex-1">
                  <p className="text-textPrimary font-medium text-[11px] truncate" title={att.file.name}>
                    {att.file.name}
                  </p>
                  <p className="text-[10px] text-textMuted flex items-center space-x-1">
                    <span>{formatSize(att.file.size)}</span>
                    <span>•</span>
                    {att.status === 'uploading' && (
                      <span className="text-amber-400 font-semibold flex items-center gap-1">
                        <Loader2 className="w-3 h-3 animate-spin" /> Uploading...
                      </span>
                    )}
                    {att.status === 'ready' && (
                      <span className="text-emerald-400 font-semibold flex items-center gap-0.5">
                        <Check className="w-3 h-3" /> Ready
                      </span>
                    )}
                    {att.status === 'failed' && (
                      <span className="text-red-400 font-semibold flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" /> Failed
                      </span>
                    )}
                  </p>
                </div>

                {att.status === 'failed' ? (
                  <button
                    type="button"
                    onClick={() => handleRetryUpload(idx)}
                    className="p-1 text-amber-400 hover:text-amber-300 font-bold text-[10px] underline"
                    title="Retry upload"
                  >
                    Retry
                  </button>
                ) : null}

                <button
                  type="button"
                  onClick={() => handleRemoveAttachment(idx)}
                  className="p-1 text-textMuted hover:text-red-400 rounded-lg transition-colors shrink-0"
                  title="Remove attachment"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            );
          })}
        </div>
      )}

      {/* Emoji Picker Popover */}
      {showEmojiPicker && (
        <div className="absolute bottom-full mb-2 left-4 z-50">
          <EmojiPicker
            onSelectEmoji={(emoji) => setContent(prev => prev + emoji)}
            onClose={() => setShowEmojiPicker(false)}
          />
        </div>
      )}

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        onChange={handleFileSelect}
        className="hidden"
        accept=".pdf,.docx,.doc,.txt,.md,.png,.jpg,.jpeg,.gif,.webp,.csv,.json"
      />

      <div className="relative flex items-end bg-bgInput border border-borderColor rounded-xl focus-within:border-accent focus-within:ring-1 focus-within:ring-accent/50 transition-all p-2">
        <textarea
          value={content}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled || isSubmitting}
          rows={1}
          className="w-full bg-transparent text-textPrimary placeholder-textMuted text-sm focus:outline-none resize-none max-h-32 min-h-[36px] py-1.5 px-2"
        />

        <div className="flex items-center space-x-1 pl-2 pb-0.5">
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled || isSubmitting || !conversationId}
            aria-label="Attach file"
            className="p-1.5 text-textMuted hover:text-textPrimary hover:bg-bgHover rounded-lg transition-colors disabled:opacity-50"
            title="Attach file"
          >
            <Paperclip className="w-5 h-5" />
          </button>

          <button
            type="button"
            onClick={() => setShowEmojiPicker(prev => !prev)}
            className="p-1.5 text-textMuted hover:text-textPrimary hover:bg-bgHover rounded-lg transition-colors"
            title="Emoji"
          >
            <Smile className="w-5 h-5" />
          </button>
          
          <button
            type="button"
            onClick={handleSubmit}
            disabled={!canSend}
            className={`p-2 rounded-lg transition-all ${
              canSend
                ? 'bg-accent hover:bg-accentHover text-white shadow-md shadow-accent/20'
                : 'bg-bgTertiary text-textMuted cursor-not-allowed'
            }`}
            title="Send Message"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
