"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getSettings, updateSettings, APIError } from "@/lib/api";
import { useTheme, type Theme } from "@/components/ThemeProvider";

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const [model, setModel] = useState("");
  const [provider, setProvider] = useState("");
  const [temperature, setTemperature] = useState(0.7);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Load settings on mount
  useEffect(() => {
    async function loadSettings() {
      try {
        setError(null);
        const settings = await getSettings();
        setModel(settings.model || "qwen3:8b");
        setProvider(settings.provider || "ollama");
        setTemperature(settings.temperature || 0.7);
      } catch (err) {
        const message = err instanceof APIError ? err.message : "Failed to load settings";
        setError(message);
      } finally {
        setLoading(false);
      }
    }

    loadSettings();
  }, []);

  // Handle save
  async function handleSave() {
    try {
      setSaving(true);
      setError(null);
      setSuccess(false);

      await updateSettings({
        model,
        provider,
        temperature,
      });

      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      const message = err instanceof APIError ? err.message : "Failed to save settings";
      setError(message);
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="settings-page page-shell flex min-h-screen items-center justify-center px-6 py-10" aria-busy="true">
        <div className="settings-loading rounded-2xl border p-8 text-center shadow-[0_18px_40px_rgba(0,0,0,0.2)]">
          <div className="settings-loading-spinner mx-auto h-10 w-10 animate-spin rounded-full border-2" />
          <p className="settings-loading-title mt-4 text-base font-semibold">Loading your settings</p>
          <p className="settings-loading-copy mt-1 text-sm">Connecting to the local configuration store...</p>
        </div>
      </div>
    );
  }

  return (
    <main className="settings-page page-shell min-h-screen px-6 py-10">
      <div className="mx-auto max-w-2xl space-y-6">
        <header className="glass-panel rounded-2xl p-6">
          <p className="text-xs uppercase tracking-[0.22em] text-teal-800/80">Configuration</p>
          <h1 className="brand-title mt-3 text-3xl font-bold text-emerald-950">Model Settings</h1>
          <p className="mt-2 text-sm text-emerald-900/75">Tune how Melo responds and which provider/model pair to use.</p>
          <Link
            href="/chat"
            className="back-to-chat mt-4 inline-flex rounded-lg border px-3 py-1.5 text-sm font-medium transition focus-visible:outline-2 focus-visible:outline-offset-2"
          >
            Back to Chat
          </Link>
        </header>

        {error && (
          <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-red-700">
            {error}
          </div>
        )}

        {success && (
          <div className="rounded-lg border border-teal-300 bg-teal-50 px-4 py-3 text-teal-800">
            Settings saved successfully!
          </div>
        )}

        <section className="rounded-2xl border border-emerald-900/10 bg-white/80 p-5 shadow-sm">
          <div className="space-y-4">
            <div>
              <label className="mb-2 block text-sm font-medium text-emerald-900">
                Appearance
              </label>
              <select
                value={theme}
                onChange={(e) => setTheme(e.target.value as Theme)}
                className="w-full rounded-lg border border-emerald-900/20 p-2.5 text-sm outline-none transition focus:border-teal-700 focus:ring-2 focus:ring-teal-200"
              >
                <option value="dark">Dark mode</option>
                <option value="light">Light mode</option>
              </select>
              <p className="mt-1 text-xs text-emerald-900/60">
                Choose how Melo-AI looks across the workspace.
              </p>
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-emerald-900">
                Model Name
              </label>
              <input
                type="text"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                placeholder="e.g., qwen3:8b"
                className="w-full rounded-lg border border-emerald-900/20 p-2.5 text-sm outline-none transition focus:border-teal-700 focus:ring-2 focus:ring-teal-200"
              />
              <p className="mt-1 text-xs text-emerald-900/60">
                The AI model to use (must be installed in Ollama)
              </p>
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-emerald-900">
                Provider
              </label>
              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
                className="w-full rounded-lg border border-emerald-900/20 p-2.5 text-sm outline-none transition focus:border-teal-700 focus:ring-2 focus:ring-teal-200"
              >
                <option value="ollama">Ollama</option>
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic</option>
              </select>
              <p className="mt-1 text-xs text-emerald-900/60">
                The AI provider to use
              </p>
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-emerald-900">
                Temperature: {temperature.toFixed(2)}
              </label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={temperature}
                onChange={(e) => setTemperature(Number(e.target.value))}
                className="w-full accent-teal-700"
              />
              <p className="mt-1 text-xs text-emerald-900/60">
                Higher values (closer to 2) make output more random. Lower values (closer to 0) make it more focused.
              </p>
            </div>
          </div>

          <button
            onClick={handleSave}
            disabled={saving}
            className="mt-6 rounded-xl bg-teal-700 px-6 py-2.5 font-semibold text-teal-50 transition hover:bg-teal-800 disabled:bg-gray-400"
          >
            {saving ? "Saving..." : "Save Settings"}
          </button>
        </section>
      </div>
    </main>
  );
}