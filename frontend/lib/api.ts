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

/**
 * Handle API response and errors
 */
async function handleResponse<T>(response: Response): Promise<T> {
  // Check if response is ok
  if (!response.ok) {
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
  top_p?: number;
  top_k?: number;
  system_prompt?: string | null;
};

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
  created_at?: string | null;
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

export type UploadDocumentPayload = {
  filename: string;
  file_type: "pdf" | "docx" | "txt";
  content: string;
  session_id?: string;
};

/**
 * Get all sessions
 */
export async function getSessions(): Promise<SessionsResponse> {
  try {
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
  message: string
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
      body: JSON.stringify(settings),
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
};

export type ChatSource = {
  filename: string;
  relevance: number;
};

type StreamChunkEvent = {
  type: "chunk";
  content: string;
};

type StreamDoneEvent = {
  type: "done";
  session_id: string;
  response: string;
  sources?: ChatSource[];
};

type StreamErrorEvent = {
  type: "error";
  error_code: string;
  message: string;
};

type StreamEvent = StreamChunkEvent | StreamDoneEvent | StreamErrorEvent;

type SendMessageStreamOptions = {
  onChunk?: (chunk: string) => void;
  onSources?: (sources: ChatSource[]) => void;
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
  sessionId: string
): Promise<DocumentSummary> {
  if (!sessionId) {
    throw new APIError(400, 'VALIDATION_ERROR', 'Session ID is required');
  }

  const formData = new FormData();
  formData.append('file', file);
  formData.append('session_id', sessionId);

  try {
    const response = await fetch(`${API_URL}/documents/upload`, {
      method: 'POST',
      body: formData,
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
    const response = await fetch(`${API_URL}/files/write`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path, content, confirm: true }),
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
    const response = await fetch(`${API_URL}/files`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path, confirm: true }),
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
  const response = await fetch(`${API_URL}/git/stage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ paths, confirm: true }),
  });
  return handleResponse(response);
}

export async function commitGitChanges(message: string): Promise<{ message: string; output: string }> {
  const response = await fetch(`${API_URL}/git/commit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, confirm: true }),
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