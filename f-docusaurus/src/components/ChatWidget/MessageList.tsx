/**
 * Message list component displaying chat history
 */
import React, { useEffect, useRef } from 'react';
import { ChatMessage } from './types';
import styles from './styles.module.css';

interface MessageListProps {
  messages: ChatMessage[];
  isLoading: boolean;
}

export default function MessageList({ messages, isLoading }: MessageListProps): JSX.Element {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className={styles.messageList}>
      {messages.length === 0 && !isLoading && (
        <div className={styles.emptyState}>
          <p>👋 Hi! Ask me anything about the documentation.</p>
        </div>
      )}

      {messages.map((message) => (
        <div
          key={message.id}
          className={`${styles.message} ${styles[message.sender]}`}
        >
          <div className={styles.messageText}>
            {message.text}
          </div>
          {message.citations && message.citations.length > 0 && (
            <div className={styles.citations}>
              <strong>Sources:</strong>
              {message.citations.map((citation, idx) => (
                <a
                  key={idx}
                  href={citation.url}
                  className={styles.citationLink}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  [{citation.source_number}] {citation.section}
                </a>
              ))}
            </div>
          )}
        </div>
      ))}

      {isLoading && (
        <div className={`${styles.message} ${styles.ai}`}>
          <div className={styles.loadingIndicator}>
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  );
}
