import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import MessageInput from '@/components/MessageInput';

describe('MessageInput', () => {
  it('renders input field', () => {
    const mockOnSend = jest.fn();
    render(
      <MessageInput onSend={mockOnSend} />
    );
    
    const input = screen.getByPlaceholderText(/type your message/i);
    expect(input).toBeInTheDocument();
  });

  it('sends message when send button is clicked', () => {
    const mockOnSend = jest.fn();
    render(
      <MessageInput onSend={mockOnSend} />
    );
    
    const input = screen.getByPlaceholderText(/type your message/i) as HTMLInputElement;
    const sendButton = screen.getByRole('button');
    
    fireEvent.change(input, { target: { value: 'Hello!' } });
    fireEvent.click(sendButton);
    
    expect(mockOnSend).toHaveBeenCalledWith('Hello!');
  });

  it('clears input after sending message', () => {
    const mockOnSend = jest.fn();
    render(
      <MessageInput onSend={mockOnSend} />
    );
    
    const input = screen.getByPlaceholderText(/type your message/i) as HTMLInputElement;
    const sendButton = screen.getByRole('button');
    
    fireEvent.change(input, { target: { value: 'Hello!' } });
    fireEvent.click(sendButton);
    
    expect(input.value).toBe('');
  });

  it('disables send when input is empty', () => {
    const mockOnSend = jest.fn();
    render(
      <MessageInput onSend={mockOnSend} />
    );
    
    const sendButton = screen.getByRole('button') as HTMLButtonElement;
    
    // Button should be disabled when input is empty
    expect(sendButton.disabled).toBe(true);
  });

  it('enables send when input has text', () => {
    const mockOnSend = jest.fn();
    render(
      <MessageInput onSend={mockOnSend} />
    );
    
    const input = screen.getByPlaceholderText(/type your message/i);
    const sendButton = screen.getByRole('button') as HTMLButtonElement;
    
    fireEvent.change(input, { target: { value: 'Hello!' } });
    
    expect(sendButton.disabled).toBe(false);
  });

  it('sends message on Enter key press', () => {
    const mockOnSend = jest.fn();
    render(
      <MessageInput onSend={mockOnSend} />
    );
    
    const input = screen.getByPlaceholderText(/type your message/i);
    
    fireEvent.change(input, { target: { value: 'Hello!' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
    
    expect(mockOnSend).toHaveBeenCalledWith('Hello!');
  });
});
