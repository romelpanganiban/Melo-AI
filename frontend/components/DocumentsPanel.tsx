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
  uploadDocumentFile,
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
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

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

  async function handleFileUpload() {
    if (!sessionId || !selectedFile) {
      setError("Select a PDF, DOCX, or TXT file first");
      return;
    }

    setUploading(true);
    setError(null);

    try {
      await uploadDocumentFile(selectedFile, sessionId);
      setSelectedFile(null);
      await loadDocuments();
    } catch (err) {
      setError(err instanceof APIError ? err.message : "Failed to upload document file");
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
    <aside className="mx-3 mb-3 flex min-w-0 max-w-full flex-col overflow-hidden rounded-2xl border border-emerald-900/10 bg-white/85 p-4 shadow-sm md:mx-4 md:h-full md:w-[360px] md:min-w-[320px] md:max-w-[380px]">
      <h2 className="brand-title text-lg font-semibold text-emerald-950">Documents</h2>
      <p className="mt-1 text-xs text-emerald-900/60">
        Upload documents to enhance AI responses with your knowledge base.
      </p>

      {error && (
        <div className="mt-3 rounded-lg border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700">
          <strong>⚠️ Upload Failed:</strong> {error}
        </div>
      )}

      {!sessionId ? (
        <div className="mt-4 rounded-lg border border-emerald-900/10 bg-emerald-50/60 p-3 text-sm text-emerald-900/75">
          ℹ️ Select a chat session first to add documents.
        </div>
      ) : (
        <>
          <div className="mt-4 space-y-3">
            <div>
              <label className="block text-xs font-semibold text-emerald-900 mb-1">
                📄 Filename
              </label>
              <input
                type="text"
                value={filename}
                onChange={(e) => setFilename(e.target.value)}
                placeholder="e.g., company_guide.txt"
                className="w-full rounded-lg border border-emerald-900/20 p-2 text-sm outline-none focus:border-teal-700 focus:ring-1 focus:ring-teal-200"
              />
              <p className="mt-1 text-xs text-emerald-900/50">
                Give your document a descriptive name
              </p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-emerald-900 mb-1">
                📋 Document Type
              </label>
              <select
                value={fileType}
                onChange={(e) => setFileType(e.target.value as "txt" | "pdf" | "docx")}
                className="w-full rounded-lg border border-emerald-900/20 p-2 text-sm outline-none focus:border-teal-700 focus:ring-1 focus:ring-teal-200"
              >
                <option value="txt">📝 Plain Text (.txt)</option>
                <option value="pdf">📕 PDF (.pdf)</option>
                <option value="docx">📗 Word Doc (.docx)</option>
              </select>
            </div>

            <div>
              <label className="mb-1 block text-xs font-semibold text-emerald-900">
                📎 Upload a file
              </label>
              <input
                type="file"
                accept=".txt,.pdf,.docx"
                onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
                className="w-full min-w-0 text-xs text-emerald-900 file:mr-2 file:rounded-md file:border-0 file:bg-emerald-100 file:px-2 file:py-1.5 file:text-xs file:font-semibold file:text-emerald-800"
              />
              <button
                type="button"
                onClick={() => void handleFileUpload()}
                disabled={uploading || !selectedFile}
                className="mt-2 w-full rounded-lg bg-emerald-100 px-3 py-2 text-xs font-semibold text-emerald-800 transition hover:bg-emerald-200 disabled:cursor-not-allowed disabled:bg-gray-200 disabled:text-gray-500"
              >
                {uploading ? "Uploading file..." : "Upload selected file"}
              </button>
            </div>

            <div>
              <label className="block text-xs font-semibold text-emerald-900 mb-1">
                ✍️ Content
              </label>
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                rows={5}
                placeholder="Paste or type your document content here..."
                className="w-full rounded-lg border border-emerald-900/20 p-2 text-sm outline-none focus:border-teal-700 focus:ring-1 focus:ring-teal-200 resize-none"
              />
              <p className="mt-1 text-xs text-emerald-900/50">
                {content.length} characters
              </p>
            </div>

            <button
              type="button"
              onClick={handleUpload}
              disabled={uploading || !filename.trim() || !content.trim()}
              className="w-full rounded-lg bg-teal-700 px-3 py-2.5 text-sm font-semibold text-teal-50 transition hover:bg-teal-800 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {uploading ? "📤 Uploading..." : "📤 Upload Document"}
            </button>

            {documents.length === 0 && !uploading && (
              <div className="mt-3 text-center text-xs text-emerald-900/50 p-3 rounded bg-emerald-50">
                No documents yet. Upload one to get started!
              </div>
            )}
          </div>

          <div className="mt-6 min-h-0 min-w-0 max-w-full space-y-2 overflow-x-hidden overflow-y-auto pr-1 md:flex-1">
            <h3 className="text-xs font-semibold text-emerald-900 mb-2">
              📚 Documents in this Session
            </h3>
            
            {loading ? (
              <p className="text-sm text-emerald-900/70">⏳ Loading documents...</p>
            ) : documents.length === 0 ? (
              <p className="text-sm text-emerald-900/65">✨ No documents yet. Upload one above!</p>
            ) : (
              documents.map((doc) => (
                <div key={doc.id} className="min-w-0 max-w-full overflow-hidden rounded-lg border border-emerald-900/10 bg-gradient-to-r from-white to-emerald-50/30 p-3 hover:border-emerald-900/20 transition">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="truncate text-sm font-semibold text-emerald-950" title={doc.filename}>
                        📄 {doc.filename}
                      </p>
                      <p className="mt-1 text-xs text-emerald-900/65">
                        {doc.file_type.toUpperCase()} • {doc.chunk_count ?? 0} chunk{(doc.chunk_count ?? 0) !== 1 ? 's' : ''}
                      </p>
                    </div>
                  </div>

                  <div className="mt-3 flex min-w-0 gap-2">
                    <button
                      type="button"
                      onClick={() => void handleToggleChunks(doc.id)}
                      className="min-w-0 flex-1 rounded-md bg-emerald-100 px-2.5 py-1.5 text-xs font-medium text-emerald-700 transition hover:bg-emerald-200"
                    >
                      {chunkMap[doc.id] ? "📋 Hide Chunks" : "📖 View Chunks"}
                    </button>
                    <button
                      type="button"
                      onClick={() => void handleDelete(doc.id)}
                      className="shrink-0 rounded-md bg-red-100 px-2.5 py-1.5 text-xs font-medium text-red-700 transition hover:bg-red-200"
                      title="Delete this document"
                    >
                      🗑️
                    </button>
                  </div>

                  {chunkMap[doc.id] && (
                    <div className="mt-3 min-w-0 max-w-full space-y-2 overflow-x-hidden overflow-y-auto rounded-md border border-emerald-900/10 bg-emerald-50/80 p-2.5 max-h-[200px]">
                      <p className="text-xs font-semibold text-emerald-900 mb-2">
                        📑 Chunks ({chunkMap[doc.id].length})
                      </p>
                      {chunkMap[doc.id].map((chunk, idx) => (
                        <div key={chunk.id} className="min-w-0 max-w-full break-words border-l-2 border-teal-600 py-1 pl-2 text-xs text-emerald-900/80 [overflow-wrap:anywhere]">
                          <p className="font-semibold text-emerald-900">Chunk {chunk.chunk_index + 1}</p>
                          <p className="line-clamp-2 text-emerald-900/70 mt-0.5">{chunk.content}</p>
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
