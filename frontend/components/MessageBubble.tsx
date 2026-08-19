import { ChatSource } from "@/lib/api";

type MessageBubbleProps = {
  role: string;
  content: string;
  sources?: ChatSource[];
  isStreaming?: boolean;
};

export default function MessageBubble({
  role,
  content,
  sources = [],
  isStreaming = false,
}: MessageBubbleProps) {
  const isUser = role === "user";

  return (
    <div className={`max-w-3xl ${isUser ? "ml-auto" : "mr-auto"}`}>
      <p className={`mb-1 text-xs font-semibold uppercase tracking-wider ${isUser ? "text-teal-800" : "text-emerald-900/55"}`}>
        {isUser ? "You" : "Melo"}
      </p>
      <div
        className={`whitespace-pre-wrap rounded-2xl p-3 text-sm leading-relaxed shadow ${
          isUser
            ? "bg-teal-700 text-teal-50"
            : "border border-emerald-900/10 bg-emerald-50/65 text-emerald-950"
        }`}
      >
        {content}
        {isStreaming && (
          <span className="ml-1 inline-block animate-pulse align-middle text-emerald-800">|</span>
        )}
      </div>
      {!isUser && !isStreaming && sources.length > 0 && (
        <div className="mt-2 text-xs text-emerald-900/70">
          <p className="font-semibold">Sources</p>
          <ul className="mt-1 space-y-1">
            {sources.map((source) => (
              <li key={`${source.filename}-${source.relevance}`}>
                {source.filename} ({source.relevance.toFixed(1)}% match)
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}