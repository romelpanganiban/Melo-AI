"use client";

import { useRef, useState } from "react";
import { type ChatMode, type InstalledModel } from "@/lib/api";
import { Bot, BookOpen, ClipboardList, FileText, MessageCircle, Paperclip, Search, Sparkles, X } from "lucide-react";

type Props = {
  sessionId: string | null;
  onSendMessage: (message: string, file?: File) => void;
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
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  function handleSend() {
    if (!sessionId) {
      setError("No session selected");
      return;
    }

    const trimmedMessage = message.trim();
    if (!trimmedMessage && !attachedFile) {
      setError("Message cannot be empty");
      return;
    }

    if (trimmedMessage.length > maxMessageLength) {
      setError(`Message exceeds maximum length (${maxMessageLength} characters)`);
      return;
    }

    setError(null);
    setMessage("");
    if (attachedFile) {
      onSendMessage(trimmedMessage || "Please read and summarize this file.", attachedFile);
    } else {
      onSendMessage(trimmedMessage);
    }
    setAttachedFile(null);
  }

  function selectFile(file: File | undefined) {
    if (!file) return;
    const extension = file.name.toLowerCase().split(".").pop();
    if (!extension || !["txt", "pdf", "docx"].includes(extension)) {
      setError("Only PDF, DOCX, and TXT files are supported");
      return;
    }
    setAttachedFile(file);
    setError(null);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="chat-composer border-t border-white/10 bg-[#0b1111]/80 p-3 text-slate-100 md:p-4">
      {error && (
        <div className="mb-3 rounded-xl border border-red-500/25 bg-red-500/10 p-3 text-red-200">
          <p className="text-sm">{error}</p>
        </div>
      )}

      <div
        className="composer-box flex flex-wrap items-end gap-2 rounded-2xl border border-white/10 bg-[#0d1715] p-2 shadow-[0_12px_28px_rgba(0,0,0,0.24)] focus-within:border-teal-500/60 focus-within:shadow-[0_12px_30px_rgba(15,118,110,0.18)]"
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault();
          selectFile(event.dataTransfer.files[0]);
        }}
      >
        {attachedFile && (
          <div className="order-first flex basis-full items-center gap-2 rounded-xl border border-white/10 bg-[#101b19] px-3 py-2 text-xs text-slate-200">
            <FileText size={16} className="text-red-300" aria-hidden="true" />
            <span className="min-w-0 flex-1 truncate" title={attachedFile.name}>{attachedFile.name}</span>
            <span className="text-slate-400">{attachedFile.name.split(".").pop()?.toUpperCase()}</span>
            <button type="button" onClick={() => setAttachedFile(null)} aria-label="Remove attached file" className="rounded p-1 text-slate-400 hover:bg-white/5 hover:text-slate-100">
              <X size={14} aria-hidden="true" />
            </button>
          </div>
        )}
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
          className="max-h-44 min-h-11 min-w-[min(100%,14rem)] flex-[1_1_18rem] resize-y border-0 bg-transparent px-2 py-2 text-sm leading-6 text-slate-100 placeholder:text-slate-400 outline-none disabled:text-slate-500"
          placeholder={
            sessionId ? "Message Melo..." : "Select a session to start"
          }
        />

        <input
          ref={fileInputRef}
          type="file"
          accept=".txt,.pdf,.docx"
          className="hidden"
          onChange={(event) => selectFile(event.target.files?.[0])}
        />
        <button type="button" onClick={() => fileInputRef.current?.click()} disabled={isSending || !sessionId} aria-label="Attach a document" className="rounded-lg p-2 text-slate-300 transition hover:bg-white/5 hover:text-slate-100 disabled:opacity-40">
          <Paperclip size={17} aria-hidden="true" />
        </button>

        <label className="flex items-center gap-1 rounded-xl border border-white/10 bg-[#101b19] px-2 text-xs text-slate-200">
          {mode === "ask" ? <Search size={14} aria-hidden="true" /> : mode === "study" ? <BookOpen size={14} aria-hidden="true" /> : mode === "plan" ? <ClipboardList size={14} aria-hidden="true" /> : mode === "agent" ? <Bot size={14} aria-hidden="true" /> : mode === "auto" ? <Sparkles size={14} aria-hidden="true" /> : <MessageCircle size={14} aria-hidden="true" />}
          <span className="sr-only">Choose response mode</span>
          <select
            value={mode}
            onChange={(event) => onModeChange(event.target.value as ChatMode)}
            disabled={isSending}
            aria-label="Choose response mode"
            className="max-w-20 bg-transparent py-2 text-xs text-slate-200 outline-none disabled:opacity-50"
          >
            <option value="chat" className="bg-[#0d1715] text-slate-100">Chat</option>
            <option value="ask" className="bg-[#0d1715] text-slate-100">Ask</option>
            <option value="study" className="bg-[#0d1715] text-slate-100">Study</option>
            <option value="plan" className="bg-[#0d1715] text-slate-100">Plan</option>
            <option value="agent" className="bg-[#0d1715] text-slate-100">Agent</option>
            <option value="auto" className="bg-[#0d1715] text-slate-100">Auto</option>
          </select>
        </label>

        <select
          value={selectedModel}
          onChange={(event) => onModelChange(event.target.value)}
          disabled={isSending}
          aria-label="Choose chat model"
          className="min-w-0 max-w-40 flex-1 rounded-xl border border-white/10 bg-[#101b19] px-2 py-2 text-xs text-slate-200 outline-none transition hover:bg-[#12201d] disabled:opacity-50 sm:flex-none"
        >
          <option value="auto" className="bg-[#0d1715] text-slate-100">Auto</option>
          {availableModels.map((model) => (
            <option key={model.name} value={model.name} className="bg-[#0d1715] text-slate-100">
              {model.name}
            </option>
          ))}
        </select>

        <button
          type="button"
          onClick={handleSend}
          disabled={isSending || !sessionId || (!message.trim() && !attachedFile)}
          className="min-h-11 flex-1 rounded-xl bg-teal-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-teal-500 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-400 disabled:cursor-not-allowed disabled:bg-white/10 disabled:text-white/35 sm:flex-none"
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
        <p className="mt-2 px-2 text-xs text-slate-400">
          {message.length} / {maxMessageLength}
        </p>
      )}
    </div>
  );
}