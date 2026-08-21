import Link from "next/link";

export default function Home() {
  return (
    <main className="page-shell flex min-h-screen items-center justify-center px-6 py-14">
      <section className="glass-panel w-full max-w-4xl rounded-3xl p-8 md:p-12">
        <p className="text-xs uppercase tracking-[0.25em] text-teal-800/80">Local-first intelligence</p>
        <h1 className="brand-title mt-4 text-4xl font-bold leading-tight text-emerald-950 md:text-6xl">
          Melo-AI is your private workspace companion.
        </h1>
        <p className="mt-5 max-w-2xl text-base text-emerald-900/80 md:text-lg">
          Chat, tune your model, and keep everything local on your own machine with a fast, focused interface.
        </p>

        <div className="mt-8 flex flex-col gap-3 sm:flex-row">
          <Link
            href="/chat"
            className="rounded-xl bg-teal-700 px-5 py-3 text-center font-semibold text-teal-50 transition hover:bg-teal-800"
          >
            Open Chat
          </Link>
          <Link
            href="/models"
            className="rounded-xl border border-teal-800/30 bg-white/70 px-5 py-3 text-center font-semibold text-teal-900 transition hover:bg-white"
          >
            Browse Models
          </Link>
          <Link
            href="/settings"
            className="rounded-xl border border-emerald-900/20 bg-emerald-100/50 px-5 py-3 text-center font-semibold text-emerald-900 transition hover:bg-emerald-100"
          >
            Open Settings
          </Link>
          <Link
            href="/coding"
            className="rounded-xl border border-emerald-900/20 bg-emerald-100/50 px-5 py-3 text-center font-semibold text-emerald-900 transition hover:bg-emerald-100"
          >
            Open Coding
          </Link>
        </div>
      </section>
    </main>
  );
}