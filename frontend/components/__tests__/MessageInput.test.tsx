import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import MessageInput from '@/components/MessageInput';

describe('MessageInput', () => {
  it('renders input field', () => {
    const mockOnSend = jest.fn();
    render(
      <MessageInput sessionId="session-1" onSendMessage={mockOnSend} isSending={false} />
    );
    
    const input = screen.getByPlaceholderText(/message melo/i);
    expect(input).toBeInTheDocument();
  });

  it('sends message when send button is clicked', () => {
    const mockOnSend = jest.fn();
    render(
      <MessageInput sessionId="session-1" onSendMessage={mockOnSend} isSending={false} />
    );
    
    const input = screen.getByPlaceholderText(/message melo/i) as HTMLInputElement;
    const sendButton = screen.getByRole('button');
    
    fireEvent.change(input, { target: { value: 'Hello!' } });
    fireEvent.click(sendButton);
    
    expect(mockOnSend).toHaveBeenCalledWith('Hello!');
  });

  it('clears input after sending message', async () => {
    const mockOnSend = jest.fn();
    render(
      <MessageInput sessionId="session-1" onSendMessage={mockOnSend} isSending={false} />
    );
    
    const input = screen.getByPlaceholderText(/message melo/i) as HTMLInputElement;
    const sendButton = screen.getByRole('button');
    
    fireEvent.change(input, { target: { value: 'Hello!' } });
    fireEvent.click(sendButton);
    
    await waitFor(() => expect(input.value).toBe(''));
  });

  it('disables send when input is empty', () => {
    const mockOnSend = jest.fn();
    render(
      <MessageInput sessionId="session-1" onSendMessage={mockOnSend} isSending={false} />
    );
    
    const sendButton = screen.getByRole('button') as HTMLButtonElement;
    
    // Button should be disabled when input is empty
    expect(sendButton.disabled).toBe(true);
  });

  it('enables send when input has text', () => {
    const mockOnSend = jest.fn();
    render(
      <MessageInput sessionId="session-1" onSendMessage={mockOnSend} isSending={false} />
    );
    
    const input = screen.getByPlaceholderText(/message melo/i);
    const sendButton = screen.getByRole('button') as HTMLButtonElement;
    
    fireEvent.change(input, { target: { value: 'Hello!' } });
    
    expect(sendButton.disabled).toBe(false);
  });

  it('sends message through the send action', () => {
    const mockOnSend = jest.fn();
    render(
      <MessageInput sessionId="session-1" onSendMessage={mockOnSend} isSending={false} />
    );
    
    const input = screen.getByPlaceholderText(/message melo/i);
    const sendButton = screen.getByRole('button');
    
    fireEvent.change(input, { target: { value: 'Hello!' } });
    fireEvent.click(sendButton);

    expect(mockOnSend).toHaveBeenCalledWith('Hello!');
  });

  it('keeps a newline when Shift+Enter is pressed', () => {
    const mockOnSend = jest.fn();
    render(
      <MessageInput sessionId="session-1" onSendMessage={mockOnSend} isSending={false} />
    );

    const input = screen.getByPlaceholderText(/message melo/i);
    fireEvent.change(input, { target: { value: 'First line' } });
    fireEvent.keyDown(input, { key: 'Enter', shiftKey: true });

    expect(mockOnSend).not.toHaveBeenCalled();
  });

  it('changes chat mode', () => {
    const onModeChange = jest.fn();
    render(
      <MessageInput
        sessionId="session-1"
        onSendMessage={jest.fn()}
        isSending={false}
        mode="chat"
        onModeChange={onModeChange}
      />
    );

    fireEvent.change(screen.getByRole('combobox', { name: /choose response mode/i }), {
      target: { value: 'ask' },
    });

    expect(onModeChange).toHaveBeenCalledWith('ask');
  });

  it('offers study mode', () => {
    render(
      <MessageInput
        sessionId="session-1"
        onSendMessage={jest.fn()}
        isSending={false}
        mode="study"
      />
    );

    expect(screen.getByRole('option', { name: 'Study' })).toBeInTheDocument();
  });

  it('offers plan mode', () => {
    render(
      <MessageInput
        sessionId="session-1"
        onSendMessage={jest.fn()}
        isSending={false}
        mode="plan"
      />
    );

    expect(screen.getByRole('option', { name: 'Plan' })).toBeInTheDocument();
  });

  it('offers auto mode', () => {
    render(
      <MessageInput
        sessionId="session-1"
        onSendMessage={jest.fn()}
        isSending={false}
        mode="auto"
      />
    );

    expect(screen.getByRole('combobox', { name: /choose response mode/i })).toHaveValue('auto');
  });
});
