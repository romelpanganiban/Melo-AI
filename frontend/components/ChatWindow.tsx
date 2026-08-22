"use client";

import { useEffect, useRef } from "react";
import { ChatMessage } from "@/lib/api";
import MessageBubble from "./MessageBubble";

type MessageWithState = ChatMessage & {
  id: string;
  isStreaming?: boolean;
};

type Props = {
  sessionId: string | null;
  messages: MessageWithState[];
  isLoading: boolean;
  error: string | null;
  onRetry: () => void;
};

export default function ChatWindow({
  sessionId,
  messages,
  isLoading,
  error,
  onRetry,
}: Props) {
  const endOfMessagesRef = useRef<HTMLDivElement | null>(null);

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
      <div className="flex flex-1 items-center justify-center p-6">
        <div className="max-w-md text-center">
          <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl border border-teal-300/15 bg-teal-600 text-2xl text-white shadow-lg shadow-black/30">
            M
          </div>
          <p className="brand-title text-2xl font-semibold text-slate-100">
            A quieter place to think
          </p>
          <p className="empty-chat-copy mt-2 text-sm leading-6 text-slate-300/65">
            Choose a conversation from the sidebar, or create a new one to begin.
          </p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex flex-1 items-center justify-center p-4">
        <div className="text-center">
          <div className="mx-auto h-9 w-9 animate-spin rounded-full border-2 border-teal-900/10 border-t-teal-700" />
          <p className="mt-3 text-sm font-medium text-slate-300/70">Opening conversation</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-1 items-center justify-center p-6">
        <div className="max-w-md rounded-2xl border border-red-900/10 bg-red-50/80 p-6 text-center shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-[0.14em] text-red-700">Unable to load chat</p>
          <p className="mt-2 text-sm leading-6 text-red-950/75">{error}</p>
          <button
            onClick={onRetry}
            className="mt-5 rounded-lg bg-teal-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-teal-500 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-400"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-panel chat-scrollbar mx-3 my-3 flex-1 overflow-y-auto rounded-2xl border border-white/10 bg-black/25 p-4 text-slate-100 shadow-[0_14px_36px_rgba(0,0,0,0.25)] md:mx-4 md:p-6">
      {messages.length === 0 ? (
        <div className="flex items-center justify-center h-full">
          <div className="max-w-sm text-center">
            <p className="brand-title text-xl font-semibold text-slate-100">What is on your mind?</p>
            <p className="mt-2 text-sm leading-6 text-slate-300/55">
              Ask a question, bring in a document, or use the composer below to get started.
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {messages.map((message, index) => (
            <MessageBubble
              key={message.id || `${message.role}-${index}`}
              role={message.role}
              content={message.content}
              sources={message.sources}
              isStreaming={message.isStreaming}
            />
          ))}
          <div ref={endOfMessagesRef} aria-hidden="true" />
        </div>
      )}
    </div>
  );
}