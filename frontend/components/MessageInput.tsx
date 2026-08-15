"use client";

import { useState } from "react";
import { sendMessage, APIError } from "@/lib/api";

type Props = {
  sessionId: string | null;
  onMessageSent: () => void;
};

export default function MessageInput({
  sessionId,
  onMessageSent,
}: Props) {
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
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

    setIsLoading(true);
    setError(null);

    try {
      await sendMessage(sessionId, trimmedMessage);
      setMessage("");
      setError(null);
      onMessageSent();
    } catch (err) {
      const errorMessage =
        err instanceof APIError
          ? err.message
          : "Failed to send message";
      setError(errorMessage);
      console.error("Error sending message:", err);
    } finally {
      setIsLoading(false);
    }
  }

  function handleKeyPress(
    e: React.KeyboardEvent<HTMLInputElement>
  ) {
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
        <input
          value={message}
          onChange={(e) => {
            setMessage(e.target.value);
            setError(null);
          }}
          onKeyPress={handleKeyPress}
          disabled={isLoading || !sessionId}
          maxLength={4096}
          className="flex-1 border rounded p-2 disabled:bg-gray-100 disabled:text-gray-500"
          placeholder={
            sessionId ? "Message Melo..." : "Select a session to start"
          }
        />

        <button
          onClick={handleSend}
          disabled={isLoading || !sessionId || !message.trim()}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition"
        >
          {isLoading ? (
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