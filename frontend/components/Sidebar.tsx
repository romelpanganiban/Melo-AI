"use client";

import { useEffect, useState } from "react";
import {
  getSessions,
  createSession,
} from "@/lib/api";

type SidebarProps = {
selectedSession: string | null;
setSelectedSession: (
sessionId: string
) => void;
};

export default function Sidebar({
  selectedSession,
  setSelectedSession,
}: SidebarProps) {
  const [sessions, setSessions] =
    useState<any[]>([]);

  async function loadSessions() {
    const data =
      await getSessions();

    setSessions(data);
  }

  async function handleNewChat() {
    await createSession();

    loadSessions();
  }

  useEffect(() => {
    loadSessions();
  }, []);

  return (
    <div className="w-64 h-screen border-r p-4 flex flex-col">
        <h2 className="font-bold text-xl mb-4">
        Melo-AI
        </h2>

        <button
        onClick={handleNewChat}
        className="w-full p-2 bg-blue-500 text-white rounded"
        >
        New Chat
        </button>

        <div className="mt-4 space-y-2 flex-1 overflow-y-auto">
        {sessions.map((session) => (
            <div
            key={session.id}
            onClick={() =>
                setSelectedSession(session.id)
            }
            className={`cursor-pointer p-2 rounded hover:bg-gray-100 ${
                selectedSession === session.id
                ? "bg-blue-100"
                : ""
            }`}
            >
            {session.title}
            </div>
        ))}
        </div>
    </div>
    );
}