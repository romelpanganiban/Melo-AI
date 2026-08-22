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
  ChatSource,
  createSession,
  getSessions,
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
  const [sessionRefresh, setSessionRefresh] =
    useState(0);
  const [sidebarOpen, setSidebarOpen] =
    useState(false);
  const [messages, setMessages] = useState<ChatMessageWithState[]>([]);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const historyRequestRef = useRef(0);
  const activeStreamRef = useRef<AbortController | null>(null);
  const sessionBootstrapRef = useRef(false);
  const localSessionRef = useRef<string | null>(null);

  function createLocalSessionId() {
    if (typeof crypto !== "undefined" && crypto.randomUUID) {
      return crypto.randomUUID();
    }
    return `local-${Date.now()}`;
  }

  useEffect(() => {
    if (sessionBootstrapRef.current || selectedSession) {
      return;
    }

    sessionBootstrapRef.current = true;
    void (async () => {
      try {
        const response = await getSessions();
        const sessions = Array.isArray(response.sessions) ? response.sessions : [];
        const session = sessions[0] ?? await createSession();
        setSelectedSession(session.id);
        setSessionRefresh((current) => current + 1);
      } catch {
        localSessionRef.current = createLocalSessionId();
        setSelectedSession(localSessionRef.current);
        setError(null);
      }
    })();
  }, [selectedSession]);

  const loadHistory = useCallback(async () => {
    const requestId = ++historyRequestRef.current;

    if (!selectedSession) {
      setMessages([]);
      setError(null);
      return;
    }

    if (localSessionRef.current === selectedSession) {
      setMessages([]);
      setIsHistoryLoading(false);
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

      if (requestId === historyRequestRef.current) {
        setMessages(mapped);
      }
    } catch (err) {
      if (requestId !== historyRequestRef.current) {
        return;
      }

      const message =
        err instanceof APIError
          ? err.message
          : "Failed to load chat history";
      setError(message);
      setMessages([]);
    } finally {
      if (requestId === historyRequestRef.current) {
        setIsHistoryLoading(false);
      }
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
        onSources: (sources: ChatSource[]) => {
          setMessages((prev) =>
            prev.map((message) =>
              message.id === assistantMessageId
                ? { ...message, sources }
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
      setSessionRefresh((prev) => prev + 1);
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
        refreshKey={sessionRefresh}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="glass-panel mx-3 mt-3 flex items-center justify-between rounded-2xl px-4 py-3 md:mx-4">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setSidebarOpen((prev) => !prev)}
              className="rounded-lg border border-white/15 bg-white/5 px-3 py-1.5 text-sm font-medium text-slate-200 transition hover:bg-white/10 md:hidden"
              aria-label="Toggle sidebar"
            >
              Menu
            </button>
            <div>
              <h1 className="brand-title text-lg font-semibold text-slate-100 md:text-xl">Melo Chat</h1>
              <p className="text-xs text-slate-400/70">Private by design, local by default</p>
            </div>
          </div>

          <nav className="hidden items-center gap-2 text-sm md:flex">
            <Link
              href="/models"
              className="rounded-lg px-3 py-1.5 font-medium text-slate-300 transition hover:bg-white/10"
            >
              Models
            </Link>
            <Link
              href="/settings"
              className="rounded-lg px-3 py-1.5 font-medium text-slate-300 transition hover:bg-white/10"
            >
              Settings
            </Link>
            <Link
              href="/coding"
              className="rounded-lg px-3 py-1.5 font-medium text-slate-300 transition hover:bg-white/10"
            >
              Coding
            </Link>
            <Link
              href="/training"
              className="rounded-lg px-3 py-1.5 font-medium text-slate-300 transition hover:bg-white/10"
            >
              Training
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