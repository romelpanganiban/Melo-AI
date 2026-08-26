"use client";

import { useState } from "react";
import type { ReactNode } from "react";
import { ChatSource, ChatUsage } from "@/lib/api";

type MessageBubbleProps = {
  role: string;
  content: string;
  sources?: ChatSource[];
  isStreaming?: boolean;
  model?: string;
  usage?: ChatUsage;
};

type MessagePart =
  | { type: "text"; content: string }
  | { type: "code"; language: string; content: string };

function splitMessage(content: string): MessagePart[] {
  const parts: MessagePart[] = [];
  const pattern = /```([\w+-]*)\n?([\s\S]*?)```/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = pattern.exec(content)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ type: "text", content: content.slice(lastIndex, match.index) });
    }
    parts.push({
      type: "code",
      language: match[1] || "text",
      content: match[2].replace(/^\n/, "").replace(/\n$/, ""),
    });
    lastIndex = pattern.lastIndex;
  }

  if (lastIndex < content.length) {
    parts.push({ type: "text", content: content.slice(lastIndex) });
  }

  return parts.length ? parts : [{ type: "text", content }];
}

function renderText(content: string): ReactNode {
  const cleaned = content
    .split("\n")
    .filter((line) => !/^\s*(?:\*{3,}|-{3,}|_{3,})\s*$/.test(line))
    .map((line) => line.replace(/^\s*#{1,6}\s+/, ""))
    .join("\n");
  const parts = cleaned.split(/(\*\*[^*]+\*\*|__[^_]+__|`[^`]+`)/g);

  return parts.map((part, index) => {
    if ((part.startsWith("**") && part.endsWith("**")) || (part.startsWith("__") && part.endsWith("__"))) {
      return <strong key={`bold-${index}`}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return <code key={`inline-code-${index}`} className="rounded bg-emerald-900/10 px-1 py-0.5 font-mono text-[0.9em]">{part.slice(1, -1)}</code>;
    }
    return <span key={`text-${index}`}>{part}</span>;
  });
}

function CodeBlock({ language, content }: { language: string; content: string }) {
  const [copied, setCopied] = useState(false);

  async function copyCode() {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className="my-3 overflow-hidden rounded-2xl border border-white/10 bg-[#3b3b3b] text-gray-100 shadow-sm">
      <div className="flex items-center justify-between gap-3 border-b border-white/10 px-4 py-2 text-xs text-gray-200">
        <span className="font-mono">{language}</span>
        <button
          type="button"
          onClick={() => void copyCode()}
          className="rounded-md px-2 py-1 hover:bg-white/10"
          aria-label={`Copy ${language} code`}
        >
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <pre className="overflow-x-auto px-4 py-3 text-xs leading-6 sm:text-sm"><code>{content}</code></pre>
    </div>
  );
}

export default function MessageBubble({
  role,
  content,
  sources = [],
  isStreaming = false,
  model,
  usage,
}: MessageBubbleProps) {
  const isUser = role === "user";

  return (
    <div className={`max-w-3xl ${isUser ? "ml-auto" : "mr-auto"}`}>
      <p className={`mb-1 text-xs font-semibold uppercase tracking-wider ${isUser ? "text-teal-300" : "text-slate-400/65"}`}>
        {isUser ? "You" : "Melo"}
      </p>
      <div
        className={`whitespace-pre-wrap rounded-2xl p-3 text-sm leading-relaxed shadow ${
          isUser
            ? "bg-teal-600 text-white"
            : "assistant-bubble border border-white/10 bg-[#17211d] text-slate-100"
        }`}
      >
        {splitMessage(content).map((part, index) =>
          part.type === "code" ? (
            <CodeBlock key={`code-${index}`} language={part.language} content={part.content} />
          ) : (
            <span key={`text-${index}`}>{renderText(part.content)}</span>
          )
        )}
        {isStreaming && (
          <span className="ml-1 inline-block animate-pulse align-middle text-teal-300">|</span>
        )}
      </div>
      {!isUser && !isStreaming && sources.length > 0 && (
        <div className="mt-2 text-xs text-slate-400/75">
          <p className="font-semibold">Sources</p>
          <ul className="mt-1 space-y-1">
            {sources.map((source) => (
              <li key={`${source.document_id || source.filename}-${source.relevance}`}>
                {source.filename} ({source.relevance.toFixed(1)}% match)
                {source.chunks?.length ? ` · chunks ${source.chunks.join(", ")}` : ""}
              </li>
            ))}
          </ul>
        </div>
      )}
      {!isUser && !isStreaming && (model || usage) && (
        <p className="mt-2 text-[11px] text-slate-400/65">
          {model ? `Model: ${model}` : ""}
          {model && usage ? " · " : ""}
          {usage ? `Credits: ${usage.total_tokens} tokens` : ""}
        </p>
      )}
    </div>
  );
}