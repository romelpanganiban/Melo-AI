"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { APIError, createTrainingDataset, getTrainingDatasets, TrainingDataset } from "@/lib/api";

type TrainingMessage = { role: "user" | "assistant"; content: string };

export default function TrainingPage() {
  const [name, setName] = useState("melo-training-data");
  const [messages, setMessages] = useState<TrainingMessage[]>([
    { role: "user", content: "How should I configure this?" },
    { role: "assistant", content: "Describe the goal, constraints, and expected result." },
  ]);
  const [datasets, setDatasets] = useState<TrainingDataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    getTrainingDatasets()
      .then((data) => setDatasets(Array.isArray(data.datasets) ? data.datasets : []))
      .catch((err) => setError(err instanceof APIError ? err.message : "Failed to load datasets"))
      .finally(() => setLoading(false));
  }, []);

  function updateMessage(index: number, field: keyof TrainingMessage, value: string) {
    setMessages((current) => current.map((message, messageIndex) => messageIndex === index ? { ...message, [field]: value } : message));
  }

  function addMessage(role: "user" | "assistant") {
    setMessages((current) => [...current, { role, content: "" }]);
  }

  function removeMessage(index: number) {
    setMessages((current) => current.filter((_, messageIndex) => messageIndex !== index));
  }

  async function saveDataset() {
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const created = await createTrainingDataset(name, [{ messages }]);
      setDatasets((current) => [created, ...current.filter((dataset) => dataset.name !== created.name)]);
      setSuccess(`Saved ${created.name}.jsonl`);
    } catch (err) {
      setError(err instanceof APIError ? err.message : "Failed to save dataset");
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="training-page page-shell min-h-screen px-4 py-6 sm:px-6 sm:py-10">
      <div className="mx-auto max-w-4xl space-y-6">
        <header className="glass-panel rounded-2xl p-5 sm:p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.22em] text-teal-800/80">Fine tuning</p>
              <h1 className="brand-title mt-3 text-3xl font-bold text-emerald-950">Training Dataset</h1>
              <p className="mt-2 text-sm text-emerald-900/75">Prepare validated conversation data before running an Unsloth training job.</p>
            </div>
            <Link href="/chat" className="back-to-chat rounded-lg border px-3 py-1.5 text-sm font-medium transition focus-visible:outline-2 focus-visible:outline-offset-2">Back to Chat</Link>
          </div>
        </header>

        {error && <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}
        {success && <div className="rounded-lg border border-teal-300 bg-teal-50 px-4 py-3 text-sm text-teal-800">{success}</div>}

        <section className="rounded-2xl border border-emerald-900/10 bg-white/80 p-4 shadow-sm sm:p-5">
          <label htmlFor="dataset-name" className="block text-sm font-medium text-emerald-900">Dataset name</label>
          <input id="dataset-name" value={name} onChange={(event) => setName(event.target.value)} className="mt-2 w-full rounded-lg border border-emerald-900/20 p-2.5 text-sm outline-none focus:border-teal-700 focus:ring-2 focus:ring-teal-200" />
          <div className="mt-5 space-y-3">
            {messages.map((message, index) => (
              <div key={index} className="grid gap-2 sm:grid-cols-[8rem_minmax(0,1fr)_auto]">
                <select value={message.role} onChange={(event) => updateMessage(index, "role", event.target.value)} className="rounded-lg border border-emerald-900/20 p-2 text-sm">
                  <option value="user">User</option>
                  <option value="assistant">Assistant</option>
                </select>
                <textarea value={message.content} onChange={(event) => updateMessage(index, "content", event.target.value)} placeholder="Message content" className="min-h-20 rounded-lg border border-emerald-900/20 p-2 text-sm outline-none focus:border-teal-700 focus:ring-2 focus:ring-teal-200" />
                <button
                  type="button"
                  onClick={() => removeMessage(index)}
                  className="self-start rounded-lg border border-red-300 px-3 py-2 text-xs font-semibold text-red-700 transition hover:bg-red-50"
                  aria-label={`Remove message ${index + 1}`}
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <button type="button" onClick={() => addMessage("user")} className="training-add-button rounded-lg border px-3 py-2 text-xs font-semibold transition duration-150">Add User Message</button>
            <button type="button" onClick={() => addMessage("assistant")} className="training-add-button rounded-lg border px-3 py-2 text-xs font-semibold transition duration-150">Add Assistant Message</button>
            <button type="button" onClick={() => void saveDataset()} disabled={saving || loading} className="rounded-lg bg-teal-700 px-4 py-2 text-xs font-semibold text-white hover:bg-teal-800 disabled:bg-gray-400">{saving ? "Saving..." : "Save JSONL Dataset"}</button>
          </div>
        </section>

        <section className="rounded-2xl border border-emerald-900/10 bg-white/80 p-4 shadow-sm sm:p-5">
          <h2 className="font-semibold text-emerald-950">Saved datasets</h2>
          {datasets.length === 0 ? <p className="mt-3 text-sm text-emerald-900/60">No datasets saved yet.</p> : <ul className="mt-3 space-y-2 text-sm text-emerald-900/75">{datasets.map((dataset) => <li key={dataset.name} className="flex flex-wrap justify-between gap-2 rounded-lg bg-emerald-50 px-3 py-2"><span>{dataset.name}.jsonl</span><span className="text-xs">{dataset.size_bytes ? `${dataset.size_bytes} bytes` : `${dataset.example_count ?? 0} examples`}</span></li>)}</ul>}
        </section>
      </div>
    </main>
  );
}