"use client";

import { useEffect, useState } from "react";
import {
  getSessions,
  createSession,
  APIError,
} from "@/lib/api";

type SidebarProps = {
  selectedSession: string | null;
  setSelectedSession: (sessionId: string) => void;
};

export default function Sidebar({
  selectedSession,
  setSelectedSession,
}: SidebarProps) {
  const [sessions, setSessions] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadSessions() {
    setIsLoading(true);
    setError(null);

    try {
      const data = await getSessions();
      setSessions(data.sessions || data || []);
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
      await createSession();
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
    loadSessions();
  }, []);

  return (
    <div className="w-64 h-screen border-r border-gray-300 p-4 flex flex-col bg-gradient-to-b from-blue-50 to-white">
      <div className="mb-4">
        <h2 className="font-bold text-xl">Melo-AI</h2>
        <p className="text-xs text-gray-500">Local AI Assistant</p>
      </div>

      <button
        onClick={handleNewChat}
        disabled={isCreating || isLoading}
        className="w-full p-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition flex items-center justify-center gap-2"
      >
        {isCreating ? (
          <>
            <span className="inline-block animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
            Creating...
          </>
        ) : (
          "+ New Chat"
        )}
      </button>

      {error && (
        <div className="mt-3 p-2 bg-red-100 border border-red-400 text-red-700 text-xs rounded">
          <p>{error}</p>
          <button
            onClick={loadSessions}
            className="mt-1 underline text-xs"
          >
            Retry
          </button>
        </div>
      )}

      <div className="mt-4 space-y-2 flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500" />
          </div>
        ) : sessions.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-400 text-sm">No sessions yet</p>
            <p className="text-gray-400 text-xs mt-1">
              Create a new chat to start
            </p>
          </div>
        ) : (
          sessions.map((session) => (
            <div
              key={session.id}
              onClick={() => setSelectedSession(session.id)}
              className={`cursor-pointer p-2 rounded hover:bg-gray-200 transition truncate ${
                selectedSession === session.id
                  ? "bg-blue-100 font-semibold"
                  : "text-gray-700"
              }`}
              title={session.title}
            >
              {session.title}
            </div>
          ))
        )}
      </div>
    </div>
  );
}