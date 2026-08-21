import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { describe, expect, it, jest } from '@jest/globals';
import ChatWindow from '../ChatWindow';
import type { ChatMessage } from '../../lib/api';

const mockMessages: (ChatMessage & { id: string })[] = [
  { id: '1', role: 'user', content: 'Hello!' },
  { id: '2', role: 'assistant', content: 'Hi there!' },
  { id: '3', role: 'user', content: 'How are you?' },
  { id: '4', role: 'assistant', content: 'I am doing well, thanks for asking!' },
];

const defaultProps = {
  sessionId: 'session-1',
  isLoading: false,
  error: null,
  onRetry: jest.fn(),
};

describe('ChatWindow', () => {
  it('renders messages correctly', () => {
    render(<ChatWindow {...defaultProps} messages={mockMessages} />);

    expect(screen.getByText('Hello!')).toBeTruthy();
    expect(screen.getByText('Hi there!')).toBeTruthy();
    expect(screen.getByText('How are you?')).toBeTruthy();
    expect(screen.getByText('I am doing well, thanks for asking!')).toBeTruthy();
  });

  it('shows the empty state when there are no messages', () => {
    render(<ChatWindow {...defaultProps} messages={[]} />);

    expect(screen.getByText(/no messages yet/i)).toBeTruthy();
  });

  it('shows the loading state', () => {
    render(<ChatWindow {...defaultProps} isLoading messages={mockMessages} />);

    expect(screen.getByText(/loading messages/i)).toBeTruthy();
  });

  it('shows an error and retry action', () => {
    render(<ChatWindow {...defaultProps} error="Network failed" messages={[]} />);

    expect(screen.getByText('Network failed')).toBeTruthy();
    expect(screen.getByRole('button', { name: /retry/i })).toBeTruthy();
  });
});
