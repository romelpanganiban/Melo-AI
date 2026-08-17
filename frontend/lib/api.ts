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

/**
 * Get all sessions
 */
export async function getSessions() {
  try {
    const response = await fetch(`${API_URL}/sessions`, {
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
      'Failed to fetch sessions',
      { originalError: String(error) }
    );
  }
}

/**
 * Create a new session
 */
export async function createSession() {
  try {
    const response = await fetch(`${API_URL}/sessions`, {
      method: 'POST',
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
export async function getSettings() {
  try {
    const response = await fetch(`${API_URL}/settings`, {
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
};

type StreamChunkEvent = {
  type: "chunk";
  content: string;
};

type StreamDoneEvent = {
  type: "done";
  session_id: string;
  response: string;
};

type StreamErrorEvent = {
  type: "error";
  error_code: string;
  message: string;
};

type StreamEvent = StreamChunkEvent | StreamDoneEvent | StreamErrorEvent;

type SendMessageStreamOptions = {
  onChunk?: (chunk: string) => void;
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