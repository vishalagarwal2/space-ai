import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  sendChatMessage,
  getChatConversations,
  getChatConversation,
  deleteChatConversation,
  createChatConversation,
  ChatMessage,
  ChatConversation,
  SendMessageRequest,
  SendMessageResponse,
} from "@/lib/api/chat";

interface ApiError {
  response?: {
    data?: {
      error?: string;
    };
  };
  message?: string;
}

export const chatKeys = {
  all: ["chat"] as const,
  conversations: () => [...chatKeys.all, "conversations"] as const,
  conversation: (id: string) => [...chatKeys.all, "conversation", id] as const,
};

export function useChatConversations() {
  return useQuery({
    queryKey: chatKeys.conversations(),
    queryFn: async (): Promise<ChatConversation[]> => {
      const response = await getChatConversations();
      return response.data;
    },
    staleTime: 2 * 60 * 1000,
  });
}

export function useChatConversation(conversationId: string) {
  return useQuery({
    queryKey: chatKeys.conversation(conversationId),
    queryFn: async (): Promise<{
      conversation: ChatConversation;
      messages: ChatMessage[];
    }> => {
      const response = await getChatConversation(conversationId);
      return response.data;
    },
    enabled: !!conversationId,
    staleTime: 1 * 60 * 1000,
  });
}

export function useSendChatMessage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (
      payload: SendMessageRequest
    ): Promise<SendMessageResponse> => {
      const response = await sendChatMessage(payload);
      return response.data;
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: chatKeys.conversations() });

      if (variables.conversation_id) {
        queryClient.invalidateQueries({
          queryKey: chatKeys.conversation(variables.conversation_id),
        });
      }
    },
    onError: (error: unknown) => {
      const apiError = error as ApiError;
      const message =
        apiError?.response?.data?.error || "Failed to send message";
      toast.error(message);
    },
  });
}

export function useCreateChatConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: { title?: string; agent_id?: string }) => {
      const response = await createChatConversation(payload);
      return response.data;
    },
    onSuccess: () => {
      toast.success("Conversation created successfully!");
      queryClient.invalidateQueries({ queryKey: chatKeys.conversations() });
    },
    onError: (error: unknown) => {
      const apiError = error as ApiError;
      const message =
        apiError?.response?.data?.error || "Failed to create conversation";
      toast.error(message);
    },
  });
}

export function useDeleteChatConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (conversationId: string) => {
      const response = await deleteChatConversation(conversationId);
      return response.data;
    },
    onSuccess: (_, conversationId) => {
      toast.success("Conversation deleted successfully!");
      queryClient.removeQueries({
        queryKey: chatKeys.conversation(conversationId),
      });
      queryClient.invalidateQueries({ queryKey: chatKeys.conversations() });
    },
    onError: (error: unknown) => {
      const apiError = error as ApiError;
      const message =
        apiError?.response?.data?.error || "Failed to delete conversation";
      toast.error(message);
    },
  });
}
