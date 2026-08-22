"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  getSessions,
  createSession,
  deleteSession,
  APIError,
} from "@/lib/api";

type Session = {
  id: string;
  title: string;
};

type SidebarProps = {
  selectedSession: string | null;
  setSelectedSession: (sessionId: string) => void;
  isOpen: boolean;
  onClose: () => void;
  onSessionDeleted: (sessionId: string, remainingSessions: Session[]) => void;
  refreshKey?: number;
};

export default function Sidebar({
  selectedSession,
  setSelectedSession,
  isOpen,
  onClose,
  onSessionDeleted,
  refreshKey = 0,
}: SidebarProps) {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadSessions() {
    setIsLoading(true);
    setError(null);

    try {
      const data = await getSessions();
      const payload = data as {
        sessions?: Session[];
      };
      setSessions(payload.sessions || []);
      setError(null);
    } catch (err) {
      const message =
        err instanceof APIError
          ? err.message
          : "Failed to load sessions";
      setError(message);
      setSessions([]);
      console.error("Error loading sessions:", err);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleNewChat() {
    setIsCreating(true);
    setError(null);

    try {
      const newSession = await createSession();
      setSelectedSession(newSession.id);
      await loadSessions();
      setError(null);
    } catch (err) {
      const message =
        err instanceof APIError
          ? err.message
          : "Failed to create session";
      setError(message);
      console.error("Error creating session:", err);
    } finally {
      setIsCreating(false);
    }
  }

  async function handleDeleteChat(event: React.MouseEvent, session: Session) {
    event.stopPropagation();
    if (!window.confirm(`Delete "${session.title}"? This cannot be undone.`)) {
      return;
    }

    try {
      setError(null);
      await deleteSession(session.id);
      const remainingSessions = sessions.filter((item) => item.id !== session.id);
      setSessions(remainingSessions);
      onSessionDeleted(session.id, remainingSessions);
    } catch (err) {
      const message = err instanceof APIError ? err.message : "Failed to delete session";
      setError(message);
    }
  }

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      void loadSessions();
    }, 0);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [refreshKey]);

  return (
    <>
      {isOpen && (
        <button
          type="button"
          className="fixed inset-0 z-30 bg-emerald-950/35 md:hidden"
          onClick={onClose}
          aria-label="Close sidebar"
        />
      )}

      <aside
        className={`chat-sidebar fixed inset-y-0 left-0 z-40 flex w-72 max-w-[calc(100vw-1rem)] min-w-0 flex-none transform flex-col overflow-x-hidden border-r border-white/10 bg-[#0d1411] p-4 transition-transform duration-300 md:static md:w-72 md:translate-x-0 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="mb-4 flex items-start justify-between">
          <div>
            <h2 className="brand-title text-xl font-bold text-slate-100">Melo-AI</h2>
            <p className="text-xs text-slate-400/70">Local AI Assistant</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md px-2 py-1 text-sm text-slate-300/70 hover:bg-white/10 md:hidden"
            aria-label="Close sidebar"
          >
            Close
          </button>
        </div>

        <button
          onClick={handleNewChat}
          disabled={isCreating || isLoading}
          className="w-full rounded-xl bg-teal-600 p-2.5 font-semibold text-white shadow-lg shadow-black/20 transition hover:bg-teal-500 disabled:cursor-not-allowed disabled:bg-white/10 disabled:text-white/35"
        >
          {isCreating ? (
            <span className="inline-flex items-center gap-2">
              <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              Creating...
            </span>
          ) : (
            "+ New Chat"
          )}
        </button>

        <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
          <Link
            href="/models"
            className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-center font-medium text-slate-300 transition hover:bg-white/10"
          >
            Models
          </Link>
          <Link
            href="/settings"
            className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-center font-medium text-slate-300 transition hover:bg-white/10"
          >
            Settings
          </Link>
          <Link
            href="/coding"
            className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-center font-medium text-slate-300 transition hover:bg-white/10"
          >
            Coding
          </Link>
          <Link
            href="/training"
            className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-center font-medium text-slate-300 transition hover:bg-white/10"
          >
            Training
          </Link>
        </div>

        {error && (
          <div className="mt-3 rounded-lg border border-red-300 bg-red-50 p-2 text-xs text-red-700">
            <p>{error}</p>
            <button
              onClick={loadSessions}
              className="mt-1 underline"
            >
              Retry
            </button>
          </div>
        )}

        <div className="chat-scrollbar mt-4 min-h-0 min-w-0 flex-1 space-y-2 overflow-y-auto pr-1">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="inline-block h-6 w-6 animate-spin rounded-full border-b-2 border-teal-700" />
            </div>
          ) : sessions.length === 0 ? (
            <div className="rounded-xl border border-white/10 bg-white/5 py-8 text-center">
              <p className="text-sm text-slate-300/70">No sessions yet</p>
              <p className="mt-1 text-xs text-slate-400/60">Create a new chat to start</p>
            </div>
          ) : (
            sessions.map((session) => (
              <div
                key={session.id}
                className={`group flex w-full items-center gap-1 rounded-lg transition ${
                  selectedSession === session.id
                    ? "bg-teal-500/20 font-semibold text-teal-200"
                    : "text-slate-300/80 hover:bg-white/10"
                }`}
              >
                <button
                  type="button"
                  onClick={() => setSelectedSession(session.id)}
                  className="min-w-0 flex-1 truncate px-3 py-2 text-left text-sm"
                  title={session.title}
                >
                  {session.title}
                </button>
                <button
                  type="button"
                  onClick={(event) => void handleDeleteChat(event, session)}
                  className="mr-1 rounded-md px-2 py-1 text-slate-400/60 opacity-0 transition hover:bg-red-500/20 hover:text-red-300 focus-visible:opacity-100 focus-visible:outline-none group-hover:opacity-100"
                  aria-label={`Delete ${session.title}`}
                  title="Delete chat"
                >
                  &#128465;
                </button>
              </div>
            ))
          )}
        </div>
      </aside>
    </>
  );
}