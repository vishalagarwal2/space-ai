import axiosInstance from "../axios";

// Types for chat functionality
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
  metadata?: Record<string, any>;
}

export interface ChatConversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  agent_name?: string;
}

export interface SendMessageRequest {
  content: string;
  conversation_id?: string;
  agent_id?: string;
}

export interface SendMessageResponse {
  success: boolean;
  data: {
    message: ChatMessage;
    conversation_id: string;
    response?: string;
  };
  error?: string;
}

// Send a message using the existing knowledge base chat endpoint
export const sendChatMessage = async (payload: SendMessageRequest) => {
  return axiosInstance.post("/api/knowledge-base/chat/send/", payload);
};

// Get all conversations for the user
export const getChatConversations = async () => {
  return axiosInstance.get("/api/knowledge-base/conversations/");
};

// Get a specific conversation with messages
export const getChatConversation = async (conversationId: string) => {
  return axiosInstance.get(`/api/knowledge-base/conversations/${conversationId}/`);
};

// Delete a conversation
export const deleteChatConversation = async (conversationId: string) => {
  return axiosInstance.delete(`/api/knowledge-base/conversations/${conversationId}/delete/`);
};

// Create a new conversation
export const createChatConversation = async (payload: {
  title?: string;
  agent_id?: string;
}) => {
  return axiosInstance.post("/api/knowledge-base/conversations/", payload);
};
