import { useRef, useEffect, type ReactNode } from 'react';

export interface ChatBubble {
  /** Stable React key for this row. */
  key: string;
  /** Which side the bubble aligns to. */
  side: 'left' | 'right';
  /** Bubble body. */
  content: ReactNode;
  /** Tailwind classes for colour/border/max-width/whitespace — page-specific. */
  bubbleClassName: string;
  /** Optional node rendered above the bubble (role label, score badge). */
  header?: ReactNode;
  /** Optional node rendered below the bubble (feedback, source chips). */
  footer?: ReactNode;
}

interface ChatThreadProps {
  messages: ChatBubble[];
  /** Show the "..." typing indicator after the last message. */
  loading?: boolean;
  /** Tailwind classes for the loading bubble — page-specific (e.g. red border). */
  loadingBubbleClassName?: string;
  /** Tailwind classes for the scroll container. */
  className?: string;
}

const BUBBLE_BASE = 'px-4 py-2 rounded-xl text-sm';

/**
 * Shared scrollable chat message list with auto-scroll-to-bottom and a typing
 * indicator. All page-specific styling (colours, borders, max-width, decorations)
 * is supplied per-message so visual output stays identical across consumers.
 */
export default function ChatThread({
  messages,
  loading = false,
  loadingBubbleClassName = 'bg-gray-800 text-gray-400',
  className,
}: ChatThreadProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  return (
    <div className={className}>
      {messages.map(m => (
        <div
          key={m.key}
          className={`flex flex-col ${m.side === 'right' ? 'items-end' : 'items-start'}`}
        >
          {m.header}
          <div className={`${BUBBLE_BASE} ${m.bubbleClassName}`}>{m.content}</div>
          {m.footer}
        </div>
      ))}
      {loading && (
        <div className="flex justify-start">
          <div className={`${BUBBLE_BASE} ${loadingBubbleClassName}`}>...</div>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
