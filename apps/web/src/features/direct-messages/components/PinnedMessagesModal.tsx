import React, { useState, useEffect } from 'react';
import { PinnedMessageItem, getPinnedMessages, unpinMessage } from '../advanced-api';
import { Pin, X, Loader2, ArrowRight } from 'lucide-react';

interface PinnedMessagesModalProps {
  isOpen: boolean;
  onClose: () => void;
  conversationId: string;
  onJumpToMessage?: (messageId: string) => void;
  token?: string;
}

export const PinnedMessagesModal: React.FC<PinnedMessagesModalProps> = ({
  isOpen,
  onClose,
  conversationId,
  onJumpToMessage,
  token
}) => {
  const [pins, setPins] = useState<PinnedMessageItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!isOpen || !conversationId) return;
    setIsLoading(true);
    getPinnedMessages(conversationId, token)
      .then(res => setPins(res))
      .catch(err => console.error('Failed fetching pinned messages:', err))
      .finally(() => setIsLoading(false));
  }, [isOpen, conversationId, token]);

  if (!isOpen) return null;

  const handleUnpin = async (messageId: string) => {
    try {
      await unpinMessage(messageId, token);
      setPins(prev => prev.filter(p => p.message_id !== messageId));
    } catch (err) {
      console.error('Failed unpinning message:', err);
    }
  };

  return (
    <div className="fixed inset-0 bg-bgOverlay backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-bgDialog border border-borderColor rounded-2xl w-full max-w-lg p-5 shadow-2xl space-y-4">
        <div className="flex items-center justify-between border-b border-borderMuted pb-3">
          <div className="flex items-center space-x-2">
            <Pin className="w-5 h-5 text-amber-500 fill-amber-500" />
            <h3 className="text-sm font-semibold text-textPrimary">Pinned Messages</h3>
          </div>
          <button onClick={onClose} className="p-1 text-textMuted hover:text-textPrimary rounded-lg">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="max-h-96 overflow-y-auto space-y-3">
          {isLoading ? (
            <div className="flex items-center justify-center py-8 text-xs text-textMuted">
              <Loader2 className="w-4 h-4 animate-spin mr-2 text-accentText" />
              Loading pins...
            </div>
          ) : pins.length === 0 ? (
            <div className="py-8 text-center text-xs text-textMuted">
              No pinned messages in this conversation
            </div>
          ) : (
            pins.map(pin => (
              <div
                key={pin.id}
                className="bg-bgCard border border-borderColor rounded-xl p-3 space-y-2 hover:border-borderHover transition-colors"
              >
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-textPrimary">{pin.message.sender_name || 'User'}</span>
                  <span className="text-[10px] text-textMuted">{new Date(pin.pinned_at).toLocaleDateString()}</span>
                </div>
                <p className="text-xs text-textSecondary leading-relaxed">{pin.message.content}</p>

                <div className="flex items-center justify-between pt-2 border-t border-borderMuted text-[10px]">
                  <span className="text-textMuted">Pinned by {pin.pinned_by_name}</span>
                  <div className="flex items-center space-x-2">
                    {onJumpToMessage && (
                      <button
                        onClick={() => {
                          onJumpToMessage(pin.message_id);
                          onClose();
                        }}
                        className="text-accentText hover:underline flex items-center space-x-1"
                      >
                        <span>Jump</span>
                        <ArrowRight className="w-3 h-3" />
                      </button>
                    )}
                    <button
                      onClick={() => handleUnpin(pin.message_id)}
                      className="text-dangerText hover:underline"
                    >
                      Unpin
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
