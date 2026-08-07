type MessageBubbleProps = {
  role: string;
  content: string;
};

export default function MessageBubble({
  role,
  content,
}: MessageBubbleProps) {
  return (
    <div
      className={`p-3 rounded max-w-xl ${
        role === "user"
          ? "bg-blue-500 text-white ml-auto"
          : "bg-gray-200"
      }`}
    >
      {content}
    </div>
  );
}