"use client";

import {
  useEffect,
  useState,
} from "react";

import { getHistory } from "@/lib/api";
import MessageBubble from "./MessageBubble";

type Props = {
  sessionId: string | null;
  refresh: number;
};

export default function ChatWindow({
  sessionId,
  refresh,
}: Props) {
  const [messages, setMessages] =
    useState<any[]>([]);

  useEffect(() => {
    async function loadHistory() {
      if (!sessionId) return;

      const data =
        await getHistory(
          sessionId
        );

      setMessages(data);
    }

    loadHistory();
  }, [sessionId, refresh]);

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.map(
        (
          message,
          index
        ) => (
          <MessageBubble
            key={index}
            role={message.role}
            content={
              message.content
            }
          />
        )
      )}
    </div>
  );
}