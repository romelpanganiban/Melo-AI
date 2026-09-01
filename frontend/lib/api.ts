/**
 * API Error types
 */
export class APIError extends Error {
  constructor(
    public statusCode: number,
    public errorCode: string,
    message: string,
    public details?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'APIError';
  }
}

/**
 * Get API base URL from environment or use default
 * NEXT_PUBLIC_API_URL is injected by Next.js at build time for NEXT_PUBLIC_ prefixed vars
 */
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

const AUTH_TOKEN_KEY = 'melo_access_token';
const WORKSPACE_ID_KEY = 'melo_workspace_id';
const USER_EMAIL_KEY = 'melo_user_email';

export function getAccessToken(): string | null {
  return typeof window === 'undefined' ? null : window.localStorage.getItem(AUTH_TOKEN_KEY);
}

export function setAccessToken(token: string): void {
  window.localStorage.setItem(AUTH_TOKEN_KEY, token);
  window.dispatchEvent(new Event('melo-auth-change'));
}

export function clearAccessToken(): void {
  window.localStorage.removeItem(AUTH_TOKEN_KEY);
  window.localStorage.removeItem(WORKSPACE_ID_KEY);
  window.localStorage.removeItem(USER_EMAIL_KEY);
  window.dispatchEvent(new Event('melo-auth-change'));
}

export function getWorkspaceId(): string | null {
  return typeof window === 'undefined' ? null : window.localStorage.getItem(WORKSPACE_ID_KEY);
}

export function setWorkspaceId(workspaceId: string): void {
  window.localStorage.setItem(WORKSPACE_ID_KEY, workspaceId);
}

export function clearWorkspaceId(): void {
  window.localStorage.removeItem(WORKSPACE_ID_KEY);
}

export function getUserEmail(): string | null {
  return typeof window === 'undefined' ? null : window.localStorage.getItem(USER_EMAIL_KEY);
}

export function hasAccessToken(): boolean {
  return Boolean(getAccessToken());
}

async function fetch(input: RequestInfo | URL, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  const token = getAccessToken();
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const workspaceId = getWorkspaceId()?.trim();
  if (workspaceId) {
    headers.set('X-Workspace-ID', workspaceId);
  } else {
    headers.delete('X-Workspace-ID');
  }

  return globalThis.fetch(input, { ...init, headers });
}

/**
 * Handle API response and errors
 */
async function handleResponse<T>(response: Response): Promise<T> {
  // Check if response is ok
  if (!response.ok) {
    if (response.status === 401) {
      clearAccessToken();
    }
    
    let errorData;
    try {
      errorData = await response.json();
    } catch {
      errorData = {
        error: 'UNKNOWN_ERROR',
        message: `HTTP ${response.status}: ${response.statusText}`,
        details: {}
      };
    }
    
    // Only clear workspace on explicit workspace auth errors, not on general document processing errors
    const errorMessage = errorData.detail || errorData.message || '';
    if (
      (response.status === 403 && errorMessage.includes('membership')) ||
      (response.status === 400 && errorMessage.includes('Workspace-ID'))
    ) {
      clearWorkspaceId();
    }

    throw new APIError(
      response.status,
      errorData.error || 'UNKNOWN_ERROR',
      errorData.message || `HTTP ${response.status}`,
      errorData.details
    );
  }

  return response.json();
}

export type AppSettings = {
  model: string;
  provider: string;
  temperature: number;
  context_size?: 4096 | 8192;
  top_p?: number;
  top_k?: number;
  system_prompt?: string | null;
  learning_level?: "beginner" | "intermediate" | "advanced";
  explanation_style?: "clear" | "concise" | "detailed";
  quiz_difficulty?: "easy" | "medium" | "hard";
};

export type UsageSummary = {
  used_tokens: number;
  limit_tokens: number | null;
  remaining_tokens: number | null;
  period_start: string;
  unlimited: boolean;
};

export async function getUsage(): Promise<{ usage: UsageSummary | null }> {
  const response = await fetch(`${API_URL}/usage`);
  return handleResponse(response);
}

export type StudyProgress = {
  id: number;
  session_id: string;
  collection_id?: string | null;
  topic: string;
  completed_cards: number;
  quiz_score?: number | null;
  updated_at: string;
};

export async function getStudyProgress(sessionId: string, collectionId?: string): Promise<{ progress: StudyProgress[] }> {
  const query = collectionId ? `?collection_id=${encodeURIComponent(collectionId)}` : "";
  const response = await fetch(`${API_URL}/study/progress/${sessionId}${query}`);
  return handleResponse(response);
}

export async function saveStudyProgress(sessionId: string, progress: Omit<StudyProgress, "id" | "session_id" | "updated_at">): Promise<StudyProgress> {
  const response = await fetch(`${API_URL}/study/progress/${sessionId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(progress),
  });
  return handleResponse<StudyProgress>(response);
}

export type InstalledModel = {
  name: string;
  size?: number | null;
  modified_at?: string | null;
};

export type CodeFile = {
  path: string;
  size_bytes: number;
  line_count: number;
  content: string;
};

export type CodeFileWriteResult = {
  path: string;
  size_bytes: number;
  line_count: number;
  created: boolean;
};

export type CodeAnalysis = {
  path: string;
  extension: string;
  language: string;
  size_bytes: number;
  line_count: number;
  imports: string[];
  functions: string[];
  classes: string[];
  syntax_error?: string;
};

export type CodeAssistantResult = {
  path: string;
  result: string;
};

export type GitStatus = {
  branch: string;
  files: { status: string; path: string }[];
  count: number;
};

export type GitDiff = {
  path: string | null;
  diff: string;
};

export type TrainingDataset = {
  name: string;
  path: string;
  example_count?: number;
  size_bytes?: number;
};

export type SessionSummary = {
  id: string;
  title: string;
};

export type SessionsResponse = {
  sessions: SessionSummary[];
  count: number;
};

export async function readWorkspaceFile(path: string): Promise<CodeFile> {
  try {
    const response = await fetch(`${API_URL}/files/read`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path }),
    });
    return handleResponse<CodeFile>(response);
  } catch (error) {
    if (error instanceof APIError) throw error;
    throw new APIError(500, 'NETWORK_ERROR', 'Failed to read workspace file', {
      originalError: String(error),
    });
  }
}

export async function analyzeWorkspaceFile(path: string): Promise<CodeAnalysis> {
  try {
    const response = await fetch(`${API_URL}/analysis/code`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path }),
    });
    return handleResponse<CodeAnalysis>(response);
  } catch (error) {
    if (error instanceof APIError) throw error;
    throw new APIError(500, 'NETWORK_ERROR', 'Failed to analyze workspace file', {
      originalError: String(error),
    });
  }
}

export async function getModels(): Promise<{ models: InstalledModel[]; count: number; error?: string }> {
  try {
    const response = await fetch(`${API_URL}/models`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    return handleResponse(response);
  } catch (error) {
    if (error instanceof APIError) throw error;
    throw new APIError(
      500,
      'NETWORK_ERROR',
      'Failed to fetch installed models',
      { originalError: String(error) }
    );
  }
}

export type DocumentSummary = {
  id: string;
  filename: string;
  file_type: "pdf" | "docx" | "txt";
  chunk_count?: number;
  collection_id?: string | null;
  created_at?: string | null;
};

export type KnowledgeCollection = {
  id: string;
  name: string;
  description?: string | null;
  created_at?: string;
};

export type SessionDocumentsResponse = {
  session_id: string;
  documents: DocumentSummary[];
  count: number;
};

export type DocumentChunk = {
  id: string;
  document_id: string;
  chunk_index: number;
  content: string;
  tokens?: number | null;
  created_at?: string | null;
};

export type DocumentChunksResponse = {
  document_id: string;
  chunks: DocumentChunk[];
  count: number;
};

export type DocumentSearchResult = {
  filename: string;
  content: string;
  relevance: number;
  chunk_index?: number | null;
};

export type DocumentSearchResponse = {
  query: string;
  results: DocumentSearchResult[];
  available: boolean;
};

export type UploadDocumentPayload = {
  filename: string;
  file_type: "pdf" | "docx" | "txt";
  content: string;
  session_id?: string;
  collection_id?: string;
};

export async function getCollections(): Promise<{ collections: KnowledgeCollection[] }> {
  const response = await fetch(`${API_URL}/collections`);
  return handleResponse(response);
}

export async function createCollection(name: string): Promise<KnowledgeCollection> {
  const response = await fetch(`${API_URL}/collections`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  return handleResponse<KnowledgeCollection>(response);
}

/**
 * Get all sessions
 */
export async function getSessions(): Promise<SessionsResponse> {
  try {
    const workspaceId = getWorkspaceId()?.trim();
    if (!workspaceId) {
      throw new APIError(400, 'WORKSPACE_REQUIRED', 'No active workspace. Please log in again.');
    }

    const response = await fetch(`${API_URL}/sessions`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    return handleResponse<SessionsResponse>(response);
  } catch (error) {
    if (error instanceof APIError) throw error;
    throw new APIError(
      500,
      'NETWORK_ERROR',
      'Failed to fetch sessions',
      { originalError: String(error) }
    );
  }
}

/**
 * Create a new session
 */
export async function createSession(): Promise<SessionSummary> {
  try {
    const workspaceId = getWorkspaceId()?.trim();
    if (!workspaceId) {
      throw new APIError(400, 'WORKSPACE_REQUIRED', 'No active workspace. Please log in again.');
    }

    const response = await fetch(`${API_URL}/sessions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    return handleResponse<SessionSummary>(response);
  } catch (error) {
    if (error instanceof APIError) throw error;
    throw new APIError(
      500,
      'NETWORK_ERROR',
      'Failed to create session',
      { originalError: String(error) }
    );
  }
}

/**
 * Get chat history for a session
 */
export async function getHistory(sessionId: string) {
  try {
    if (!sessionId) {
      throw new APIError(
        400,
        'VALIDATION_ERROR',
        'Session ID is required',
        { field: 'sessionId' }
      );
    }

    const response = await fetch(`${API_URL}/history/${sessionId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    return handleResponse(response);
  } catch (error) {
    if (error instanceof APIError) throw error;
    throw new APIError(
      500,
      'NETWORK_ERROR',
      'Failed to fetch chat history',
      { originalError: String(error) }
    );
  }
}

/**
 * Send a message to a session
 */
export async function sendMessage(
  sessionId: string,
  message: string,
  mode: ChatMode = "chat",
  collectionId?: string,
) {
  try {
    if (!sessionId) {
      throw new APIError(
        400,
        'VALIDATION_ERROR',
        'Session ID is required',
        { field: 'sessionId' }
      );
    }

    if (!message || message.trim().length === 0) {
      throw new APIError(
        400,
        'VALIDATION_ERROR',
        'Message cannot be empty',
        { field: 'message' }
      );
    }

    const response = await fetch(`${API_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        message: message.trim(),
        mode,
        collection_id: collectionId,
      }),
    });
    return handleResponse(response);
  } catch (error) {
    if (error instanceof APIError) throw error;
    throw new APIError(
      500,
      'NETWORK_ERROR',
      'Failed to send message',
      { originalError: String(error) }
    );
  }
}

/**
 * Get current settings
 */
export async function getSettings(): Promise<AppSettings> {
  try {
    const response = await fetch(`${API_URL}/settings`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    return handleResponse<AppSettings>(response);
  } catch (error) {
    if (error instanceof APIError) throw error;
    throw new APIError(
      500,
      'NETWORK_ERROR',
      'Failed to fetch settings',
      { originalError: String(error) }
    );
  }
}

/**
 * Update application settings
 */
export async function updateSettings(settings: {
  model: string;
  provider: string;
  temperature: number;
  context_size?: 4096 | 8192;
  learning_level?: "beginner" | "intermediate" | "advanced";
  explanation_style?: "clear" | "concise" | "detailed";
  quiz_difficulty?: "easy" | "medium" | "hard";
}) {
  try {
    if (!settings.model || settings.model.trim().length === 0) {
      throw new APIError(
        400,
        'VALIDATION_ERROR',
        'Model is required',
        { field: 'model' }
      );
    }

    if (!settings.provider || settings.provider.trim().length === 0) {
      throw new APIError(
        400,
        'VALIDATION_ERROR',
        'Provider is required',
        { field: 'provider' }
      );
    }

    if (typeof settings.temperature !== 'number' || settings.temperature < 0 || settings.temperature > 2) {
      throw new APIError(
        400,
        'VALIDATION_ERROR',
        'Temperature must be between 0 and 2',
        { field: 'temperature' }
      );
    }

    const response = await fetch(`${API_URL}/settings`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ ...settings, context_size: settings.context_size || 8192 }),
    });
    return handleResponse(response);
  } catch (error) {
    if (error instanceof APIError) throw error;
    throw new APIError(
      500,
      'NETWORK_ERROR',
      'Failed to update settings',
      { originalError: String(error) }
    );
  }
}

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  sources?: ChatSource[];
  model?: string;
  usage?: ChatUsage;
};

export type ChatMode = "chat" | "ask" | "study" | "plan" | "agent" | "auto";

export type AgentAction = {
  action: "read_file" | "analyze_code" | "search_documents";
  path?: string;
  query?: string;
  session_id?: string;
  collection_id?: string;
};

export type AgentRunResponse = {
  results: { action: AgentAction["action"]; result: unknown }[];
  executed: number;
  side_effects: false;
};

export type AgentApproval = {
  approval_id: string;
  action: "write_file" | "delete_file" | "git_stage" | "git_commit";
  target: string;
  expires_at: string;
};

export async function requestAgentApproval(
  action: AgentApproval["action"],
  target: string,
): Promise<AgentApproval> {
  const response = await fetch(`${API_URL}/agent/approvals`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, target }),
  });
  return handleResponse<AgentApproval>(response);
}

export async function runReadOnlyAgent(actions: AgentAction[]): Promise<AgentRunResponse> {
  const response = await fetch(`${API_URL}/agent/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ actions }),
  });
  return handleResponse<AgentRunResponse>(response);
}

export type ChatUsage = {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
};

export type ChatSource = {
  document_id?: string;
  filename: string;
  relevance: number;
  chunks?: number[];
};

type StreamChunkEvent = {
  type: "chunk";
  content: string;
};

type StreamDoneEvent = {
  type: "done";
  session_id: string;
  response: string;
  model?: string;
  usage?: ChatUsage;
  sources?: ChatSource[];
};

type StreamErrorEvent = {
  type: "error";
  error_code: string;
  message: string;
};

type StreamEvent = StreamChunkEvent | StreamDoneEvent | StreamErrorEvent;

type SendMessageStreamOptions = {
  mode?: ChatMode;
  collectionId?: string;
  documentId?: string;
  onChunk?: (chunk: string) => void;
  onSources?: (sources: ChatSource[]) => void;
  onMetadata?: (metadata: { model?: string; usage?: ChatUsage }) => void;
  signal?: AbortSignal;
};

export async function sendMessageStream(
  sessionId: string,
  message: string,
  options: SendMessageStreamOptions = {}
) {
  if (!sessionId) {
    throw new APIError(
      400,
      'VALIDATION_ERROR',
      'Session ID is required',
      { field: 'sessionId' }
    );
  }

  if (!message || message.trim().length === 0) {
    throw new APIError(
      400,
      'VALIDATION_ERROR',
      'Message cannot be empty',
      { field: 'message' }
    );
  }

  const response = await fetch(`${API_URL}/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
      message: message.trim(),
      mode: options.mode || "chat",
      collection_id: options.collectionId,
      document_id: options.documentId,
    }),
    signal: options.signal,
  });

  if (!response.ok) {
    await handleResponse(response);
  }

  if (!response.body) {
    throw new APIError(500, 'STREAM_ERROR', 'No streaming body returned by server');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let finalResponse = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() ?? '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) {
          continue;
        }

        let event: StreamEvent;
        try {
          event = JSON.parse(trimmed) as StreamEvent;
        } catch {
          continue;
        }

        if (event.type === 'chunk') {
          finalResponse += event.content;
          options.onChunk?.(event.content);
          continue;
        }

        if (event.type === 'done') {
          options.onMetadata?.({ model: event.model, usage: event.usage });
          options.onSources?.(event.sources || []);
          return event.response || finalResponse;
        }

        if (event.type === 'error') {
          throw new APIError(
            500,
            event.error_code || 'STREAM_ERROR',
            event.message || 'Streaming chat failed'
          );
        }
      }
    }

    return finalResponse;
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }

    if (error instanceof DOMException && error.name === 'AbortError') {
      throw error;
    }

    throw new APIError(
      500,
      'NETWORK_ERROR',
      'Failed to stream message response',
      { originalError: String(error) }
    );
  } finally {
    reader.releaseLock();
  }
}

export async function uploadDocument(payload: UploadDocumentPayload): Promise<DocumentSummary> {
  try {
    const response = await fetch(`${API_URL}/documents`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
    return handleResponse<DocumentSummary>(response);
  } catch (error) {
    if (error instanceof APIError) throw error;
    throw new APIError(
      500,
      'NETWORK_ERROR',
      'Failed to upload document',
      { originalError: String(error) }
    );
  }
}

export async function getSessionDocuments(sessionId: string): Promise<SessionDocumentsResponse> {
  try {
    if (!sessionId) {
      throw new APIError(
        400,
        'VALIDATION_ERROR',
        'Session ID is required',
        { field: 'sessionId' }
      );
    }

    const response = await fetch(`${API_URL}/sessions/${sessionId}/documents`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    return handleResponse<SessionDocumentsResponse>(response);
  } catch (error) {
    if (error instanceof APIError) throw error;
    throw new APIError(
      500,
      'NETWORK_ERROR',
      'Failed to fetch session documents',
      { originalError: String(error) }
    );
  }
}

export async function getDocumentChunks(documentId: string): Promise<DocumentChunksResponse> {
  try {
    if (!documentId) {
      throw new APIError(
        400,
        'VALIDATION_ERROR',
        'Document ID is required',
        { field: 'documentId' }
      );
    }

    const response = await fetch(`${API_URL}/documents/${documentId}/chunks`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    return handleResponse<DocumentChunksResponse>(response);
  } catch (error) {
    if (error instanceof APIError) throw error;
    throw new APIError(
      500,
      'NETWORK_ERROR',
      'Failed to fetch document chunks',
      { originalError: String(error) }
    );
  }
}

export async function deleteDocument(documentId: string): Promise<void> {
  try {
    if (!documentId) {
      throw new APIError(
        400,
        'VALIDATION_ERROR',
        'Document ID is required',
        { field: 'documentId' }
      );
    }

    const response = await fetch(`${API_URL}/documents/${documentId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      await handleResponse(response);
    }
  } catch (error) {
    if (error instanceof APIError) throw error;
    throw new APIError(
      500,
      'NETWORK_ERROR',
      'Failed to delete document',
      { originalError: String(error) }
    );
  }
}

export async function uploadDocumentFile(
  file: File,
  sessionId: string,
  collectionId?: string,
): Promise<DocumentSummary> {
  if (!sessionId) {
    throw new APIError(400, 'VALIDATION_ERROR', 'Session ID is required');
  }

  const formData = new FormData();
  formData.append('file', file);
  formData.append('session_id', sessionId);
  if (collectionId) formData.append('collection_id', collectionId);

  try {
    // Ensure headers are set - use the internal fetch wrapper
    const response = await fetch(`${API_URL}/documents/upload`, {
      method: 'POST',
      body: formData,
      headers: {}, // Empty headers object triggers the wrapper to add Authorization and X-Workspace-ID
    });
    return handleResponse<DocumentSummary>(response);
  } catch (error) {
    if (error instanceof APIError) throw error;
    throw new APIError(
      500,
      'NETWORK_ERROR',
      'Failed to upload document file',
      { originalError: String(error) }
    );
  }
}

export async function writeWorkspaceFile(path: string, content: string): Promise<CodeFileWriteResult> {
  try {
    const approval = await requestAgentApproval("write_file", path);
    const response = await fetch(`${API_URL}/files/write`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path, content, confirm: true, approval_id: approval.approval_id }),
    });
    return handleResponse<CodeFileWriteResult>(response);
  } catch (error) {
    if (error instanceof APIError) throw error;
    throw new APIError(500, 'NETWORK_ERROR', 'Failed to save workspace file', {
      originalError: String(error),
    });
  }
}

export async function deleteWorkspaceFile(path: string): Promise<void> {
  try {
    const approval = await requestAgentApproval("delete_file", path);
    const response = await fetch(`${API_URL}/files`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path, confirm: true, approval_id: approval.approval_id }),
    });
    await handleResponse(response);
  } catch (error) {
    if (error instanceof APIError) throw error;
    throw new APIError(500, 'NETWORK_ERROR', 'Failed to delete workspace file', {
      originalError: String(error),
    });
  }
}

export async function reviewWorkspaceFile(path: string, instruction?: string): Promise<CodeAssistantResult> {
  const response = await fetch(`${API_URL}/coding/review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path, instruction }),
  });
  return handleResponse<CodeAssistantResult>(response);
}

export async function generateWorkspaceCode(path: string, instruction: string): Promise<CodeAssistantResult> {
  const response = await fetch(`${API_URL}/coding/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path, instruction }),
  });
  return handleResponse<CodeAssistantResult>(response);
}

export async function getGitStatus(): Promise<GitStatus> {
  const response = await fetch(`${API_URL}/git/status`);
  return handleResponse<GitStatus>(response);
}

export async function getGitDiff(path?: string): Promise<GitDiff> {
  const query = path ? `?path=${encodeURIComponent(path)}` : '';
  const response = await fetch(`${API_URL}/git/diff${query}`);
  return handleResponse<GitDiff>(response);
}

export async function stageGitFiles(paths: string[]): Promise<{ staged: string[]; count: number }> {
  const approval = await requestAgentApproval("git_stage", paths.join("\n"));
  const response = await fetch(`${API_URL}/git/stage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ paths, confirm: true, approval_id: approval.approval_id }),
  });
  return handleResponse(response);
}

export async function commitGitChanges(message: string): Promise<{ message: string; output: string }> {
  const approval = await requestAgentApproval("git_commit", message.trim());
  const response = await fetch(`${API_URL}/git/commit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, confirm: true, approval_id: approval.approval_id }),
  });
  return handleResponse(response);
}

export async function getTrainingDatasets(): Promise<{ datasets: TrainingDataset[] }> {
  const response = await fetch(`${API_URL}/training/datasets`);
  return handleResponse(response);
}

export async function createTrainingDataset(
  name: string,
  examples: { messages: { role: string; content: string }[] }[]
): Promise<TrainingDataset> {
  const response = await fetch(`${API_URL}/training/datasets`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, examples }),
  });
  return handleResponse<TrainingDataset>(response);
}

/**
 * Delete a chat session
 */
export async function deleteSession(sessionId: string): Promise<void> {
  try {
    const response = await fetch(`${API_URL}/sessions/${sessionId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      await handleResponse(response);
    }
  } catch (error) {
    if (error instanceof APIError) throw error;
    throw new APIError(
      500,
      'NETWORK_ERROR',
      'Failed to delete session',
      { originalError: String(error) }
    );
  }
}

export async function searchDocuments(
  sessionId: string,
  query: string,
  topK = 5,
  collectionId?: string,
): Promise<DocumentSearchResponse> {
  const response = await fetch(`${API_URL}/documents/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, query: query.trim(), top_k: topK, collection_id: collectionId }),
  });
  return handleResponse<DocumentSearchResponse>(response);
}

export type AuthResponse = {
  access_token: string;
  token_type: string;
  user_id: string;
  workspace_id: string;
};

export type CurrentUser = {
  user_id: string;
  email: string;
  workspace_id?: string | null;
};

export async function getCurrentUser(): Promise<CurrentUser> {
  const response = await fetch(`${API_URL}/auth/me`);
  return handleResponse<CurrentUser>(response);
}

export async function register(email: string, password: string): Promise<AuthResponse> {
  const response = await globalThis.fetch(`${API_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  const result = await handleResponse<AuthResponse>(response);
  setAccessToken(result.access_token);
  setWorkspaceId(result.workspace_id);
  window.localStorage.setItem(USER_EMAIL_KEY, email.trim().toLowerCase());
  return result;
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  const response = await globalThis.fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  const result = await handleResponse<AuthResponse>(response);
  setAccessToken(result.access_token);
  setWorkspaceId(result.workspace_id);
  window.localStorage.setItem(USER_EMAIL_KEY, email.trim().toLowerCase());
  return result;
}

export async function logout(): Promise<void> {
  try {
    const response = await fetch(`${API_URL}/auth/logout`, { method: 'POST' });
    await handleResponse(response);
  } finally {
    clearAccessToken();
  }
}

export async function downloadResponsePdf(content: string): Promise<Blob> {
  const response = await fetch(`${API_URL}/chat/export/pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content, filename: "melo-response.pdf" }),
  });
  if (!response.ok) {
    await handleResponse(response);
  }
  return response.blob();
}

export async function downloadResponseDocx(content: string): Promise<Blob> {
  const response = await fetch(`${API_URL}/chat/export/docx`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content, filename: "melo-response.docx" }),
  });
  if (!response.ok) {
    await handleResponse(response);
  }
  return response.blob();
}