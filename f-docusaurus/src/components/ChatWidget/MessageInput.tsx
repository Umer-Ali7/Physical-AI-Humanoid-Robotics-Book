/**
 * Message input component with text field and send button
 */
import React, { useState, KeyboardEvent } from 'react';
import styles from './styles.module.css';

interface MessageInputProps {
  onSend: (message: string) => void;
  disabled: boolean;
}

export default function MessageInput({ onSend, disabled }: MessageInputProps): JSX.Element {
  const [inputValue, setInputValue] = useState('');

  const handleSend = () => {
    if (inputValue.trim() && !disabled) {
      onSend(inputValue.trim());
      setInputValue('');
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className={styles.messageInput}>
      <input
        type="text"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyPress={handleKeyPress}
        placeholder="Ask a question..."
        disabled={disabled}
        className={styles.input}
        maxLength={500}
      />
      <button
        onClick={handleSend}
        disabled={disabled || !inputValue.trim()}
        className={styles.sendButton}
        aria-label="Send message"
      >
        ➤
      </button>
    </div>
  );
}
