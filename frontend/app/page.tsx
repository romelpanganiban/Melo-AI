import Link from "next/link";

export default function Home() {
  return (
    <main className="h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-white">
      <Link href="/chat">
        Open Melo-AI
      </Link>
    </main>
  );
}