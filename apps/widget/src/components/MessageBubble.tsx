import React from 'react';
import type { Message } from '../types';

interface MessageBubbleProps {
  message: Message;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user';
  
  console.log('[MessageBubble] Rendering message:', {
    id: message.id,
    role: message.role,
    contentLength: message.content.length,
    content: message.content.substring(0, 50) + (message.content.length > 50 ? '...' : '')
  });
  
  return (
    <div className={`message-bubble ${isUser ? 'user' : 'assistant'}`}>
      <div className={`message-content ${isUser ? 'user-message' : 'assistant-message'}`}>
        <p className="message-text">{message.content}</p>
        {message.citations && message.citations.length > 0 && (
          <div className="citations">
            <div className="citations-label">Sources:</div>
            {message.citations.map((citation, index) => (
              <div key={index} className="citation">
                <a 
                  href={citation.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="citation-link"
                >
                  {citation.title}
                </a>
                {citation.snippet && (
                  <p className="citation-snippet">{citation.snippet}</p>
                )}
              </div>
            ))}
          </div>
        )}
        <div className="message-timestamp">
          {new Date(message.timestamp).toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
          })}
        </div>
      </div>
    </div>
  );
};
