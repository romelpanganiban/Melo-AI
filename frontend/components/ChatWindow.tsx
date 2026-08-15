"use client";

import { useEffect, useState } from "react";
import { getHistory, APIError } from "@/lib/api";
import MessageBubble from "./MessageBubble";

type Props = {
  sessionId: string | null;
  refresh: number;
};

export default function ChatWindow({
  sessionId,
  refresh,
}: Props) {
  const [messages, setMessages] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadHistory() {
      if (!sessionId) {
        setMessages([]);
        setError(null);
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const data: any = await getHistory(sessionId);
        setMessages(data.messages || data || []);
        setError(null);
      } catch (err) {
        const message =
          err instanceof APIError
            ? err.message
            : "Failed to load chat history";
        setError(message);
        setMessages([]);
        console.error("Error loading history:", err);
      } finally {
        setIsLoading(false);
      }
    }

    loadHistory();
  }, [sessionId, refresh]);

  if (!sessionId) {
    return (
      <div className="flex-1 flex items-center justify-center p-4 bg-white">
        <div className="text-center">
          <p className="text-gray-600 text-lg font-medium">
            Select a session to start chatting
          </p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center p-4 bg-white">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
          <p className="text-gray-600 mt-2 font-medium">Loading messages...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center p-4 bg-white">
        <div className="text-center">
          <p className="text-red-600 text-lg font-semibold">Error</p>
          <p className="text-gray-700 mt-2">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-white text-gray-900">
      {messages.length === 0 ? (
        <div className="flex items-center justify-center h-full">
          <p className="text-gray-500 text-lg">
            No messages yet. Start a conversation!
          </p>
        </div>
      ) : (
        messages.map((message, index) => (
          <MessageBubble
            key={index}
            role={message.role}
            content={message.content}
          />
        ))
      )}
    </div>
  );
}