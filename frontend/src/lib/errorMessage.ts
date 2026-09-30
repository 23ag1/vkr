import { AxiosError } from 'axios';

const DEFAULT_MESSAGE = 'Произошла ошибка. Попробуйте ещё раз.';
const MAX_LENGTH = 300;

// Defence-in-depth: server-controlled strings are rendered as text (React escapes
// them), but cap the length so an oversized backend message can't dominate the UI.
const clamp = (msg: string): string =>
  msg.length > MAX_LENGTH ? `${msg.slice(0, MAX_LENGTH - 1)}…` : msg;

/**
 * Extract a human-readable message from an unknown thrown value.
 * Prefers the API response envelope ({ error: string }), then the
 * axios/native Error message, falling back to a generic Russian message.
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const envelope = error.response?.data as { error?: unknown } | undefined;
    if (envelope && typeof envelope.error === 'string' && envelope.error.trim()) {
      return clamp(envelope.error.trim());
    }
    if (error.message.trim()) return clamp(error.message.trim());
  }
  if (error instanceof Error && error.message.trim()) return clamp(error.message.trim());
  if (typeof error === 'string' && error.trim()) return clamp(error.trim());
  return DEFAULT_MESSAGE;
}
