"use client";

import { useState } from "react";

type Props = {
  sessionId: string | null;
  onSendMessage: (message: string) => void;
  isSending: boolean;
};

export default function MessageInput({
  sessionId,
  onSendMessage,
  isSending,
}: Props) {
  const [message, setMessage] = useState("");
  const [error, setError] = useState<string | null>(null);

  function handleSend() {
    if (!sessionId) {
      setError("No session selected");
      return;
    }

    const trimmedMessage = message.trim();
    if (!trimmedMessage) {
      setError("Message cannot be empty");
      return;
    }

    if (trimmedMessage.length > 4096) {
      setError("Message exceeds maximum length (4096 characters)");
      return;
    }

    setError(null);
    setMessage("");
    onSendMessage(trimmedMessage);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="chat-composer border-t border-white/10 bg-black/20 p-3 text-slate-100 md:p-4">
      {error && (
        <div className="mb-3 rounded-xl border border-red-300/15 bg-red-950/40 p-3 text-red-200">
          <p className="text-sm">{error}</p>
        </div>
      )}

      <div className="composer-box flex items-end gap-2 rounded-2xl border border-white/15 bg-[#131a17]/95 p-2 shadow-[0_12px_28px_rgba(0,0,0,0.3)] focus-within:border-teal-400/60 focus-within:shadow-[0_12px_30px_rgba(15,118,110,0.18)]">
        <textarea
          value={message}
          onChange={(e) => {
            setMessage(e.target.value);
            setError(null);
          }}
          onKeyDown={handleKeyDown}
          disabled={isSending || !sessionId}
          maxLength={4096}
          rows={2}
          className="max-h-44 min-h-11 flex-1 resize-y border-0 bg-transparent px-2 py-2 text-sm leading-6 text-slate-100 outline-none disabled:text-slate-100/35"
          placeholder={
            sessionId ? "Message Melo..." : "Select a session to start"
          }
        />

        <button
          type="button"
          onClick={handleSend}
          disabled={isSending || !sessionId || !message.trim()}
          className="min-h-11 rounded-xl bg-teal-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-teal-500 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-400 disabled:cursor-not-allowed disabled:bg-white/10 disabled:text-white/35"
        >
          {isSending ? (
            <span className="inline-flex items-center gap-1">
              <span className="inline-block animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
              Working
            </span>
          ) : (
            "Send"
          )}
        </button>
      </div>

      {message.length > 0 && (
        <p className="mt-2 px-2 text-xs text-slate-300/45">
          {message.length} / 4096
        </p>
      )}
    </div>
  );
}