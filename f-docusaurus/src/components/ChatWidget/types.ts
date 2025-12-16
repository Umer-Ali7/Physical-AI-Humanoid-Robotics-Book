/**
 * TypeScript interfaces for ChatWidget components
 */

export interface Citation {
  section: string;
  url: string;
  source_number: number;
  relevance_score?: number;
}

export interface ChatMessage {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  timestamp: number;
  citations?: Citation[];
}

export interface ChatWidgetProps {
  // Props can be extended in future
}

export interface ChatResponse {
  reply: string;
  citations?: Citation[];
}

export interface ChatRequest {
  message: string;
  session_id?: string;
  context_messages?: Array<{role: string; content: string}>;
}
