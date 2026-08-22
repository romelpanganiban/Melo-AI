"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { APIError, getModels, getSettings, updateSettings, InstalledModel } from "@/lib/api";

export default function ModelsPage() {
  const [models, setModels] = useState<InstalledModel[]>([]);
  const [selectedModel, setSelectedModel] = useState("");
  const [provider, setProvider] = useState("ollama");
  const [temperature, setTemperature] = useState(0.7);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    async function loadModels() {
      try {
        const [modelData, settings] = await Promise.all([getModels(), getSettings()]);
        const availableModels = Array.isArray(modelData.models) ? modelData.models : [];
        setModels(availableModels);
        setSelectedModel(settings.model || availableModels[0]?.name || "");
        setProvider(settings.provider || "ollama");
        setTemperature(settings.temperature ?? 0.7);
      } catch (err) {
        setError(err instanceof APIError ? err.message : "Failed to load models");
      } finally {
        setLoading(false);
      }
    }

    void loadModels();
  }, []);

  async function handleSave() {
    if (!selectedModel) return;

    try {
      setSaving(true);
      setError(null);
      await updateSettings({ model: selectedModel, provider, temperature });
      setSuccess(true);
    } catch (err) {
      setError(err instanceof APIError ? err.message : "Failed to save model");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <main className="models-page page-shell flex min-h-screen items-center justify-center px-6 py-10" aria-busy="true">
        <div className="settings-loading rounded-2xl border p-8 text-center shadow-[0_18px_40px_rgba(0,0,0,0.2)]">
          <div className="settings-loading-spinner mx-auto h-10 w-10 animate-spin rounded-full border-2" />
          <p className="settings-loading-title mt-4 text-base font-semibold">Loading installed models</p>
          <p className="settings-loading-copy mt-1 text-sm">Checking the local Ollama service...</p>
        </div>
      </main>
    );
  }

  return (
    <main className="models-page page-shell min-h-screen px-6 py-10">
      <div className="mx-auto max-w-2xl space-y-6">
        <header className="glass-panel rounded-2xl p-6">
          <p className="text-xs uppercase tracking-[0.22em] text-teal-800/80">Ollama</p>
          <h1 className="brand-title mt-3 text-3xl font-bold text-emerald-950">Installed Models</h1>
          <p className="mt-2 text-sm text-emerald-900/75">Choose a model already installed on this machine.</p>
          <Link href="/chat" className="back-to-chat mt-4 inline-flex rounded-lg border px-3 py-1.5 text-sm font-medium transition focus-visible:outline-2 focus-visible:outline-offset-2">Back to Chat</Link>
        </header>

        {error && <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-red-700">{error}</div>}
        {success && <div className="rounded-lg border border-teal-300 bg-teal-50 px-4 py-3 text-teal-800">Model saved successfully.</div>}

        <section className="rounded-2xl border border-emerald-900/10 bg-white/80 p-5 shadow-sm">
          {models.length === 0 ? (
            <p className="text-sm text-emerald-900/75">No Ollama models were found. Install one with <code>ollama pull qwen3:8b</code>.</p>
          ) : (
            <>
              <label htmlFor="model" className="mb-2 block text-sm font-medium text-emerald-900">Model</label>
              <select id="model" value={selectedModel} onChange={(event) => setSelectedModel(event.target.value)} className="w-full rounded-lg border border-emerald-900/20 p-2.5 text-sm outline-none transition focus:border-teal-700 focus:ring-2 focus:ring-teal-200">
                {models.map((model) => <option key={model.name} value={model.name}>{model.name}</option>)}
              </select>
              <button onClick={() => void handleSave()} disabled={saving || !selectedModel} className="mt-5 rounded-xl bg-teal-700 px-6 py-2.5 font-semibold text-teal-50 transition hover:bg-teal-800 disabled:bg-gray-400">
                {saving ? "Saving..." : "Use This Model"}
              </button>
            </>
          )}
        </section>
      </div>
    </main>
  );
}