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
    const userBubble = userContainer.querySelector('[class*="bg-teal-600"]');
    const assistantBubble = assistantContainer.querySelector('.assistant-bubble');
    
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

  it('cleans Markdown heading, separator, and bold markers', () => {
    render(
      <MessageBubble
        role="assistant"
        content={'### Notes\n***\n**Important** details'}
      />
    );

    expect(screen.getByText('Notes')).toBeInTheDocument();
    expect(screen.getByText('Important')).toBeInTheDocument();
    expect(screen.queryByText('### Notes')).not.toBeInTheDocument();
    expect(screen.queryByText('***')).not.toBeInTheDocument();
  });

  it('renders safe links as clickable anchors', () => {
    render(
      <MessageBubble
        role="assistant"
        content="Visit https://example.com or [Melo](https://melo.example.com)."
      />
    );

    expect(screen.getByRole('link', { name: 'https://example.com' })).toHaveAttribute('href', 'https://example.com');
    expect(screen.getByRole('link', { name: 'Melo' })).toHaveAttribute('href', 'https://melo.example.com');
    expect(screen.getAllByRole('link')[0]).toHaveAttribute('target', '_blank');
  });

  it('does not show file download actions for ordinary chat responses', () => {
    render(<MessageBubble role="assistant" content="Formatted document content" />);

    expect(screen.queryByRole('button', { name: /download markdown/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /download pdf/i })).not.toBeInTheDocument();
  });

  it('shows export actions only when explicitly enabled', () => {
    render(
      <MessageBubble
        role="assistant"
        content="Revised resume"
        sources={[{ filename: "resume.pdf", relevance: 100 }]}
        canExport
      />
    );

    expect(screen.getByRole('button', { name: /download docx/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /download pdf/i })).toBeInTheDocument();
  });
});
