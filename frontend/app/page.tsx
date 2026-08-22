import Link from "next/link";

export default function Home() {
  return (
    <main className="home-page page-shell flex min-h-screen items-center justify-center px-6 py-14">
      <section className="glass-panel w-full max-w-4xl rounded-3xl p-8 md:p-12">
        <p className="home-eyebrow text-xs uppercase tracking-[0.25em]">Local-first intelligence</p>
        <h1 className="home-heading brand-title mt-4 text-4xl font-bold leading-tight md:text-6xl">
          Melo-AI is your private workspace companion.
        </h1>
        <p className="home-copy mt-5 max-w-2xl text-base md:text-lg">
          Chat, tune your model, and keep everything local on your own machine with a fast, focused interface.
        </p>

        <div className="mt-8 flex flex-col gap-3 sm:flex-row">
          <Link
            href="/chat"
            className="rounded-xl bg-teal-600 px-5 py-3 text-center font-semibold text-white transition hover:bg-teal-500"
          >
            Open Chat
          </Link>
          <Link
            href="/models"
            className="home-secondary rounded-xl border px-5 py-3 text-center font-semibold transition"
          >
            Browse Models
          </Link>
          <Link
            href="/settings"
            className="home-secondary rounded-xl border px-5 py-3 text-center font-semibold transition"
          >
            Open Settings
          </Link>
          <Link
            href="/coding"
            className="home-secondary rounded-xl border px-5 py-3 text-center font-semibold transition"
          >
            Open Coding
          </Link>
          <Link
            href="/training"
            className="home-secondary rounded-xl border px-5 py-3 text-center font-semibold transition"
          >
            Training Data
          </Link>
        </div>
      </section>
    </main>
  );
}