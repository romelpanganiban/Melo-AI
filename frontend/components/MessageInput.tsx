"use client";

import { useState } from "react";
import { type ChatMode, type InstalledModel } from "@/lib/api";

type Props = {
  sessionId: string | null;
  onSendMessage: (message: string) => void;
  isSending: boolean;
  selectedModel?: string;
  availableModels?: InstalledModel[];
  onModelChange?: (model: string) => void;
  mode?: ChatMode;
  onModeChange?: (mode: ChatMode) => void;
};

const MAX_MESSAGE_LENGTH = 8000;

export default function MessageInput({
  sessionId,
  onSendMessage,
  isSending,
  selectedModel = "auto",
  availableModels = [],
  onModelChange = () => undefined,
  mode = "chat",
  onModeChange = () => undefined,
}: Props) {
  const [message, setMessage] = useState("");
  const maxMessageLength = MAX_MESSAGE_LENGTH;
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

    if (trimmedMessage.length > maxMessageLength) {
      setError(`Message exceeds maximum length (${maxMessageLength} characters)`);
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
          maxLength={maxMessageLength}
          rows={2}
          className="max-h-44 min-h-11 flex-1 resize-y border-0 bg-transparent px-2 py-2 text-sm leading-6 text-slate-100 outline-none disabled:text-slate-100/35"
          placeholder={
            sessionId ? "Message Melo..." : "Select a session to start"
          }
        />

        <select
          value={mode}
          onChange={(event) => onModeChange(event.target.value as ChatMode)}
          disabled={isSending}
          aria-label="Choose response mode"
          style={{ colorScheme: "dark" }}
          className="max-w-28 rounded-xl border border-white/15 bg-[#1a2823] px-2 py-2 text-xs text-slate-100 outline-none transition hover:bg-[#24362f] disabled:opacity-50"
        >
          <option value="chat" className="bg-[#1a2823] text-slate-100">Chat</option>
          <option value="ask" className="bg-[#1a2823] text-slate-100">Ask</option>
        </select>

        <select
          value={selectedModel}
          onChange={(event) => onModelChange(event.target.value)}
          disabled={isSending}
          aria-label="Choose chat model"
          style={{ colorScheme: "dark" }}
          className="max-w-40 rounded-xl border border-white/15 bg-[#1a2823] px-2 py-2 text-xs text-slate-100 outline-none transition hover:bg-[#24362f] disabled:opacity-50"
        >
          <option value="auto" className="bg-[#1a2823] text-slate-100">Auto</option>
          {availableModels.map((model) => (
            <option key={model.name} value={model.name} className="bg-[#1a2823] text-slate-100">
              {model.name}
            </option>
          ))}
        </select>

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
          {message.length} / {maxMessageLength}
        </p>
      )}
    </div>
  );
}