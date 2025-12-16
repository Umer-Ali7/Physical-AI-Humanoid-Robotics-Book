/**
 * Main ChatWidget component integrating all chat functionality
 */
import React, { useState, useEffect, useCallback } from 'react';
import ChatButton from './ChatButton';
import ChatWindow from './ChatWindow';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import { ChatMessage, ChatWidgetProps } from './types';
import { sendMessage, ChatApiError } from '../../services/chatApi';
import styles from './styles.module.css';

// Generate unique session ID
function generateSessionId(): string {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

// Storage keys
const STORAGE_KEYS = {
  MESSAGES: 'chatWidget_messages',
  SESSION_ID: 'chatWidget_sessionId',
};

export default function ChatWidget(_props: ChatWidgetProps): JSX.Element {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  // Initialize session and restore messages from storage
  useEffect(() => {
    // Get or create session ID
    let storedSessionId = sessionStorage.getItem(STORAGE_KEYS.SESSION_ID);
    if (!storedSessionId) {
      storedSessionId = generateSessionId();
      sessionStorage.setItem(STORAGE_KEYS.SESSION_ID, storedSessionId);
    }
    setSessionId(storedSessionId);

    // Restore messages from storage
    const storedMessages = sessionStorage.getItem(STORAGE_KEYS.MESSAGES);
    if (storedMessages) {
      try {
        const parsed = JSON.parse(storedMessages);
        setMessages(parsed);
      } catch {
        // Invalid stored data, ignore
      }
    }
  }, []);

  // Persist messages to storage whenever they change
  useEffect(() => {
    if (messages.length > 0) {
      sessionStorage.setItem(STORAGE_KEYS.MESSAGES, JSON.stringify(messages));
    }
  }, [messages]);

  const handleToggle = useCallback(() => {
    setIsOpen((prev) => !prev);
    // Clear error when closing
    if (isOpen) {
      setError(null);
    }
  }, [isOpen]);

  const handleSendMessage = useCallback(
    async (messageText: string) => {
      // Clear any previous error
      setError(null);

      // Create user message
      const userMessage: ChatMessage = {
        id: `msg_${Date.now()}_user`,
        text: messageText,
        sender: 'user',
        timestamp: Date.now(),
      };

      // Add user message to UI immediately
      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);

      try {
        // Build context from recent messages (last 5 exchanges = 10 messages)
        const recentMessages = messages.slice(-10);
        const contextMessages = recentMessages.map((msg) => ({
          role: msg.sender === 'user' ? 'user' : 'assistant',
          content: msg.text,
        }));

        // Call API
        const response = await sendMessage(messageText, sessionId, contextMessages);

        // Create AI message with citations
        const aiMessage: ChatMessage = {
          id: `msg_${Date.now()}_ai`,
          text: response.reply,
          sender: 'ai',
          timestamp: Date.now(),
          citations: response.citations,
        };

        // Add AI response to UI
        setMessages((prev) => [...prev, aiMessage]);
      } catch (err) {
        let errorMessage = 'Failed to get response. Please try again.';

        if (err instanceof ChatApiError) {
          if (err.statusCode === 503) {
            errorMessage = 'The chat service is currently unavailable. Please try again later.';
          } else if (err.statusCode === 400) {
            errorMessage = 'Invalid request. Please check your message and try again.';
          } else {
            errorMessage = err.message;
          }
        }

        setError(errorMessage);

        // Add error message to chat
        const errorMsg: ChatMessage = {
          id: `msg_${Date.now()}_error`,
          text: `⚠️ ${errorMessage}`,
          sender: 'ai',
          timestamp: Date.now(),
        };

        setMessages((prev) => [...prev, errorMsg]);
      } finally {
        setIsLoading(false);
      }
    },
    [messages, sessionId]
  );

  return (
    <>
      {!isOpen && <ChatButton onClick={handleToggle} isOpen={isOpen} />}

      {isOpen && (
        <div className={styles.chatWidgetContainer}>
          <ChatWindow onClose={handleToggle}>
            {error && (
              <div className={styles.errorBanner}>
                <span>⚠️ {error}</span>
                <button
                  onClick={() => setError(null)}
                  className={styles.errorDismiss}
                  aria-label="Dismiss error"
                >
                  ✕
                </button>
              </div>
            )}
            <MessageList messages={messages} isLoading={isLoading} />
            <MessageInput onSend={handleSendMessage} disabled={isLoading} />
          </ChatWindow>
        </div>
      )}
    </>
  );
}
