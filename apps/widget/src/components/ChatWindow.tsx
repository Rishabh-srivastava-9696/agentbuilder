import React from 'react';
import type { Message } from '../types';
import { MessageBubble } from './MessageBubble';
import { TypingIndicator } from './TypingIndicator';

interface ChatWindowProps {
  messages: Message[];
  isTyping: boolean;
  isExpanded?: boolean;
  isMobile?: boolean;
  onSendMessage: (text: string) => void;
  onClose: () => void;
  onToggleExpand?: () => void;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({
  messages,
  isTyping,
  isExpanded = false,
  isMobile = false,
  onSendMessage,
  onClose,
  onToggleExpand
}) => {
  const [inputValue, setInputValue] = React.useState('');
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  // Log when messages prop changes
  React.useEffect(() => {
    console.log('[ChatWindow] Messages updated:', {
      count: messages.length,
      messages: messages.map(m => ({ 
        id: m.id, 
        role: m.role, 
        contentLength: m.content.length,
        content: m.content.substring(0, 30) + '...'
      }))
    });
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim()) {
      onSendMessage(inputValue.trim());
      setInputValue('');
    }
  };

  return (
    <div className={`chat-window ${isExpanded ? 'expanded' : ''} ${isMobile ? 'mobile' : ''}`}>
      <div className="chat-header">
        <h3 className="text-lg font-semibold text-gray-800">Chat Assistant</h3>
        <div className="header-actions">
          {/* Expand/Collapse button - only show on desktop/tablet, not on mobile */}
          {!isMobile && onToggleExpand && (
            <button
              onClick={onToggleExpand}
              className="expand-button"
              aria-label={isExpanded ? 'Collapse' : 'Expand'}
              title={isExpanded ? 'Collapse (ESC)' : 'Expand'}
            >
              {isExpanded ? (
                // Collapse icon
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="4 14 10 14 10 20"></polyline>
                  <polyline points="20 10 14 10 14 4"></polyline>
                  <line x1="14" y1="10" x2="21" y2="3"></line>
                  <line x1="3" y1="21" x2="10" y2="14"></line>
                </svg>
              ) : (
                // Expand icon
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="15 3 21 3 21 9"></polyline>
                  <polyline points="9 21 3 21 3 15"></polyline>
                  <line x1="21" y1="3" x2="14" y2="10"></line>
                  <line x1="3" y1="21" x2="10" y2="14"></line>
                </svg>
              )}
            </button>
          )}
          <button 
            onClick={onClose}
            className="close-button text-gray-500 hover:text-gray-700"
            aria-label="Close chat"
          >
            ×
          </button>
        </div>
      </div>
      
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="welcome-message">
            <p className="text-gray-600">👋 Hello! How can I help you today?</p>
          </div>
        )}
        
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        
        {isTyping && <TypingIndicator />}
        
        <div ref={messagesEndRef} />
      </div>
      
      <form onSubmit={handleSubmit} className="chat-input-form">
        <div className="input-container">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Type your message..."
            className="chat-input"
            autoFocus
          />
          <button
            type="submit"
            disabled={!inputValue.trim()}
            className="send-button"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
};
