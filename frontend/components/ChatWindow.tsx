"use client";

import { useEffect, useRef, useState } from "react";
import { getHistory, APIError } from "@/lib/api";
import MessageBubble from "./MessageBubble";

type Message = {
  role: string;
  content: string;
};

type Props = {
  sessionId: string | null;
  refresh: number;
};

export default function ChatWindow({
  sessionId,
  refresh,
}: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retryToken, setRetryToken] = useState(0);
  const endOfMessagesRef = useRef<HTMLDivElement | null>(null);

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
        const data = (await getHistory(sessionId)) as {
          messages?: Message[];
        };
        setMessages(data.messages || []);
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
  }, [sessionId, refresh, retryToken]);

  useEffect(() => {
    if (!messages.length) {
      return;
    }
    endOfMessagesRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages]);

  if (!sessionId) {
    return (
      <div className="flex-1 flex items-center justify-center p-4 bg-white">
        <div className="text-center">
          <p className="text-emerald-900/80 text-lg font-medium">
            Select a session to start chatting
          </p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center p-4">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-b-2 border-teal-700" />
          <p className="mt-2 font-medium text-emerald-900/75">Loading messages...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center p-4">
        <div className="text-center">
          <p className="text-lg font-semibold text-red-700">Error</p>
          <p className="mt-2 text-emerald-950/80">{error}</p>
          <button
            onClick={() => setRetryToken((prev) => prev + 1)}
            className="mt-4 rounded-lg bg-teal-700 px-4 py-2 font-medium text-teal-50 transition hover:bg-teal-800"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-3 my-3 flex-1 overflow-y-auto rounded-2xl border border-emerald-900/10 bg-white/75 p-4 text-emerald-950 shadow-sm md:mx-4">
      {messages.length === 0 ? (
        <div className="flex items-center justify-center h-full">
          <p className="text-lg text-emerald-900/55">
            No messages yet. Start a conversation!
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {messages.map((message, index) => (
            <MessageBubble
              key={`${message.role}-${index}`}
              role={message.role}
              content={message.content}
            />
          ))}
          <div ref={endOfMessagesRef} aria-hidden="true" />
        </div>
      )}
    </div>
  );
}