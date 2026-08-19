"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  getSessions,
  createSession,
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
  refreshKey?: number;
};

export default function Sidebar({
  selectedSession,
  setSelectedSession,
  isOpen,
  onClose,
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
        className={`fixed inset-y-0 left-0 z-40 w-72 transform border-r border-emerald-900/15 bg-gradient-to-b from-emerald-50 to-lime-50 p-4 transition-transform duration-300 md:static md:translate-x-0 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="mb-4 flex items-start justify-between">
          <div>
            <h2 className="brand-title text-xl font-bold text-emerald-950">Melo-AI</h2>
            <p className="text-xs text-emerald-900/60">Local AI Assistant</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md px-2 py-1 text-sm text-emerald-900/70 hover:bg-emerald-100 md:hidden"
            aria-label="Close sidebar"
          >
            Close
          </button>
        </div>

        <button
          onClick={handleNewChat}
          disabled={isCreating || isLoading}
          className="w-full rounded-xl bg-teal-700 p-2.5 font-semibold text-teal-50 shadow-sm transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:bg-gray-400"
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
            className="rounded-lg border border-emerald-900/15 bg-white/70 px-3 py-2 text-center font-medium text-emerald-900 transition hover:bg-white"
          >
            Models
          </Link>
          <Link
            href="/settings"
            className="rounded-lg border border-emerald-900/15 bg-white/70 px-3 py-2 text-center font-medium text-emerald-900 transition hover:bg-white"
          >
            Settings
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

        <div className="mt-4 space-y-2 overflow-y-auto">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="inline-block h-6 w-6 animate-spin rounded-full border-b-2 border-teal-700" />
            </div>
          ) : sessions.length === 0 ? (
            <div className="rounded-xl border border-emerald-900/10 bg-white/60 py-8 text-center">
              <p className="text-sm text-emerald-900/70">No sessions yet</p>
              <p className="mt-1 text-xs text-emerald-900/55">Create a new chat to start</p>
            </div>
          ) : (
            sessions.map((session) => (
              <button
                key={session.id}
                type="button"
                onClick={() => setSelectedSession(session.id)}
                className={`w-full truncate rounded-lg px-3 py-2 text-left text-sm transition ${
                  selectedSession === session.id
                    ? "bg-teal-100 font-semibold text-teal-900"
                    : "text-emerald-900/80 hover:bg-emerald-100"
                }`}
                title={session.title}
              >
                {session.title}
              </button>
            ))
          )}
        </div>
      </aside>
    </>
  );
}