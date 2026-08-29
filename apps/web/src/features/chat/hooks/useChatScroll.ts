import { useRef, useState, useCallback, useEffect } from 'react';

interface UseChatScrollOptions {
  threshold?: number;
}

export function useChatScroll(options: UseChatScrollOptions = {}) {
  const { threshold = 100 } = options;
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [isAtBottom, setIsAtBottom] = useState<boolean>(true);
  const [hasNewMessages, setHasNewMessages] = useState<boolean>(false);
  const rafIdRef = useRef<number | null>(null);

  const checkIfAtBottom = useCallback(() => {
    const el = containerRef.current;
    if (!el) return true;
    const distanceToBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    return distanceToBottom <= threshold;
  }, [threshold]);

  const handleScroll = useCallback(() => {
    const atBottom = checkIfAtBottom();
    setIsAtBottom(atBottom);
    if (atBottom) {
      setHasNewMessages(false);
    }
  }, [checkIfAtBottom]);

  const scrollToBottom = useCallback((behavior: ScrollBehavior = 'smooth') => {
    const el = containerRef.current;
    if (!el) return;
    el.scrollTo({
      top: el.scrollHeight,
      behavior,
    });
    setIsAtBottom(true);
    setHasNewMessages(false);
  }, []);

  const autoFollow = useCallback(() => {
    if (rafIdRef.current) {
      cancelAnimationFrame(rafIdRef.current);
    }
    rafIdRef.current = requestAnimationFrame(() => {
      const el = containerRef.current;
      if (!el) return;
      if (checkIfAtBottom()) {
        el.scrollTop = el.scrollHeight;
        setIsAtBottom(true);
        setHasNewMessages(false);
      } else {
        setHasNewMessages(true);
      }
    });
  }, [checkIfAtBottom]);

  useEffect(() => {
    return () => {
      if (rafIdRef.current) {
        cancelAnimationFrame(rafIdRef.current);
      }
    };
  }, []);

  return {
    containerRef,
    isAtBottom,
    hasNewMessages,
    handleScroll,
    scrollToBottom,
    autoFollow,
  };
}
