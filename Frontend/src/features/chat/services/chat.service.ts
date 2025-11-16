import { apiClient, API_ENDPOINTS } from '@/core/api';
import type { ChatMessageRequest, ChatMessageResponse } from '../types/chat.types';

class ChatService {
  /**
   * Send a message to the chatbot and get a response
   * @param message - The user's message
   * @param conversationDelete - Whether to delete conversation history after this message
   * @returns Promise with the chatbot's response
   */
  async sendMessage(
    message: string,
    conversationDelete: boolean = false
  ): Promise<ChatMessageResponse> {
    const requestBody: ChatMessageRequest = {
      message,
      conversation_delete: conversationDelete,
    };

    return apiClient.post<ChatMessageResponse>(
      API_ENDPOINTS.CHAT_MESSAGE,
      requestBody
    );
  }

  /**
   * Clear the conversation history
   * @returns Promise with status confirmation
   */
  async clearConversation(): Promise<{ status: string; message: string }> {
    return apiClient.post<{ status: string; message: string }>(
      API_ENDPOINTS.CHAT_CLEAR
    );
  }
}

export const chatService = new ChatService();
