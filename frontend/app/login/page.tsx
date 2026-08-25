"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { APIError, login, register } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isRegistering, setIsRegistering] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      if (isRegistering) {
        await register(email, password);
      } else {
        await login(email, password);
      }
      router.replace("/chat");
    } catch (caught) {
      setError(caught instanceof APIError ? caught.message : "Unable to connect to Melo-AI");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="page-shell flex min-h-screen items-center justify-center px-6 py-14">
      <section className="glass-panel w-full max-w-md rounded-3xl p-8">
        <p className="home-eyebrow text-xs uppercase tracking-[0.25em]">Private workspace</p>
        <h1 className="brand-title mt-3 text-4xl font-bold">{isRegistering ? "Create your account" : "Welcome back"}</h1>
        <p className="mt-3 text-sm opacity-75">Sign in to access your Melo-AI sessions and knowledge.</p>
        <form className="mt-8 space-y-4" onSubmit={handleSubmit}>
          <label className="block text-sm font-medium">
            Email
            <input className="mt-2 w-full rounded-xl border px-4 py-3" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </label>
          <label className="block text-sm font-medium">
            Password
            <input className="mt-2 w-full rounded-xl border px-4 py-3" type="password" minLength={12} value={password} onChange={(event) => setPassword(event.target.value)} required />
          </label>
          {error && <p className="rounded-xl border border-red-300 px-4 py-3 text-sm text-red-700">{error}</p>}
          <button className="w-full rounded-xl bg-teal-600 px-5 py-3 font-semibold text-white transition hover:bg-teal-500 disabled:opacity-50" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Please wait..." : isRegistering ? "Create account" : "Sign in"}
          </button>
        </form>
        <button className="mt-5 text-sm font-medium underline" type="button" onClick={() => { setIsRegistering(!isRegistering); setError(null); }}>
          {isRegistering ? "Already have an account? Sign in" : "Need an account? Register"}
        </button>
      </section>
    </main>
  );
}