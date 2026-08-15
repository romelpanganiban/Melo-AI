import {
  getSessions,
  createSession,
  sendMessage,
  getHistory,
  APIError,
} from '@/lib/api';

// Mock fetch
global.fetch = jest.fn();

describe('API Functions', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getSessions', () => {
    it('fetches all sessions successfully', async () => {
      const mockResponse = {
        sessions: [
          { id: '1', title: 'Chat 1' },
          { id: '2', title: 'Chat 2' },
        ],
        count: 2,
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await getSessions();

      expect(result).toEqual(mockResponse);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/sessions'),
        expect.any(Object)
      );
    });

    it('throws APIError on failed response', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        json: async () => ({ error: 'SERVER_ERROR', message: 'Server error' }),
      });

      await expect(getSessions()).rejects.toThrow(APIError);
    });
  });

  describe('createSession', () => {
    it('creates a new session successfully', async () => {
      const mockResponse = {
        id: '123',
        title: 'New Chat',
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await createSession();

      expect(result).toEqual(mockResponse);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/sessions'),
        expect.objectContaining({ method: 'POST' })
      );
    });
  });

  describe('sendMessage', () => {
    it('sends message successfully', async () => {
      const mockResponse = {
        response: 'Hello!',
        recent_history: [
          { role: 'user', content: 'Hi' },
          { role: 'assistant', content: 'Hello!' },
        ],
        session_id: '123',
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await sendMessage('123', 'Hi');

      expect(result).toEqual(mockResponse);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/chat'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('123'),
        })
      );
    });

    it('throws error for empty message', async () => {
      await expect(sendMessage('123', '')).rejects.toThrow(APIError);
    });

    it('throws error for empty session id', async () => {
      await expect(sendMessage('', 'Hi')).rejects.toThrow(APIError);
    });
  });

  describe('getHistory', () => {
    it('fetches chat history successfully', async () => {
      const mockResponse = {
        session_id: '123',
        messages: [
          { role: 'user', content: 'Hi' },
          { role: 'assistant', content: 'Hello!' },
        ],
        message_count: 2,
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await getHistory('123');

      expect(result).toEqual(mockResponse);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/history/123'),
        expect.any(Object)
      );
    });
  });

  describe('APIError', () => {
    it('creates error with status code and error code', () => {
      const error = new APIError(404, 'NOT_FOUND', 'Resource not found');

      expect(error.statusCode).toBe(404);
      expect(error.errorCode).toBe('NOT_FOUND');
      expect(error.message).toBe('Resource not found');
    });

    it('includes details in error object', () => {
      const details = { field: 'session_id' };
      const error = new APIError(
        400,
        'VALIDATION_ERROR',
        'Invalid session ID',
        details
      );

      expect(error.details).toEqual(details);
    });
  });
});
