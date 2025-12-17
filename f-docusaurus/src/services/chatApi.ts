/**
 * API client for chat backend communication
 */
import { ChatRequest, ChatResponse } from '../components/ChatWidget/types';

// Backend API URL (will be updated after deploying Python backend)
const API_BASE_URL = 'http://localhost:8000';

export class ChatApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public details?: unknown
  ) {
    super(message);
    this.name = 'ChatApiError';
  }
}

/**
 * Send a message to the chat API and get AI response
 */
export async function sendMessage(
  message: string,
  sessionId?: string,
  contextMessages?: Array<{ role: string; content: string }>
): Promise<ChatResponse> {
  try {
    const requestBody: ChatRequest = {
      message: message.trim(),
      session_id: sessionId,
      context_messages: contextMessages,
    };

    const response = await fetch(`${API_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({
        error: `HTTP ${response.status}: ${response.statusText}`,
      }));

      throw new ChatApiError(
        errorData.error || 'Failed to get response from chat API',
        response.status,
        errorData.details
      );
    }

    const data = await response.json();

    // Map backend response format to frontend format
    // Backend returns: { answer: string, processing_time: number }
    // Frontend expects: { reply: string, citations?: Citation[] }
    const mappedResponse: ChatResponse = {
      reply: data.answer || data.reply || '', // Support both formats
      citations: data.citations || [], // Citations may not be provided by backend
    };

    return mappedResponse;
  } catch (error) {
    if (error instanceof ChatApiError) {
      throw error;
    }

    // Network errors or other issues
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new ChatApiError(
        'Unable to connect to chat service. Please check your connection.',
        undefined,
        error
      );
    }

    throw new ChatApiError(
      'An unexpected error occurred while communicating with the chat service.',
      undefined,
      error
    );
  }
}

/**
 * Check if the chat API is available
 */
export async function healthCheck(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
    });
    return response.ok;
  } catch {
    return false;
  }
}
