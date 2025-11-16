export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  productOptions?: number[];
}

export interface ChatMessageRequest {
  message: string;
  conversation_delete?: boolean;
}

export interface ChatMessageResponse {
  Answers: string;
  Options?: number[];
}

export interface ChatError {
  message: string;
  code?: string;
}
