"use client";

import { useCallback, useEffect, useState } from "react";
import {
  APIError,
  DocumentChunk,
  DocumentSummary,
  deleteDocument,
  createCollection,
  getCollections,
  getDocumentChunks,
  getSessionDocuments,
  searchDocuments,
  type DocumentSearchResult,
  uploadDocument,
  uploadDocumentFile,
} from "@/lib/api";
import { FileText, Search, Upload } from "lucide-react";

type Props = {
  sessionId: string | null;
  onCollectionChange?: (collectionId?: string) => void;
};

export default function DocumentsPanel({ sessionId, onCollectionChange }: Props) {
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [chunkMap, setChunkMap] = useState<Record<string, DocumentChunk[]>>({});
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [filename, setFilename] = useState("");
  const [content, setContent] = useState("");
  const [fileType, setFileType] = useState<"txt" | "pdf" | "docx">("txt");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<DocumentSearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [collections, setCollections] = useState<{ id: string; name: string }[]>([]);
  const [collectionId, setCollectionId] = useState("");
  const [newCollectionName, setNewCollectionName] = useState("");

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

  useEffect(() => {
    void getCollections().then((response) => {
      setCollections(response.collections || []);
      if (response.collections?.[0]) setCollectionId((current) => current || response.collections[0].id);
    }).catch(() => setCollections([]));
  }, []);

  useEffect(() => {
    onCollectionChange?.(collectionId || undefined);
  }, [collectionId, onCollectionChange]);

  async function handleCreateCollection() {
    if (!newCollectionName.trim()) return;
    try {
      const collection = await createCollection(newCollectionName.trim());
      setCollections((current) => [...current, collection]);
      setCollectionId(collection.id);
      setNewCollectionName("");
    } catch (err) {
      setError(err instanceof APIError ? err.message : "Failed to create collection");
    }
  }

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
        collection_id: collectionId || undefined,
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
      await uploadDocumentFile(selectedFile, sessionId, collectionId || undefined);
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

  async function handleSearch() {
    if (!sessionId || !searchQuery.trim()) return;
    setSearching(true);
    setError(null);
    try {
      const response = await searchDocuments(sessionId, searchQuery, 5, collectionId || undefined);
      setSearchResults(response.results);
    } catch (err) {
      setError(err instanceof APIError ? err.message : "Failed to search documents");
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  }

  return (
    <aside className="documents-panel mx-3 mb-3 flex min-w-0 max-w-full flex-col overflow-hidden rounded-2xl border border-white/10 bg-[#111916]/95 p-4 shadow-[0_14px_36px_rgba(0,0,0,0.22)] md:mx-4 md:h-full md:w-[360px] md:min-w-[320px] md:max-w-[380px]">
      <h2 className="brand-title flex items-center gap-2 text-lg font-semibold text-slate-100"><FileText size={18} aria-hidden="true" /> Documents</h2>
      <p className="mt-1 text-xs text-slate-400/70">
        Upload documents to enhance AI responses with your knowledge base.
      </p>

      {error && (
        <div className="mt-3 rounded-lg border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700">
          <strong>⚠️ Upload Failed:</strong> {error}
        </div>
      )}

      {!sessionId ? (
        <div className="mt-4 rounded-lg border border-teal-300/10 bg-teal-950/35 p-3 text-sm text-teal-100/75">
          ℹ️ Select a chat session first to add documents.
        </div>
      ) : (
        <>
          <div className="mt-4 space-y-3">
            <div>
              <label htmlFor="knowledge-collection" className="mb-1 block text-xs font-semibold text-slate-300">Knowledge collection</label>
              <select id="knowledge-collection" value={collectionId} onChange={(event) => setCollectionId(event.target.value)} className="w-full rounded-lg border border-white/15 bg-white/5 p-2 text-sm text-slate-100">
                <option value="">All session documents</option>
                {collections.map((collection) => <option key={collection.id} value={collection.id}>{collection.name}</option>)}
              </select>
              <div className="mt-2 flex gap-2">
                <input value={newCollectionName} onChange={(event) => setNewCollectionName(event.target.value)} placeholder="New collection name" className="min-w-0 flex-1 rounded-lg border border-white/15 bg-white/5 p-2 text-xs text-slate-100" />
                <button type="button" onClick={() => void handleCreateCollection()} disabled={!newCollectionName.trim()} className="rounded-lg bg-white/10 px-3 text-xs text-slate-200 disabled:opacity-40">Create</button>
              </div>
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-300">
                📄 Filename
              </label>
              <input
                type="text"
                value={filename}
                onChange={(e) => setFilename(e.target.value)}
                placeholder="e.g., company_guide.txt"
                className="w-full rounded-lg border border-white/15 bg-white/5 p-2 text-sm text-slate-100 outline-none focus:border-teal-400 focus:ring-1 focus:ring-teal-400/30"
              />
              <p className="mt-1 text-xs text-slate-400/55">
                Give your document a descriptive name
              </p>
            </div>

            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-300">
                📋 Document Type
              </label>
              <select
                value={fileType}
                onChange={(e) => setFileType(e.target.value as "txt" | "pdf" | "docx")}
                className="w-full rounded-lg border border-white/15 bg-white/5 p-2 text-sm text-slate-100 outline-none focus:border-teal-400 focus:ring-1 focus:ring-teal-400/30"
              >
                <option value="txt">📝 Plain Text (.txt)</option>
                <option value="pdf">📕 PDF (.pdf)</option>
                <option value="docx">📗 Word Doc (.docx)</option>
              </select>
            </div>

            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-300">
                📎 Upload a file
              </label>
              <input
                type="file"
                accept=".txt,.pdf,.docx"
                onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
                className="document-file-input w-full min-w-0 text-xs text-slate-300"
              />
              <button
                type="button"
                onClick={() => void handleFileUpload()}
                disabled={uploading || !selectedFile}
                className="mt-2 w-full rounded-lg bg-teal-500/15 px-3 py-2 text-xs font-semibold text-teal-200 transition hover:bg-teal-500/25 disabled:cursor-not-allowed disabled:bg-white/5 disabled:text-white/30"
              >
                <span className="inline-flex items-center gap-2"><Upload size={14} aria-hidden="true" /> {uploading ? "Uploading file..." : "Upload selected file"}</span>
              </button>
            </div>

            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-300">
                ✍️ Content
              </label>
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                rows={5}
                placeholder="Paste or type your document content here..."
                className="w-full resize-none rounded-lg border border-white/15 bg-white/5 p-2 text-sm text-slate-100 outline-none focus:border-teal-400 focus:ring-1 focus:ring-teal-400/30"
              />
              <p className="mt-1 text-xs text-slate-400/55">
                {content.length} characters
              </p>
            </div>

            <button
              type="button"
              onClick={handleUpload}
              disabled={uploading || !filename.trim() || !content.trim()}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-teal-600 px-3 py-2.5 text-sm font-semibold text-white transition hover:bg-teal-500 disabled:cursor-not-allowed disabled:bg-white/10 disabled:text-white/35"
            >
              {uploading ? "📤 Uploading..." : "📤 Upload Document"}
            </button>

            <div className="border-t border-white/10 pt-3">
              <label htmlFor="document-search" className="mb-1 flex items-center gap-2 text-xs font-semibold text-slate-300"><Search size={14} aria-hidden="true" /> Search knowledge</label>
              <div className="flex gap-2">
                <input id="document-search" value={searchQuery} onChange={(event) => setSearchQuery(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") void handleSearch(); }} placeholder="Search your documents" className="min-w-0 flex-1 rounded-lg border border-white/15 bg-white/5 p-2 text-sm text-slate-100 outline-none focus:border-teal-400" />
                <button type="button" onClick={() => void handleSearch()} disabled={searching || !searchQuery.trim()} aria-label="Search documents" className="rounded-lg bg-teal-500/20 px-3 text-teal-200 disabled:opacity-40"><Search size={16} aria-hidden="true" /></button>
              </div>
              {searchResults.length > 0 && <ul className="mt-3 space-y-2">{searchResults.map((result, index) => <li key={`${result.filename}-${result.chunk_index ?? index}`} className="rounded-lg border border-white/10 bg-white/5 p-2 text-xs text-slate-300"><p className="font-semibold text-teal-200">{result.filename} <span className="font-normal text-slate-400">{result.relevance}%</span></p><p className="mt-1 line-clamp-3">{result.content}</p></li>)}</ul>}
            </div>

            {documents.length === 0 && !uploading && (
              <div className="mt-3 rounded bg-white/5 p-3 text-center text-xs text-slate-400/60">
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
                      {chunkMap[doc.id].map((chunk) => (
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
