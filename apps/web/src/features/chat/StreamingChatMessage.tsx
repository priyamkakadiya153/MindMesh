import React, { useState, useEffect, useRef } from 'react';
import { Sparkles, Square, RefreshCw, CheckCircle2, Clock } from 'lucide-react';
import { streamChatResponse, StreamChatPayload } from './api';
import { useAuth } from '../auth/auth-provider';

interface StreamingChatMessageProps {
  query: string;
  conversationId?: string;
  workspaceId?: string;
  provider?: string;
  model?: string;
  onCompleted?: (finalText: string) => void;
}

export const StreamingChatMessage: React.FC<StreamingChatMessageProps> = ({
  query,
  conversationId,
  workspaceId,
  provider,
  model,
  onCompleted
}) => {
  const { token, user } = useAuth();
  const orgId = user?.organization_id || '';

  const [text, setText] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [statusEvent, setStatusEvent] = useState<string>('connecting');
  const [metrics, setMetrics] = useState<{ tokens: number; latency: number } | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const textContainerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!query || !token) return;

    const controller = new AbortController();
    abortControllerRef.current = controller;
    setIsStreaming(true);
    setText('');
    setStatusEvent('connecting');

    streamChatResponse(
      token,
      orgId,
      {
        query,
        conversation_id: conversationId,
        workspace_id: workspaceId,
        provider,
        model
      },
      (eventData) => {
        if (eventData.event === 'connected') {
          setStatusEvent('streaming');
        } else if (eventData.event === 'token') {
          setText(eventData.accumulated || '');
        } else if (eventData.event === 'progress') {
          setMetrics((prev) => ({ tokens: eventData.tokens_streamed, latency: prev?.latency || 0 }));
        } else if (eventData.event === 'completed') {
          setIsStreaming(false);
          setStatusEvent('completed');
          setMetrics({ tokens: eventData.total_tokens, latency: eventData.latency_ms });
          if (onCompleted) onCompleted(text);
        } else if (eventData.event === 'cancelled') {
          setIsStreaming(false);
          setStatusEvent('cancelled');
        }
      },
      (err) => {
        console.error('Streaming error:', err);
        setIsStreaming(false);
        setStatusEvent('error');
      },
      controller.signal
    );

    return () => {
      controller.abort();
    };
  }, [query, conversationId, workspaceId, token]);

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsStreaming(false);
      setStatusEvent('cancelled');
    }
  };

  return (
    <div className="bg-bgCard border border-borderColor rounded-2xl p-5 space-y-4 shadow-xl">
      {/* Header status bar */}
      <div className="flex items-center justify-between text-xs border-b border-borderMuted pb-3">
        <div className="flex items-center gap-2">
          <Sparkles size={16} className="text-accentText" />
          <span className="font-semibold text-textPrimary">MindMesh AI Assistant</span>
          {isStreaming && (
            <span className="px-2 py-0.5 bg-accentSubtle border border-accent/30 text-accentText text-[11px] font-medium rounded-full flex items-center gap-1">
              <RefreshCw size={11} className="animate-spin" /> Streaming Tokens
            </span>
          )}
          {statusEvent === 'completed' && (
            <span className="px-2 py-0.5 bg-successBg text-successText text-[11px] font-medium rounded-full flex items-center gap-1">
              <CheckCircle2 size={11} /> Complete
            </span>
          )}
        </div>

        <div className="flex items-center gap-3">
          {metrics && (
            <span className="text-[11px] font-mono text-textMuted flex items-center gap-1">
              <Clock size={11} /> {metrics.latency}ms • {metrics.tokens} Tokens
            </span>
          )}
          {isStreaming && (
            <button
              onClick={handleStop}
              className="flex items-center gap-1 px-2.5 py-1 bg-dangerBg hover:bg-dangerBg/80 text-dangerText border border-dangerBorder rounded-lg text-xs font-semibold transition-colors"
            >
              <Square size={10} className="fill-current" /> Stop
            </button>
          )}
        </div>
      </div>

      {/* Streaming Response Content */}
      <div ref={textContainerRef} className="text-xs text-textPrimary font-mono leading-relaxed whitespace-pre-wrap">
        {text}
        {isStreaming && <span className="inline-block w-1.5 h-3.5 bg-accent ml-1 animate-pulse" />}
      </div>
    </div>
  );
};
