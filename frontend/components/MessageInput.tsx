"use client";

import { useState } from "react";

type Props = {
  sessionId: string | null;
  onSendMessage: (message: string) => void;
  isSending: boolean;
};

export default function MessageInput({
  sessionId,
  onSendMessage,
  isSending,
}: Props) {
  const [message, setMessage] = useState("");
  const [error, setError] = useState<string | null>(null);

  function handleSend() {
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
    setMessage("");
    onSendMessage(trimmedMessage);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="border-t border-gray-300 p-4 bg-white text-gray-900">
      {error && (
        <div className="mb-3 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          <p className="text-sm">{error}</p>
        </div>
      )}

      <div className="flex gap-2">
        <textarea
          value={message}
          onChange={(e) => {
            setMessage(e.target.value);
            setError(null);
          }}
          onKeyDown={handleKeyDown}
          disabled={isSending || !sessionId}
          maxLength={4096}
          rows={2}
          className="max-h-44 min-h-11 flex-1 resize-y rounded border p-2 disabled:bg-gray-100 disabled:text-gray-500"
          placeholder={
            sessionId ? "Message Melo..." : "Select a session to start"
          }
        />

        <button
          type="button"
          onClick={handleSend}
          disabled={isSending || !sessionId || !message.trim()}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition"
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
        <p className="text-xs text-gray-400 mt-1">
          {message.length} / 4096
        </p>
      )}
    </div>
  );
}