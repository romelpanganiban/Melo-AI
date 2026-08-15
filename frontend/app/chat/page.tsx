"use client";

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

  function reloadMessages() {
    setRefresh(
      (prev) => prev + 1
    );
  }

  return (
    <div className="h-screen flex bg-white">
      <Sidebar
        selectedSession={
          selectedSession
        }
        setSelectedSession={
          setSelectedSession
        }
      />

      <div className="flex flex-col flex-1">
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