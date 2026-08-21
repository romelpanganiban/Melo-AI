"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import {
  analyzeWorkspaceFile,
  APIError,
  CodeAnalysis,
  CodeFile,
  deleteWorkspaceFile,
  generateWorkspaceCode,
  getGitDiff,
  getGitStatus,
  commitGitChanges,
  stageGitFiles,
  readWorkspaceFile,
  reviewWorkspaceFile,
  writeWorkspaceFile,
} from "@/lib/api";

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  return `${(bytes / 1024).toFixed(1)} KB`;
}

export default function CodingPage() {
  const [path, setPath] = useState("backend/services/code_analysis_service.py");
  const [file, setFile] = useState<CodeFile | null>(null);
  const [content, setContent] = useState("");
  const [analysis, setAnalysis] = useState<CodeAnalysis | null>(null);
  const [instruction, setInstruction] = useState("");
  const [assistantResult, setAssistantResult] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [assistantLoading, setAssistantLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [gitStatus, setGitStatus] = useState<{ branch: string; files: { status: string; path: string }[]; count: number } | null>(null);
  const [gitDiff, setGitDiff] = useState("");
  const [commitMessage, setCommitMessage] = useState("");
  const [gitBusy, setGitBusy] = useState(false);
  const [selectedGitPaths, setSelectedGitPaths] = useState<string[]>([]);

  function isGeneratedPath(path: string) {
    return path.endsWith(".db") || /^backend\/data\/.*\.json$/.test(path);
  }

  async function handleInspect(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!path.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const [fileData, analysisData] = await Promise.all([
        readWorkspaceFile(path.trim()),
        analyzeWorkspaceFile(path.trim()),
      ]);
      setFile(fileData);
      setContent(fileData.content);
      setAnalysis(analysisData);
      setAssistantResult(null);
    } catch (err) {
      setFile(null);
      setAnalysis(null);
      setError(err instanceof APIError ? err.message : "Failed to inspect file");
    } finally {
      setLoading(false);
    }
  }

  async function refreshGit() {
    setError(null);
    try {
      const [status, diff] = await Promise.all([getGitStatus(), getGitDiff()]);
      setGitStatus(status);
      setGitDiff(diff.diff);
      setSelectedGitPaths((current) => {
        const available = new Set(status.files.map((file) => file.path));
        const retained = current.filter((path) => available.has(path));
        return retained.length > 0 || current.length > 0
          ? retained
          : status.files
              .filter((file) => !isGeneratedPath(file.path))
              .map((file) => file.path);
      });
    } catch (err) {
      setError(err instanceof APIError ? err.message : "Failed to load Git status");
    }
  }

  async function handleStage() {
    if (!selectedGitPaths.length || !window.confirm(`Stage ${selectedGitPaths.length} selected file${selectedGitPaths.length === 1 ? "" : "s"}?`)) return;
    setGitBusy(true);
    try {
      await stageGitFiles(selectedGitPaths);
      await refreshGit();
    } catch (err) {
      setError(err instanceof APIError ? err.message : "Failed to stage changes");
    } finally {
      setGitBusy(false);
    }
  }

  async function handleCommit() {
    if (!commitMessage.trim() || !window.confirm(`Create commit: ${commitMessage.trim()}?`)) return;
    setGitBusy(true);
    try {
      await commitGitChanges(commitMessage.trim());
      setCommitMessage("");
      await refreshGit();
    } catch (err) {
      setError(err instanceof APIError ? err.message : "Failed to create commit");
    } finally {
      setGitBusy(false);
    }
  }

  async function runAssistant(action: "review" | "generate") {
    if (!file) return;

    setAssistantLoading(true);
    setError(null);
    try {
      const response = action === "review"
        ? await reviewWorkspaceFile(file.path, instruction)
        : await generateWorkspaceCode(file.path, instruction);
      setAssistantResult(response.result);
    } catch (err) {
      setError(
        err instanceof APIError
          ? `${err.message}${err.details?.field ? ` (field: ${String(err.details.field)})` : ""}`
          : "Coding assistant request failed"
      );
    } finally {
      setAssistantLoading(false);
    }
  }

  async function handleSave() {
    if (!file || !window.confirm(`Save changes to ${file.path}?`)) return;

    setSaving(true);
    setError(null);
    try {
      const saved = await writeWorkspaceFile(file.path, content);
      setFile({ ...file, ...saved, content });
      setContent(content);
      setAnalysis(await analyzeWorkspaceFile(saved.path));
    } catch (err) {
      setError(err instanceof APIError ? err.message : "Failed to save file");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!file || !window.confirm(`Delete ${file.path}? This cannot be undone.`)) return;

    setSaving(true);
    setError(null);
    try {
      await deleteWorkspaceFile(file.path);
      setFile(null);
      setAnalysis(null);
      setContent("");
    } catch (err) {
      setError(err instanceof APIError ? err.message : "Failed to delete file");
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="page-shell min-h-screen px-4 py-6 sm:px-6 sm:py-10">
      <div className="mx-auto max-w-7xl space-y-6">
        <header className="glass-panel rounded-2xl p-5 sm:p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-[0.22em] text-teal-800/80">Workspace tools</p>
              <h1 className="brand-title mt-3 text-3xl font-bold text-emerald-950">Coding Assistant</h1>
              <p className="mt-2 max-w-2xl text-sm text-emerald-900/75">Read and understand source files inside the Melo-AI workspace.</p>
            </div>
            <Link href="/chat" className="rounded-lg border border-emerald-900/20 bg-white/70 px-3 py-1.5 text-sm font-medium text-emerald-900 transition hover:bg-white">Back to Chat</Link>
          </div>
        </header>

        <form onSubmit={handleInspect} className="rounded-2xl border border-emerald-900/10 bg-white/80 p-4 shadow-sm sm:p-5">
          <label htmlFor="workspace-path" className="block text-sm font-medium text-emerald-900">Workspace-relative file path</label>
          <div className="mt-2 flex flex-col gap-2 sm:flex-row">
            <input id="workspace-path" value={path} onChange={(event) => setPath(event.target.value)} placeholder="frontend/lib/api.ts" className="min-w-0 flex-1 rounded-lg border border-emerald-900/20 p-2.5 text-sm outline-none transition focus:border-teal-700 focus:ring-2 focus:ring-teal-200" />
            <button type="submit" disabled={loading || !path.trim()} className="rounded-lg bg-teal-700 px-5 py-2.5 font-semibold text-teal-50 transition hover:bg-teal-800 disabled:bg-gray-400">{loading ? "Inspecting..." : "Inspect File"}</button>
          </div>
          <p className="mt-2 text-xs text-emerald-900/60">Supported source and text files are limited to 1 MB. Reads and analysis do not modify files.</p>
        </form>

        <section className="rounded-2xl border border-emerald-900/10 bg-white/80 p-4 shadow-sm sm:p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="font-semibold text-emerald-950">Git Workspace</h2>
              <p className="mt-1 text-xs text-emerald-900/60">Review branch, file status, and working-tree changes.</p>
            </div>
            <button type="button" onClick={() => void refreshGit()} className="rounded-lg bg-emerald-900 px-3 py-2 text-xs font-semibold text-white transition hover:bg-emerald-800">Refresh Git</button>
          </div>
          {gitStatus && (
            <>
              <p className="mt-4 text-sm text-emerald-900/80"><span className="font-semibold">Branch:</span> {gitStatus.branch || "Unknown"} · {gitStatus.count} changed file{gitStatus.count === 1 ? "" : "s"}</p>
              {gitStatus.files.length > 0 && <ul className="mt-3 grid gap-2 text-xs text-emerald-900/75 sm:grid-cols-2">{gitStatus.files.map((file) => <li key={`${file.status}-${file.path}`} className="min-w-0"><label className="flex min-w-0 items-center gap-2"><input type="checkbox" checked={selectedGitPaths.includes(file.path)} onChange={(event) => setSelectedGitPaths((current) => event.target.checked ? [...current, file.path] : current.filter((path) => path !== file.path))} className="shrink-0 accent-teal-700" /><span className="min-w-0 truncate"><span className="mr-2 font-mono font-semibold">{file.status}</span>{file.path}</span></label></li>)}</ul>}
              <pre className="mt-4 max-h-80 overflow-auto whitespace-pre-wrap rounded-lg bg-emerald-950 p-3 text-xs leading-5 text-emerald-50">{gitDiff || "Working tree is clean."}</pre>
              <div className="mt-4 flex flex-col gap-2 border-t border-emerald-900/10 pt-4 sm:flex-row">
                <button type="button" onClick={() => void handleStage()} disabled={gitBusy || selectedGitPaths.length === 0} className="rounded-lg border border-emerald-900/20 px-3 py-2 text-xs font-semibold text-emerald-900 hover:bg-emerald-50 disabled:bg-gray-100">{gitBusy ? "Working..." : `Stage Selected (${selectedGitPaths.length})`}</button>
                <input value={commitMessage} onChange={(event) => setCommitMessage(event.target.value)} placeholder="Commit message" maxLength={200} className="min-w-0 flex-1 rounded-lg border border-emerald-900/20 px-3 py-2 text-xs outline-none focus:border-teal-700 focus:ring-2 focus:ring-teal-200" />
                <button type="button" onClick={() => void handleCommit()} disabled={gitBusy || !commitMessage.trim()} className="rounded-lg bg-emerald-900 px-3 py-2 text-xs font-semibold text-white hover:bg-emerald-800 disabled:bg-gray-400">Commit</button>
              </div>
            </>
          )}
        </section>

        {error && <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}

        {file && analysis && (
          <div className="grid min-w-0 gap-6 lg:grid-cols-[minmax(0,1fr)_18rem]">
            <section className="min-w-0 overflow-hidden rounded-2xl border border-emerald-900/10 bg-[#17231f] shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/10 px-4 py-3 text-xs text-emerald-100/70">
                <span className="truncate">{file.path}</span>
                <span className="flex items-center gap-3">
                  {formatBytes(file.size_bytes)} · {file.line_count} lines
                  <button type="button" onClick={() => void handleSave()} disabled={saving} className="rounded bg-teal-500 px-2 py-1 font-semibold text-white hover:bg-teal-400 disabled:bg-gray-500">{saving ? "Working..." : "Save"}</button>
                  <button type="button" onClick={() => void handleDelete()} disabled={saving} className="rounded bg-red-700 px-2 py-1 font-semibold text-white hover:bg-red-600 disabled:bg-gray-500">Delete</button>
                </span>
              </div>
              <textarea aria-label="File content" value={content} onChange={(event) => setContent(event.target.value)} spellCheck={false} className="min-h-[55vh] w-full resize-y bg-transparent p-4 font-mono text-xs leading-6 text-emerald-50 outline-none sm:text-sm" />
            </section>

            <aside className="min-w-0 space-y-4">
              <section className="rounded-2xl border border-emerald-900/10 bg-white/80 p-4 shadow-sm">
                <h2 className="font-semibold text-emerald-950">AI Assistant</h2>
                <textarea value={instruction} onChange={(event) => setInstruction(event.target.value)} placeholder="e.g. Find error-handling risks" className="mt-3 min-h-24 w-full rounded-lg border border-emerald-900/20 p-2.5 text-sm outline-none transition focus:border-teal-700 focus:ring-2 focus:ring-teal-200" />
                <div className="mt-2 grid grid-cols-2 gap-2">
                  <button type="button" onClick={() => void runAssistant("review")} disabled={assistantLoading} className="rounded-lg border border-teal-700/30 px-2 py-2 text-sm font-semibold text-teal-800 hover:bg-teal-50 disabled:bg-gray-100">Review</button>
                  <button type="button" onClick={() => void runAssistant("generate")} disabled={assistantLoading || !instruction.trim()} className="rounded-lg bg-teal-700 px-2 py-2 text-sm font-semibold text-white hover:bg-teal-800 disabled:bg-gray-400">Generate</button>
                </div>
                {assistantResult && <pre className="mt-3 max-h-72 overflow-auto whitespace-pre-wrap rounded-lg bg-emerald-950 p-3 text-xs leading-5 text-emerald-50">{assistantResult}</pre>}
              </section>
              <section className="rounded-2xl border border-emerald-900/10 bg-white/80 p-4 shadow-sm">
                <h2 className="font-semibold text-emerald-950">File Profile</h2>
                <dl className="mt-3 space-y-2 text-sm text-emerald-900/75">
                  <div className="flex justify-between gap-3"><dt>Language</dt><dd className="font-medium text-emerald-950">{analysis.language}</dd></div>
                  <div className="flex justify-between gap-3"><dt>Imports</dt><dd className="font-medium text-emerald-950">{analysis.imports.length}</dd></div>
                  <div className="flex justify-between gap-3"><dt>Functions</dt><dd className="font-medium text-emerald-950">{analysis.functions.length}</dd></div>
                  <div className="flex justify-between gap-3"><dt>Classes</dt><dd className="font-medium text-emerald-950">{analysis.classes.length}</dd></div>
                </dl>
                {analysis.syntax_error && <p className="mt-3 rounded-lg bg-red-50 p-2 text-xs text-red-700">{analysis.syntax_error}</p>}
              </section>
              <section className="rounded-2xl border border-emerald-900/10 bg-white/80 p-4 shadow-sm">
                <h2 className="font-semibold text-emerald-950">Symbols</h2>
                <p className="mt-3 text-xs font-semibold uppercase tracking-wide text-emerald-900/55">Classes</p>
                <p className="mt-1 break-words text-sm text-emerald-900/75">{analysis.classes.join(", ") || "None detected"}</p>
                <p className="mt-3 text-xs font-semibold uppercase tracking-wide text-emerald-900/55">Functions</p>
                <p className="mt-1 break-words text-sm text-emerald-900/75">{analysis.functions.join(", ") || "None detected"}</p>
              </section>
            </aside>
          </div>
        )}
      </div>
    </main>
  );
}