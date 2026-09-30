interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  placeholder: string;
  /** Disable the send button (e.g. while a request is in flight). */
  disabled?: boolean;
  /** 'sm' = compact (gray-800, rounded-lg, smaller padding); 'md' = default. */
  variant?: 'sm' | 'md';
  /** Extra classes on the wrapper (e.g. top border for an in-card input). */
  className?: string;
}

const INPUT_VARIANT = {
  sm: 'bg-gray-800 rounded-lg px-3 py-2',
  md: 'bg-gray-900 rounded-xl px-4 py-3',
} as const;

const BUTTON_VARIANT = {
  sm: 'px-3 py-2 rounded-lg',
  md: 'px-4 py-3 rounded-xl',
} as const;

/**
 * Shared chat composer: text input + send button with Enter-to-send
 * (Shift+Enter ignored). Send is disabled when empty or `disabled`.
 */
export default function ChatInput({
  value,
  onChange,
  onSend,
  placeholder,
  disabled = false,
  variant = 'md',
  className,
}: ChatInputProps) {
  const sendDisabled = disabled || !value.trim();

  return (
    <div className={`flex gap-2${className ? ` ${className}` : ''}`}>
      <input
        value={value}
        onChange={e => onChange(e.target.value)}
        onKeyDown={e => e.key === 'Enter' && !e.shiftKey && !sendDisabled && onSend()}
        placeholder={placeholder}
        className={`flex-1 border border-gray-700 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-gray-500 ${INPUT_VARIANT[variant]}`}
      />
      <button
        onClick={onSend}
        disabled={sendDisabled}
        className={`bg-blue-600 hover:bg-blue-700 text-sm disabled:opacity-50 transition-colors ${BUTTON_VARIANT[variant]}`}
      >
        →
      </button>
    </div>
  );
}
