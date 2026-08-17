"use client";

import { useState } from "react";

type Props = {
  sessionId: string | null;
  onSendMessage: (message: string) => Promise<void>;
  isSending: boolean;
};

export default function MessageInput({
  sessionId,
  onSendMessage,
  isSending,
}: Props) {
  const [message, setMessage] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleSend() {
    if (!sessionId) {
      setError("No session selected");
      return;
    }

    const trimmedMessage = message.trim();
    if (!trimmedMessage) {
      setError("Message cannot be empty");
      return;
    }

    if (trimmedMessage.length > 4096) {
      setError("Message exceeds maximum length (4096 characters)");
      return;
    }

    setError(null);

    try {
      await onSendMessage(trimmedMessage);
      setMessage("");
      setError(null);
    } catch (err) {
      const errorMessage =
        err instanceof Error
          ? err.message
          : "Failed to send message";
      setError(errorMessage);
      console.error("Error sending message:", err);
    }
  }

  function handleKeyPress(
    e: React.KeyboardEvent<HTMLTextAreaElement>
  ) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="mx-3 mb-3 rounded-2xl border border-emerald-900/10 bg-white/85 p-4 text-emerald-950 shadow-sm md:mx-4 md:mb-4">
      {error && (
        <div className="mb-3 rounded-lg border border-red-300 bg-red-50 p-3 text-red-700">
          <p className="text-sm">{error}</p>
        </div>
      )}

      <div className="flex items-end gap-2">
        <textarea
          value={message}
          onChange={(e) => {
            setMessage(e.target.value);
            setError(null);
          }}
          onKeyPress={handleKeyPress}
          disabled={isSending || !sessionId}
          maxLength={4096}
          rows={2}
          className="max-h-44 min-h-11 flex-1 resize-y rounded-xl border border-emerald-900/20 p-2.5 text-sm shadow-inner outline-none transition focus:border-teal-700 focus:ring-2 focus:ring-teal-200 disabled:bg-gray-100 disabled:text-gray-500"
          placeholder={
            sessionId ? "Message Melo... (Enter to send, Shift+Enter for new line)" : "Select a session to start"
          }
        />

        <button
          onClick={handleSend}
          disabled={isSending || !sessionId || !message.trim()}
          className="rounded-xl bg-teal-700 px-4 py-2 font-semibold text-teal-50 transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:bg-gray-400"
        >
          {isSending ? (
            <span className="inline-flex items-center gap-1">
              <span className="inline-block animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
              Sending
            </span>
          ) : (
            "Send"
          )}
        </button>
      </div>

      {message.length > 0 && (
        <p className="mt-1 text-xs text-emerald-900/55">
          {message.length} / 4096
        </p>
      )}
    </div>
  );
}