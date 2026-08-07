"use client";

import { useState } from "react";
import { sendMessage } from "@/lib/api";

type Props = {
  sessionId: string | null;
  onMessageSent: () => void;
};

export default function MessageInput({
  sessionId,
  onMessageSent,
}: Props) {
  const [message, setMessage] =
    useState("");

  async function handleSend() {
    if (!sessionId) return;

    if (!message.trim()) return;

    await sendMessage(
      sessionId,
      message
    );

    setMessage("");

    onMessageSent();
  }

  return (
    <div className="border-t p-4 flex gap-2">
      <input
        value={message}
        onChange={(e) =>
          setMessage(e.target.value)
        }
        className="flex-1 border rounded p-2"
        placeholder="Message Melo..."
      />

      <button
        onClick={handleSend}
        className="bg-blue-500 text-white px-4 rounded"
      >
        Send
      </button>
    </div>
  );
}