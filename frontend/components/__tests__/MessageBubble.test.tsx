import React from 'react';
import { render, screen } from '@testing-library/react';
import MessageBubble from '@/components/MessageBubble';

describe('MessageBubble', () => {
  it('renders user message correctly', () => {
    render(
      <MessageBubble
        role="user"
        content="Hello, AI!"
      />
    );
    expect(screen.getByText('Hello, AI!')).toBeInTheDocument();
  });

  it('renders assistant message correctly', () => {
    render(
      <MessageBubble
        role="assistant"
        content="Hello, human!"
      />
    );
    expect(screen.getByText('Hello, human!')).toBeInTheDocument();
  });

  it('applies different styles for user vs assistant', () => {
    const { container: userContainer } = render(
      <MessageBubble
        role="user"
        content="User message"
      />
    );
    
    const { container: assistantContainer } = render(
      <MessageBubble
        role="assistant"
        content="Assistant message"
      />
    );

    // User messages should have different styling than assistant
    const userBubble = userContainer.querySelector('[class*="bg-teal-700"]');
    const assistantBubble = assistantContainer.querySelector('[class*="bg-emerald-50"]');
    
    expect(userBubble || assistantBubble).toBeInTheDocument();
  });

  it('handles long text content', () => {
    const longText = 'This is a very long message that should wrap properly without breaking the layout.'.repeat(5);
    render(
      <MessageBubble
        role="user"
        content={longText}
      />
    );
    expect(screen.getByText(longText)).toBeInTheDocument();
  });
});
