export interface ProductOption {
  id: number;
  name: string;
  price: number;
  score: number;
}

export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  productOptions?: (number | ProductOption)[];
}

export interface ChatMessageRequest {
  message: string;
  conversation_delete?: boolean;
}

export interface ChatMessageResponse {
  Answers: string;
  Options?: (number | ProductOption)[];
}

export interface ChatError {
  message: string;
  code?: string;
}
