import React, { useState } from 'react';
import { Message, AttachmentItem } from '../types';
import { EmojiPicker } from './EmojiPicker';
import { Check, CheckCheck, Clock, Edit2, Trash2, Copy, AlertCircle, Reply, Smile, Share2, Pin, MessageSquare, FileText, Image as ImageIcon, Download, Eye, Loader2, Scissors, Package, Film, Archive, FileCode } from 'lucide-react';
import { detectFileType } from '../../files/utils/fileCapabilities';

interface MessageBubbleProps {
  message: Message;
  currentUserId: string;
  isTargetHighlighted?: boolean;
  onEdit?: (messageId: string, currentContent: string) => void;
  onDelete?: (messageId: string) => void;
  onReply?: (message: Message) => void;
  onOpenThread?: (message: Message) => void;
  onReact?: (messageId: string, emoji: string) => void;
  onForward?: (message: Message) => void;
  onPin?: (messageId: string) => void;
  onRetry?: (message: Message) => void;
  onPreviewAttachment?: (attachment: AttachmentItem) => void;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  currentUserId,
  isTargetHighlighted = false,
  onEdit,
  onDelete,
  onReply,
  onOpenThread,
  onReact,
  onForward,
  onPin,
  onRetry,
  onPreviewAttachment
}) => {
  const isMine = message.sender_id === currentUserId;
  const [showActions, setShowActions] = useState(false);
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [copied, setCopied] = useState(false);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const rawDateStr = (message.edited && message.updated_at) ? message.updated_at : message.created_at;
  const isoUtc = typeof rawDateStr === 'string' && !rawDateStr.endsWith('Z') && !/[+-]\d{2}:?\d{2}$/.test(rawDateStr)
    ? `${rawDateStr}Z`
    : rawDateStr;

  const formattedTime = new Date(isoUtc).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit'
  });

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const handleDownloadAttachment = async (att: AttachmentItem) => {
    if (downloadingId === att.id) return;
    setDownloadingId(att.id);

    try {
      const token = localStorage.getItem('token') || '';
      const downloadUrlWithToken = token ? `${att.download_url}?token=${encodeURIComponent(token)}` : att.download_url;
      const res = await fetch(downloadUrlWithToken);
      if (!res.ok) throw new Error('Download failed');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = att.original_filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download error:', err);
      alert('Unable to download the file. Please try again.');
    } finally {
      setDownloadingId(null);
    }
  };

  const renderStatusIcon = () => {
    if (!isMine) return null;
    switch (message.status) {
      case 'sending':
        return (
          <span title="Sending">
            <Clock className="w-3.5 h-3.5 text-[#E0E7FF]/70 animate-spin shrink-0" />
          </span>
        );
      case 'sent':
        return (
          <span title="Sent to server">
            <Check className="w-3.5 h-3.5 text-[#C7D2FE] shrink-0" />
          </span>
        );
      case 'delivered':
        return (
          <span title="Delivered to recipient">
            <CheckCheck className="w-3.5 h-3.5 text-[#C7D2FE] shrink-0" />
          </span>
        );
      case 'read':
        return (
          <span title="Read by recipient">
            <CheckCheck className="w-3.5 h-3.5 text-[#67E8F9] drop-shadow-sm shrink-0 font-bold" />
          </span>
        );
      case 'failed':
        return (
          <button 
            type="button"
            onClick={() => onRetry && onRetry(message)}
            title="Failed to send. Click to retry"
            className="flex items-center gap-1 text-red-300 hover:text-red-100 font-semibold cursor-pointer underline"
          >
            <AlertCircle className="w-3.5 h-3.5 shrink-0" />
            <span className="text-[9px]">Retry</span>
          </button>
        );
      default:
        return (
          <span title="Sent">
            <Check className="w-3.5 h-3.5 text-[#C7D2FE] shrink-0" />
          </span>
        );
    }
  };

  return (
    <div
      id={`message-${message.id}`}
      className={`group relative flex flex-col my-1.5 px-4 transition-all duration-700 rounded-2xl ${
        isMine ? 'items-end' : 'items-start'
      } ${
        isTargetHighlighted
          ? 'ring-2 ring-indigo-500 shadow-xl shadow-indigo-500/30 bg-indigo-500/10 dark:bg-indigo-500/20 py-2.5 my-3 animate-pulse'
          : ''
      }`}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => {
        setShowActions(false);
        setShowEmojiPicker(false);
      }}
    >
      <div className={`flex items-end space-x-2 max-w-[75%] ${isMine ? 'flex-row-reverse space-x-reverse' : 'flex-row'}`}>
        {!isMine && (
          <div className="w-8 h-8 rounded-full bg-accentSubtle border border-accent/30 text-accentText font-semibold text-xs flex items-center justify-center flex-shrink-0">
            {message.sender?.full_name?.charAt(0).toUpperCase() || 'U'}
          </div>
        )}

        <div
          className={`relative px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${
            isMine
              ? 'bg-[#5B5BF7] dark:bg-[#4F46E5] text-white rounded-br-none shadow-md shadow-indigo-500/10'
              : 'bg-bgCard dark:bg-[#111827] text-textPrimary dark:text-[#F9FAFB] rounded-bl-none border border-borderColor dark:border-[#1F2937] shadow-sm'
          } ${message.deleted ? 'italic opacity-70 border border-dashed border-borderMuted' : ''}`}
        >
          {!isMine && (
            <span className="block text-[11px] font-semibold text-blue-500 dark:text-[#3B82F6] mb-0.5">
              {message.sender?.full_name || message.sender_name}
            </span>
          )}

          {message.content && (
            <p className="whitespace-pre-wrap break-words">{message.content}</p>
          )}

          {/* Render Message Attachments */}
          {message.attachments && message.attachments.length > 0 && (
            <div className={`space-y-2 ${message.content ? 'mt-2 pt-2 border-t border-white/20' : ''}`}>
              {message.attachments.map(att => {
                const caps = detectFileType(att.original_filename, att.mime_type);
                const isCurrentlyDownloading = downloadingId === att.id;

                const renderAttachmentIcon = () => {
                  switch (caps.iconType) {
                    case 'embroidery': return <Scissors className="w-4 h-4 text-purple-400" />;
                    case 'image': return <ImageIcon className="w-4 h-4 text-emerald-400" />;
                    case 'code': return <FileCode className="w-4 h-4 text-purple-400" />;
                    case 'video': return <Film className="w-4 h-4 text-blue-400" />;
                    case 'archive': return <Archive className="w-4 h-4 text-amber-400" />;
                    default: return <FileText className="w-4 h-4" />;
                  }
                };

                return (
                  <div
                    key={att.id}
                    className={`flex items-center justify-between p-2.5 rounded-xl border text-xs gap-3 ${
                      isMine
                        ? 'bg-white/10 border-white/20 text-white'
                        : 'bg-bgInput border-borderColor text-textPrimary'
                    }`}
                  >
                    <div className="flex items-center space-x-2.5 min-w-0">
                      <div className={`p-2 rounded-lg shrink-0 ${isMine ? 'bg-white/20 text-white' : 'bg-accentSubtle text-accentText'}`}>
                        {renderAttachmentIcon()}
                      </div>
                      <div className="min-w-0">
                        <p className="font-medium truncate text-xs" title={att.original_filename}>
                          {att.original_filename}
                        </p>
                        <p className={`text-[10px] ${isMine ? 'text-white/80' : 'text-textMuted'}`}>
                          {formatSize(att.file_size)} • {caps.categoryLabel}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-1 shrink-0">
                      {onPreviewAttachment && (
                        <button
                          type="button"
                          onClick={() => onPreviewAttachment(att)}
                          aria-label="Preview file"
                          className={`p-1.5 rounded-lg transition-colors flex items-center space-x-1 text-[11px] font-semibold cursor-pointer ${
                            isMine
                              ? 'hover:bg-white/20 text-white'
                              : 'hover:bg-bgHover text-accentText'
                          }`}
                          title="Preview File"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          <span className="hidden sm:inline">Preview</span>
                        </button>
                      )}

                      <button
                        type="button"
                        onClick={() => handleDownloadAttachment(att)}
                        disabled={isCurrentlyDownloading}
                        aria-label="Download file"
                        className={`p-1.5 rounded-lg transition-colors flex items-center space-x-1 text-[11px] font-semibold cursor-pointer disabled:opacity-50 ${
                          isMine
                            ? 'hover:bg-white/20 text-white'
                            : 'hover:bg-bgHover text-emerald-400'
                        }`}
                        title="Download File"
                      >
                        {isCurrentlyDownloading ? (
                          <>
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            <span className="hidden sm:inline">Downloading...</span>
                          </>
                        ) : (
                          <>
                            <Download className="w-3.5 h-3.5" />
                            <span className="hidden sm:inline">Download</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          <div className="flex items-center justify-end space-x-1.5 mt-1 text-[10px] select-none">
            <span className={`font-sans text-[10px] leading-none ${isMine ? 'text-[#E0E7FF]' : 'text-textMuted dark:text-gray-400'}`}>
              {formattedTime}
            </span>
            {message.edited && !message.deleted && (
              <span className={`font-sans font-medium text-[10px] leading-none ${isMine ? 'text-[#E0E7FF]/80' : 'text-textMuted opacity-75'}`}>
                • Edited
              </span>
            )}
            {renderStatusIcon()}
          </div>
        </div>
      </div>

      {/* Thread replies trigger button */}
      {((message as any).thread_count > 0 || onOpenThread) && (
        <div className={`mt-1 text-xs ${isMine ? 'mr-10' : 'ml-10'}`}>
          <button
            onClick={() => onOpenThread && onOpenThread(message)}
            className="flex items-center space-x-1 text-purple-500 hover:underline text-[11px] font-medium"
          >
            <MessageSquare className="w-3 h-3" />
            <span>{(message as any).thread_count || 0} {(message as any).thread_count === 1 ? 'reply' : 'replies'}</span>
          </button>
        </div>
      )}

      {/* Emoji Picker Popover */}
      {showEmojiPicker && (
        <div className={`absolute top-0 -translate-y-full z-50 ${isMine ? 'right-6' : 'left-12'}`}>
          <EmojiPicker
            onSelectEmoji={(emoji) => {
              if (onReact) onReact(message.id, emoji);
              setShowEmojiPicker(false);
            }}
            onClose={() => setShowEmojiPicker(false)}
          />
        </div>
      )}

      {/* Hover Actions Bar */}
      {showActions && !message.deleted && (
        <div
          className={`absolute top-0 -translate-y-1/2 flex items-center space-x-1 bg-bgDialog border border-borderColor backdrop-blur rounded-lg p-1 shadow-lg z-10 ${
            isMine ? 'right-6' : 'left-12'
          }`}
        >
          {onReact && (
            <button
              onClick={() => setShowEmojiPicker(prev => !prev)}
              className="p-1 hover:bg-bgHover text-amber-500 hover:text-amber-400 rounded transition-colors"
              title="React"
            >
              <Smile className="w-3.5 h-3.5" />
            </button>
          )}
          {onReply && (
            <button
              onClick={() => onReply(message)}
              className="p-1 hover:bg-bgHover text-textMuted hover:text-textPrimary rounded transition-colors"
              title="Reply"
            >
              <Reply className="w-3.5 h-3.5" />
            </button>
          )}
          {onOpenThread && (
            <button
              onClick={() => onOpenThread(message)}
              className="p-1 hover:bg-bgHover text-purple-500 hover:text-purple-400 rounded transition-colors"
              title="Reply in Thread"
            >
              <MessageSquare className="w-3.5 h-3.5" />
            </button>
          )}
          {onForward && (
            <button
              onClick={() => onForward(message)}
              className="p-1 hover:bg-bgHover text-accentText rounded transition-colors"
              title="Forward Message"
            >
              <Share2 className="w-3.5 h-3.5" />
            </button>
          )}
          {onPin && (
            <button
              onClick={() => onPin(message.id)}
              className="p-1 hover:bg-bgHover text-amber-500 hover:text-amber-400 rounded transition-colors"
              title="Pin Message"
            >
              <Pin className="w-3.5 h-3.5" />
            </button>
          )}
          <button
            onClick={handleCopy}
            className="p-1 hover:bg-bgHover text-textMuted hover:text-textPrimary rounded transition-colors"
            title="Copy Text"
          >
            <Copy className="w-3.5 h-3.5" />
          </button>
          {isMine && onEdit && (
            <button
              onClick={() => onEdit(message.id, message.content)}
              className="p-1 hover:bg-bgHover text-textMuted hover:text-textPrimary rounded transition-colors"
              title="Edit Message"
            >
              <Edit2 className="w-3.5 h-3.5" />
            </button>
          )}
          {isMine && onDelete && (
            <button
              onClick={() => onDelete(message.id)}
              className="p-1 hover:bg-bgHover text-dangerText hover:underline rounded transition-colors"
              title="Delete Message"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      )}
    </div>
  );
};
