"use client";

import { useCallback, useEffect, useState } from "react";
import {
  APIError,
  DocumentChunk,
  DocumentSummary,
  deleteDocument,
  getDocumentChunks,
  getSessionDocuments,
  uploadDocument,
} from "@/lib/api";

type Props = {
  sessionId: string | null;
};

export default function DocumentsPanel({ sessionId }: Props) {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [chunkMap, setChunkMap] = useState<Record<string, DocumentChunk[]>>({});
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [filename, setFilename] = useState("");
  const [content, setContent] = useState("");
  const [fileType, setFileType] = useState<"txt" | "pdf" | "docx">("txt");

  const loadDocuments = useCallback(async () => {
    if (!sessionId) {
      setDocuments([]);
      setChunkMap({});
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await getSessionDocuments(sessionId);
      setDocuments(response.documents || []);
      setChunkMap({});
    } catch (err) {
      const message =
        err instanceof APIError
          ? err.message
          : "Failed to load documents";
      setError(message);
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      void loadDocuments();
    }, 0);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [loadDocuments]);

  async function handleUpload() {
    if (!sessionId) {
      setError("Select a session first");
      return;
    }

    if (!filename.trim()) {
      setError("Filename is required");
      return;
    }

    if (!content.trim()) {
      setError("Document content is required");
      return;
    }

    setUploading(true);
    setError(null);

    try {
      await uploadDocument({
        filename: filename.trim(),
        file_type: fileType,
        content: content.trim(),
        session_id: sessionId,
      });

      setFilename("");
      setContent("");
      setFileType("txt");
      await loadDocuments();
    } catch (err) {
      const message =
        err instanceof APIError
          ? err.message
          : "Failed to upload document";
      setError(message);
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(documentId: string) {
    setError(null);

    try {
      await deleteDocument(documentId);
      await loadDocuments();
    } catch (err) {
      const message =
        err instanceof APIError
          ? err.message
          : "Failed to delete document";
      setError(message);
    }
  }

  async function handleToggleChunks(documentId: string) {
    if (chunkMap[documentId]) {
      setChunkMap((prev) => {
        const next = { ...prev };
        delete next[documentId];
        return next;
      });
      return;
    }

    setError(null);

    try {
      const response = await getDocumentChunks(documentId);
      setChunkMap((prev) => ({
        ...prev,
        [documentId]: response.chunks || [],
      }));
    } catch (err) {
      const message =
        err instanceof APIError
          ? err.message
          : "Failed to fetch chunks";
      setError(message);
    }
  }

  return (
    <aside className="mx-3 mb-3 rounded-2xl border border-emerald-900/10 bg-white/85 p-4 shadow-sm md:mx-4 md:w-[360px] md:min-w-[320px] md:max-w-[380px]">
      <h2 className="brand-title text-lg font-semibold text-emerald-950">Documents</h2>
      <p className="mt-1 text-xs text-emerald-900/60">
        Upload text now, then add PDF and DOCX parsing once package install is available.
      </p>

      {error && (
        <div className="mt-3 rounded-lg border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      {!sessionId ? (
        <div className="mt-4 rounded-lg border border-emerald-900/10 bg-emerald-50/60 p-3 text-sm text-emerald-900/75">
          Select a session to manage documents.
        </div>
      ) : (
        <>
          <div className="mt-4 space-y-2">
            <input
              type="text"
              value={filename}
              onChange={(e) => setFilename(e.target.value)}
              placeholder="Filename (e.g. notes.txt)"
              className="w-full rounded-lg border border-emerald-900/20 p-2 text-sm outline-none focus:border-teal-700"
            />

            <select
              value={fileType}
              onChange={(e) => setFileType(e.target.value as "txt" | "pdf" | "docx")}
              className="w-full rounded-lg border border-emerald-900/20 p-2 text-sm outline-none focus:border-teal-700"
            >
              <option value="txt">txt</option>
              <option value="pdf">pdf</option>
              <option value="docx">docx</option>
            </select>

            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={4}
              placeholder="Paste document content..."
              className="w-full rounded-lg border border-emerald-900/20 p-2 text-sm outline-none focus:border-teal-700"
            />

            <button
              type="button"
              onClick={handleUpload}
              disabled={uploading}
              className="w-full rounded-lg bg-teal-700 px-3 py-2 text-sm font-semibold text-teal-50 transition hover:bg-teal-800 disabled:bg-gray-400"
            >
              {uploading ? "Uploading..." : "Upload Document"}
            </button>
          </div>

          <div className="mt-4 max-h-[340px] space-y-2 overflow-y-auto pr-1">
            {loading ? (
              <p className="text-sm text-emerald-900/70">Loading documents...</p>
            ) : documents.length === 0 ? (
              <p className="text-sm text-emerald-900/65">No documents in this session yet.</p>
            ) : (
              documents.map((doc) => (
                <div key={doc.id} className="rounded-lg border border-emerald-900/10 bg-white/75 p-3">
                  <p className="truncate text-sm font-semibold text-emerald-950">{doc.filename}</p>
                  <p className="mt-1 text-xs text-emerald-900/65">
                    Type: {doc.file_type} | Chunks: {doc.chunk_count ?? 0}
                  </p>

                  <div className="mt-2 flex gap-2">
                    <button
                      type="button"
                      onClick={() => void handleToggleChunks(doc.id)}
                      className="rounded-md border border-emerald-900/20 px-2 py-1 text-xs font-medium text-emerald-900 hover:bg-emerald-100"
                    >
                      {chunkMap[doc.id] ? "Hide Chunks" : "View Chunks"}
                    </button>
                    <button
                      type="button"
                      onClick={() => void handleDelete(doc.id)}
                      className="rounded-md border border-red-300 px-2 py-1 text-xs font-medium text-red-700 hover:bg-red-50"
                    >
                      Delete
                    </button>
                  </div>

                  {chunkMap[doc.id] && (
                    <div className="mt-2 space-y-1 rounded-md border border-emerald-900/10 bg-emerald-50/60 p-2">
                      {chunkMap[doc.id].map((chunk) => (
                        <div key={chunk.id} className="text-xs text-emerald-900/80">
                          <p className="font-semibold">Chunk {chunk.chunk_index + 1}</p>
                          <p className="line-clamp-3">{chunk.content}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </>
      )}
    </aside>
  );
}
