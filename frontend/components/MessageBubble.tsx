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
          ? "bg-blue-500 text-white ml-auto rounded-lg shadow"
          : "bg-gray-200 text-gray-900 rounded-lg shadow"
      }`}
    >
      {content}
    </div>
  );
}