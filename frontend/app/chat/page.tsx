"use client";

import Link from "next/link";
import { useState } from "react";

import Sidebar from "@/components/Sidebar";
import ChatWindow from "@/components/ChatWindow";
import MessageInput from "@/components/MessageInput";

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

  function reloadMessages() {
    setRefresh(
      (prev) => prev + 1
    );
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

        <ChatWindow
          sessionId={
            selectedSession
          }
          refresh={refresh}
        />

        <MessageInput
          sessionId={
            selectedSession
          }
          onMessageSent={
            reloadMessages
          }
        />
      </div>
    </div>
  );
}