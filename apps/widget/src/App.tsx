import React from 'react';
import { WidgetButton } from './components/WidgetButton';
import { ChatWindow } from './components/ChatWindow';
import { useWidgetStore } from './stores/widgetStore';
import { useFullscreen } from './hooks/useFullscreen';
import { APIClient } from './utils/apiClient';
import { extractPageContext } from './utils/pageContext';
import type { WidgetConfig } from './types';
import './App.css';
import './styles/responsive.css';

const apiClient = new APIClient('http://localhost:8000');

interface AppProps {
  config?: WidgetConfig;
}

function App({ config }: AppProps) {
  const {
    isOpen,
    messages,
    isTyping,
    conversationId,
    isExpanded,
    setIsOpen,
    addMessage,
    updateMessage,
    setIsTyping,
    setConfig,
    setConversationId,
    setExpanded
  } = useWidgetStore();

  // Fullscreen hook for expand/collapse functionality
  const { isExpanded: isFullscreen, toggleExpanded, isMobile } = useFullscreen();

  // Sync fullscreen state with store
  React.useEffect(() => {
    setExpanded(isFullscreen);
  }, [isFullscreen, setExpanded]);

  // Generate persistent user_id and conversation_id
  const [userId] = React.useState(() => {
    const stored = localStorage.getItem('agent_widget_user_id');
    if (stored) return stored;
    const newId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem('agent_widget_user_id', newId);
    return newId;
  });

  React.useEffect(() => {
    if (config) {
      setConfig(config);
    }
  }, [config, setConfig]);

  // Initialize conversation_id when widget first opens
  React.useEffect(() => {
    if (isOpen && !conversationId) {
      const stored = sessionStorage.getItem('agent_widget_conversation_id');
      if (stored) {
        setConversationId(stored);
      } else {
        const newConvId = `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        setConversationId(newConvId);
        sessionStorage.setItem('agent_widget_conversation_id', newConvId);
      }
    }
  }, [isOpen, conversationId, setConversationId]);

  const handleToggleWidget = () => {
    setIsOpen(!isOpen);
  };

  const handleSendMessage = async (text: string) => {
    // Add user message
    addMessage({
      id: Date.now().toString(),
      content: text,
      role: 'user',
      timestamp: new Date()
    });

    // Set typing indicator
    setIsTyping(true);

    try {
      // Extract page context
      const context = extractPageContext();
      
      // Get agent ID from config (default to Essco agent if not specified)
      const agentId = config?.agentId || 'f168131d-7833-4f9c-ac8e-8a19b22c16f3';
      
      // Use conversation ID from store (or create new one)
      const currentConvId = conversationId || `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      if (!conversationId) {
        setConversationId(currentConvId);
        sessionStorage.setItem('agent_widget_conversation_id', currentConvId);
      }
      
      // Create placeholder message for streaming
      const assistantMessageId = (Date.now() + 1).toString();
      let streamedContent = '';  // Track streamed content
      
      console.log('[App] Adding placeholder message:', assistantMessageId);
      
      addMessage({
        id: assistantMessageId,
        content: '',
        role: 'assistant',
        timestamp: new Date(),
        citations: []
      });
      
      console.log('[App] Calling sendMessage with streaming...');
      
      // Send message to API with streaming enabled
      const response = await apiClient.sendMessage({
        content: text,
        context,
        userId  // Pass the persistent user_id
      }, currentConvId, agentId, (chunk) => {
        // Handle streaming chunks
        console.log('[App] Stream chunk received:', chunk);
        if (chunk.type === 'content' && chunk.content) {
          // Append new content
          streamedContent += chunk.content;
          console.log('[App] Updating message with content:', streamedContent.substring(0, 50) + '...');
          // Update the message with accumulated content
          updateMessage(assistantMessageId, {
            content: streamedContent
          });
        } else if (chunk.type === 'status') {
          // Optionally show status updates (e.g., "Retrieving context...")
          console.log('[App] Status:', chunk.content);
        }
      });

      console.log('[App] Stream complete, final response:', response);

      // Update final message with complete response and citations
      updateMessage(assistantMessageId, {
        content: response.content,
        citations: response.citations
      });
    } catch (error) {
      console.error('Error sending message:', error);
      
      // Add error message
      addMessage({
        id: (Date.now() + 1).toString(),
        content: 'Sorry, I encountered an error. Please try again.',
        role: 'assistant',
        timestamp: new Date()
      });
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="widget-container">
      <WidgetButton onClick={handleToggleWidget} />
      
      {isOpen && (
        <div className={`widget-overlay ${isExpanded ? 'expanded' : ''}`}>
          <ChatWindow
            messages={messages}
            isTyping={isTyping}
            isExpanded={isExpanded}
            isMobile={isMobile}
            onSendMessage={handleSendMessage}
            onClose={() => setIsOpen(false)}
            onToggleExpand={toggleExpanded}
          />
        </div>
      )}
    </div>
  );
}

export default App;
