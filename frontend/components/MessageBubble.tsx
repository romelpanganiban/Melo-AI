type MessageBubbleProps = {
  role: string;
  content: string;
  isStreaming?: boolean;
};

export default function MessageBubble({
  role,
  content,
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
    </div>
  );
}