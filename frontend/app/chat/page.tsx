"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";

import Sidebar from "@/components/Sidebar";
import ChatWindow from "@/components/ChatWindow";
import MessageInput from "@/components/MessageInput";
import DocumentsPanel from "@/components/DocumentsPanel";
import {
  APIError,
  ChatMessage,
  getHistory,
  sendMessageStream,
} from "@/lib/api";

type ChatMessageWithState = ChatMessage & {
  id: string;
  isStreaming?: boolean;
};

function createMessageId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export default function ChatPage() {
  const [
    selectedSession,
    setSelectedSession,
  ] = useState<string | null>(
    null
  );

  const [refresh, setRefresh] =
    useState(0);
  const [sidebarOpen, setSidebarOpen] =
    useState(false);
  const [messages, setMessages] = useState<ChatMessageWithState[]>([]);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const activeStreamRef = useRef<AbortController | null>(null);

  const loadHistory = useCallback(async () => {
    if (!selectedSession) {
      setMessages([]);
      setError(null);
      return;
    }

    setIsHistoryLoading(true);
    setError(null);

    try {
      const data = (await getHistory(selectedSession)) as {
        messages?: ChatMessage[];
      };

      const mapped = (data.messages || []).map((message, index) => ({
        id: createMessageId(`history-${index}`),
        role: message.role,
        content: message.content,
      }));

      setMessages(mapped);
    } catch (err) {
      const message =
        err instanceof APIError
          ? err.message
          : "Failed to load chat history";
      setError(message);
      setMessages([]);
    } finally {
      setIsHistoryLoading(false);
    }
  }, [selectedSession]);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      void loadHistory();
    }, 0);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [loadHistory, refresh]);

  useEffect(() => {
    activeStreamRef.current?.abort();
  }, [selectedSession]);

  useEffect(() => {
    return () => {
      activeStreamRef.current?.abort();
    };
  }, []);

  async function handleSendMessage(userMessage: string) {
    if (!selectedSession || isSending) {
      return;
    }

    setError(null);
    setIsSending(true);

    const userMessageId = createMessageId("user");
    const assistantMessageId = createMessageId("assistant");

    setMessages((prev) => [
      ...prev,
      {
        id: userMessageId,
        role: "user",
        content: userMessage,
      },
      {
        id: assistantMessageId,
        role: "assistant",
        content: "",
        isStreaming: true,
      },
    ]);

    activeStreamRef.current?.abort();
    const controller = new AbortController();
    activeStreamRef.current = controller;

    try {
      const finalResponse = await sendMessageStream(selectedSession, userMessage, {
        signal: controller.signal,
        onChunk: (chunk) => {
          setMessages((prev) =>
            prev.map((message) =>
              message.id === assistantMessageId
                ? {
                    ...message,
                    content: message.content + chunk,
                  }
                : message
            )
          );
        },
      });

      setMessages((prev) =>
        prev.map((message) =>
          message.id === assistantMessageId
            ? {
                ...message,
                content: finalResponse,
                isStreaming: false,
              }
            : message
        )
      );
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        return;
      }

      const message =
        err instanceof APIError || err instanceof Error
          ? err.message
          : "Failed to send message";

      setError(message);
      setMessages((prev) =>
        prev.map((item) =>
          item.id === assistantMessageId
            ? {
                ...item,
                content: `[Error] ${message}`,
                isStreaming: false,
              }
            : item
        )
      );
    } finally {
      setIsSending(false);
      activeStreamRef.current = null;
    }
  }

  return (
    <div className="page-shell h-screen flex overflow-hidden">
      <Sidebar
        selectedSession={
          selectedSession
        }
        setSelectedSession={
          (id) => {
            setSelectedSession(id);
            setSidebarOpen(false);
          }
        }
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="glass-panel mx-3 mt-3 flex items-center justify-between rounded-2xl px-4 py-3 md:mx-4">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setSidebarOpen((prev) => !prev)}
              className="rounded-lg border border-emerald-900/20 bg-white/70 px-3 py-1.5 text-sm font-medium text-emerald-900 transition hover:bg-white md:hidden"
              aria-label="Toggle sidebar"
            >
              Menu
            </button>
            <div>
              <h1 className="brand-title text-lg font-semibold text-emerald-950 md:text-xl">Melo Chat</h1>
              <p className="text-xs text-emerald-900/65">Private by design, local by default</p>
            </div>
          </div>

          <nav className="flex items-center gap-2 text-sm">
            <Link
              href="/models"
              className="rounded-lg px-3 py-1.5 font-medium text-emerald-900 transition hover:bg-emerald-100"
            >
              Models
            </Link>
            <Link
              href="/settings"
              className="rounded-lg px-3 py-1.5 font-medium text-emerald-900 transition hover:bg-emerald-100"
            >
              Settings
            </Link>
          </nav>
        </header>

        <div className="flex min-h-0 flex-1 flex-col md:flex-row">
          <div className="flex min-h-0 flex-1 flex-col">
            <ChatWindow
              sessionId={
                selectedSession
              }
              messages={messages}
              isLoading={isHistoryLoading}
              error={error}
              onRetry={() => {
                setRefresh((prev) => prev + 1);
              }}
            />

            <MessageInput
              sessionId={
                selectedSession
              }
              onSendMessage={handleSendMessage}
              isSending={isSending}
            />
          </div>

          <DocumentsPanel sessionId={selectedSession} />
        </div>
      </div>
    </div>
  );
}