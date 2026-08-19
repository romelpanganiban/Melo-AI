/// <reference types="@testing-library/jest-dom" />

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, jest } from '@jest/globals';
import Sidebar from '../Sidebar';

const mockedFetch = jest.fn() as jest.MockedFunction<typeof fetch>;
global.fetch = mockedFetch;

function createResponse(payload: unknown): Response {
  return {
    ok: true,
    json: async () => payload,
  } as Response;
}

const defaultProps = {
  selectedSession: '1',
  setSelectedSession: jest.fn(),
  isOpen: true,
  onClose: jest.fn(),
};

describe('Sidebar', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockedFetch.mockImplementation((_input, init) => {
      if (init?.method === 'POST') {
        return Promise.resolve(createResponse({ id: '4', title: 'New Chat' }));
      }

      return Promise.resolve(createResponse({
          sessions: [
            { id: '1', title: 'First Chat' },
            { id: '2', title: 'Second Chat' },
            { id: '3', title: 'Third Chat' },
          ],
          count: 3,
        }));
    });
  });

  it('loads and renders sessions', async () => {
    render(<Sidebar {...defaultProps} />);

  expect(await screen.findByText('First Chat')).toBeTruthy();
  expect(screen.getByText('Second Chat')).toBeTruthy();
  expect(screen.getByText('Third Chat')).toBeTruthy();
  });

  it('selects a session when clicked', async () => {
    render(<Sidebar {...defaultProps} />);

    fireEvent.click(await screen.findByText('Second Chat'));

    expect(defaultProps.setSelectedSession).toHaveBeenCalledWith('2');
  });

  it('creates a new chat', async () => {
    render(<Sidebar {...defaultProps} />);

    fireEvent.click(screen.getByRole('button', { name: /new chat/i }));

    await waitFor(() => {
      expect(mockedFetch).toHaveBeenCalledWith(
        expect.stringContaining('/sessions'),
        expect.objectContaining({ method: 'POST' })
      );
    });
    expect(defaultProps.setSelectedSession).toHaveBeenCalledWith('4');
    expect(mockedFetch).toHaveBeenCalledTimes(3);
  });

  it('shows an empty state when no sessions exist', async () => {
    mockedFetch.mockResolvedValue(createResponse({ sessions: [], count: 0 }));

    render(<Sidebar {...defaultProps} />);

    expect(await screen.findByText('No sessions yet')).toBeTruthy();
  });
});
