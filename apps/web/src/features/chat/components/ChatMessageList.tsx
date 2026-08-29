import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Bot, User as UserIcon, Copy, Check, RotateCcw, Square, Loader2, ArrowDown } from 'lucide-react';
import { ChatMessage, CitationData, ActionProposalData } from '../chat-api';
import { CitationCard } from './CitationCard';
import { ActionProposalCard } from './ActionProposalCard';

interface ChatMessageListProps {
  messages: ChatMessage[];
  streamingToken: string;
  streamingActionProposal?: ActionProposalData | null;
  isStreaming: boolean;
  onStopGeneration?: () => void;
  onRegenerateResponse?: () => void;
  onPreviewCitation: (citation: CitationData) => void;
}

export const ChatMessageList: React.FC<ChatMessageListProps> = React.memo(({
  messages,
  streamingToken,
  streamingActionProposal,
  isStreaming,
  onStopGeneration,
  onRegenerateResponse,
  onPreviewCitation
}) => {
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [showNewMessagesBtn, setShowNewMessagesBtn] = useState(false);

  const containerRef = useRef<HTMLDivElement>(null);
  const bottomSentinelRef = useRef<HTMLDivElement>(null);
  const userScrolledUpRef = useRef(false);
  const prevMessagesCountRef = useRef(messages.length);

  const scrollToBottom = useCallback((smooth = true) => {
    if (bottomSentinelRef.current) {
      bottomSentinelRef.current.scrollIntoView({ behavior: smooth ? 'smooth' : 'auto' });
    } else if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
    userScrolledUpRef.current = false;
    setShowNewMessagesBtn(false);
  }, []);

  // Handle user scroll detection with 90px bottom threshold
  const handleScroll = () => {
    if (!containerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 90;

    if (isAtBottom) {
      userScrolledUpRef.current = false;
      setShowNewMessagesBtn(false);
    } else {
      userScrolledUpRef.current = true;
    }
  };

  // Initial render / Message length / Streaming token effect
  useEffect(() => {
    const messagesCountChanged = messages.length !== prevMessagesCountRef.current;
    prevMessagesCountRef.current = messages.length;

    // If new user message arrived or we are at bottom, auto-scroll
    if (!userScrolledUpRef.current || messagesCountChanged) {
      requestAnimationFrame(() => {
        scrollToBottom(true);
      });
    } else if (userScrolledUpRef.current && (isStreaming || streamingToken)) {
      setShowNewMessagesBtn(true);
    }
  }, [messages.length, streamingToken, isStreaming, scrollToBottom]);

  // Scroll to bottom on initial mount or when conversation changes
  useEffect(() => {
    scrollToBottom(false);
  }, [scrollToBottom]);

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div
      ref={containerRef}
      onScroll={handleScroll}
      className="flex-1 overflow-y-auto p-4 space-y-6 relative custom-scrollbar"
      role="log"
      aria-live="polite"
      aria-label="Chat Message Feed"
    >
      {messages.map((msg, idx) => {
        const isUser = msg.role === 'user';
        const isLastAssistant = !isUser && idx === messages.length - 1;

        return (
          <div key={msg.id || idx} className={`flex gap-3 max-w-4xl ${isUser ? 'ml-auto flex-row-reverse' : ''}`}>
            {/* Avatar */}
            <div className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 text-xs font-semibold shadow-md ${
              isUser
                ? 'bg-accent text-white'
                : 'bg-bgTertiary border border-borderMuted text-accentText'
            }`}>
              {isUser ? <UserIcon size={16} /> : <Bot size={16} />}
            </div>

            {/* Bubble */}
            <div className={`space-y-2 flex-1 min-w-0 ${isUser ? 'items-end text-right' : ''}`}>
              <div className={`inline-block text-left p-4 rounded-2xl text-xs leading-relaxed max-w-full shadow-sm ${
                isUser
                  ? 'bg-accent text-white rounded-tr-none'
                  : 'bg-bgCard border border-borderColor text-textPrimary rounded-tl-none'
              }`}>
                {renderFormattedContent(msg.content)}
              </div>

              {/* Action Proposal Card */}
              {!isUser && (msg.action_proposal || msg.metadata?.action_proposal) && (
                <ActionProposalCard proposal={msg.action_proposal || msg.metadata?.action_proposal} />
              )}

              {/* Citations Card Row */}
              {!isUser && msg.citations && msg.citations.length > 0 && (
                <div className="flex flex-wrap gap-1.5 pt-1">
                  <span className="text-[10px] text-textMuted font-semibold self-center mr-1">Sources:</span>
                  {msg.citations.map((cit, cIdx) => (
                    <CitationCard key={cIdx} citation={cit} onPreviewClick={onPreviewCitation} />
                  ))}
                </div>
              )}

              {/* Assistant Message Actions */}
              {!isUser && (
                <div className="flex items-center gap-2 text-[10px] text-textMuted pt-0.5">
                  <button
                    onClick={() => handleCopy(msg.content, msg.id)}
                    className="flex items-center gap-1 hover:text-textPrimary transition-colors"
                  >
                    {copiedId === msg.id ? <Check size={12} className="text-successText" /> : <Copy size={12} />}
                    {copiedId === msg.id ? 'Copied' : 'Copy'}
                  </button>

                  {isLastAssistant && onRegenerateResponse && !isStreaming && (
                    <button
                      onClick={onRegenerateResponse}
                      className="flex items-center gap-1 hover:text-textPrimary transition-colors ml-2"
                    >
                      <RotateCcw size={12} /> Regenerate
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        );
      })}

      {/* Streaming Active Bubble */}
      {isStreaming && (
        <div className="flex gap-3 max-w-4xl">
          <div className="w-8 h-8 rounded-xl bg-bgTertiary border border-borderMuted text-accentText flex items-center justify-center flex-shrink-0">
            <Bot size={16} />
          </div>
          <div className="space-y-2 flex-1">
            <div className="inline-block p-4 rounded-2xl rounded-tl-none bg-bgCard border border-accent/30 text-textPrimary text-xs leading-relaxed shadow-sm">
              {streamingToken ? (
                renderFormattedContent(streamingToken)
              ) : (
                <div className="flex items-center gap-2 text-accentText">
                  <Loader2 size={14} className="animate-spin" />
                  <span>Retrieving grounded knowledge & generating response...</span>
                </div>
              )}
            </div>

            {streamingActionProposal && (
              <ActionProposalCard proposal={streamingActionProposal} />
            )}

            {onStopGeneration && !streamingActionProposal && (
              <div>
                <button
                  onClick={onStopGeneration}
                  className="flex items-center gap-1.5 px-3 py-1 bg-dangerBg hover:bg-dangerBg/80 border border-dangerBorder text-dangerText rounded-lg text-xs font-medium transition-all"
                >
                  <Square size={12} className="fill-current" /> Stop Generation
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Sentinel for smooth auto-scroll tracking */}
      <div ref={bottomSentinelRef} className="h-1" />

      {/* Floating "↓ New messages" Pill Button */}
      {showNewMessagesBtn && (
        <div className="sticky bottom-2 flex justify-center z-30 pointer-events-none">
          <button
            onClick={() => scrollToBottom(true)}
            className="pointer-events-auto flex items-center gap-1.5 px-3.5 py-1.5 bg-accent hover:bg-accentHover text-white rounded-full text-xs font-semibold shadow-xl border border-white/20 transition-all duration-200 animate-bounce cursor-pointer active:scale-95"
          >
            <ArrowDown size={14} /> New messages
          </button>
        </div>
      )}
    </div>
  );

  function renderFormattedContent(text: string) {
    if (!text) return null;

    const parts = text.split(/(```[\s\S]*?```)/g);

    return parts.map((part, pIdx) => {
      if (part.startsWith('```') && part.endsWith('```')) {
        const codeContent = part.replace(/^```[a-zA-Z]*\n?/, '').replace(/```$/, '');
        return (
          <div key={pIdx} className="my-2 rounded-xl border border-borderColor bg-bgInput overflow-hidden font-mono text-[11px]">
            <div className="flex items-center justify-between px-3 py-1.5 bg-bgHeader border-b border-borderMuted text-[10px] text-textMuted">
              <span>Code Snippet</span>
              <button
                onClick={() => handleCopy(codeContent, `code-${pIdx}`)}
                className="flex items-center gap-1 hover:text-textPrimary transition-colors"
              >
                {copiedId === `code-${pIdx}` ? <Check size={10} className="text-successText" /> : <Copy size={10} />}
                Copy Code
              </button>
            </div>
            <pre className="p-3 overflow-x-auto text-textSecondary leading-relaxed">
              <code>{codeContent}</code>
            </pre>
          </div>
        );
      }

      return (
        <div key={pIdx} className="whitespace-pre-wrap leading-relaxed space-y-1">
          {part}
        </div>
      );
    });
  }
});
