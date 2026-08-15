import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Sidebar from '@/components/Sidebar';

describe('Sidebar', () => {
  const mockSessions = [
    { id: '1', title: 'First Chat' },
    { id: '2', title: 'Second Chat' },
    { id: '3', title: 'Third Chat' },
  ];

  const mockHandlers = {
    onNewChat: jest.fn(),
    onSelectSession: jest.fn(),
    onRenameSession: jest.fn(),
    onDeleteSession: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders sidebar with sessions list', () => {
    render(
      <Sidebar
        sessions={mockSessions}
        currentSessionId="1"
        onNewChat={mockHandlers.onNewChat}
        onSelectSession={mockHandlers.onSelectSession}
      />
    );
    
    expect(screen.getByText('First Chat')).toBeInTheDocument();
    expect(screen.getByText('Second Chat')).toBeInTheDocument();
    expect(screen.getByText('Third Chat')).toBeInTheDocument();
  });

  it('shows new chat button', () => {
    render(
      <Sidebar
        sessions={mockSessions}
        currentSessionId="1"
        onNewChat={mockHandlers.onNewChat}
        onSelectSession={mockHandlers.onSelectSession}
      />
    );
    
    const newChatButton = screen.getByRole('button', { name: /new|chat/i });
    expect(newChatButton).toBeInTheDocument();
  });

  it('calls onNewChat when new chat button is clicked', () => {
    render(
      <Sidebar
        sessions={mockSessions}
        currentSessionId="1"
        onNewChat={mockHandlers.onNewChat}
        onSelectSession={mockHandlers.onSelectSession}
      />
    );
    
    const newChatButton = screen.getByRole('button', { name: /new|chat/i });
    fireEvent.click(newChatButton);
    
    expect(mockHandlers.onNewChat).toHaveBeenCalled();
  });

  it('calls onSelectSession when session is clicked', () => {
    render(
      <Sidebar
        sessions={mockSessions}
        currentSessionId="1"
        onNewChat={mockHandlers.onNewChat}
        onSelectSession={mockHandlers.onSelectSession}
      />
    );
    
    const sessionElement = screen.getByText('Second Chat');
    fireEvent.click(sessionElement);
    
    expect(mockHandlers.onSelectSession).toHaveBeenCalledWith('2');
  });

  it('highlights current session', () => {
    const { container } = render(
      <Sidebar
        sessions={mockSessions}
        currentSessionId="2"
        onNewChat={mockHandlers.onNewChat}
        onSelectSession={mockHandlers.onSelectSession}
      />
    );
    
    // The current session should have different styling
    const currentSession = screen.getByText('Second Chat').closest('div');
    expect(currentSession?.className).toMatch(/active|selected|bg-/i);
  });

  it('renders empty state when no sessions', () => {
    render(
      <Sidebar
        sessions={[]}
        currentSessionId={undefined}
        onNewChat={mockHandlers.onNewChat}
        onSelectSession={mockHandlers.onSelectSession}
      />
    );
    
    const newChatButton = screen.getByRole('button', { name: /new|chat/i });
    expect(newChatButton).toBeInTheDocument();
  });

  it('handles all sessions correctly', () => {
    const { container } = render(
      <Sidebar
        sessions={mockSessions}
        currentSessionId="1"
        onNewChat={mockHandlers.onNewChat}
        onSelectSession={mockHandlers.onSelectSession}
      />
    );
    
    // All sessions should be rendered
    mockSessions.forEach(session => {
      expect(screen.getByText(session.title)).toBeInTheDocument();
    });
  });
});
