/**
 * Floating chat button component
 */
import React from 'react';
import styles from './styles.module.css';

interface ChatButtonProps {
  onClick: () => void;
  isOpen: boolean;
}

export default function ChatButton({ onClick, isOpen }: ChatButtonProps): JSX.Element {
  return (
    <button
      onClick={onClick}
      className={styles.chatButton}
      aria-label={isOpen ? "Close chat" : "Open chat"}
    >
      {isOpen ? '✕' : '💬'}
    </button>
  );
}
