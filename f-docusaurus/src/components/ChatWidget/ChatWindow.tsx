/**
 * Chat window container component
 */
import React from 'react';
import styles from './styles.module.css';

interface ChatWindowProps {
  onClose: () => void;
  children: React.ReactNode;
}

export default function ChatWindow({ onClose, children }: ChatWindowProps): JSX.Element {
  return (
    <div className={styles.chatWindow}>
      <div className={styles.chatHeader}>
        <strong>Documentation Chat</strong>
        <button
          onClick={onClose}
          className={styles.closeButton}
          aria-label="Close chat"
        >
          ✕
        </button>
      </div>
      <div className={styles.chatContent}>
        {children}
      </div>
    </div>
  );
}
