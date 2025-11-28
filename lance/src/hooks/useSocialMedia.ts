import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  createSocialMediaConversation,
  getSocialMediaConversations,
  getSocialMediaConversation,
  sendSocialMediaMessage,
  getSocialMediaMessages,
  deleteSocialMediaConversation,
  generateInstagramPost,
  getSocialMediaPosts,
  approveSocialMediaPost,
  rejectSocialMediaPost,
  postToInstagram,
  getPostPreview,
  SocialMediaConversation,
  SocialMediaMessage,
  CreateConversationRequest,
  SendMessageRequest,
  SendMessageResponse,
} from "@/lib/api/socialMedia";

interface ApiError {
  response?: {
    data?: {
      error?: string;
    };
  };
  message?: string;
}

export const socialMediaKeys = {
  all: ["socialMedia"] as const,
  conversations: () => [...socialMediaKeys.all, "conversations"] as const,
  conversation: (id: string) =>
    [...socialMediaKeys.all, "conversation", id] as const,
  messages: (id: string) => [...socialMediaKeys.all, "messages", id] as const,
  posts: () => [...socialMediaKeys.all, "posts"] as const,
  post: (id: string) => [...socialMediaKeys.all, "post", id] as const,
};

export function useSocialMediaConversations() {
  return useQuery({
    queryKey: socialMediaKeys.conversations(),
    queryFn: async (): Promise<SocialMediaConversation[]> => {
      const response = await getSocialMediaConversations();
      return response.data;
    },
    staleTime: 2 * 60 * 1000,
  });
}

export function useSocialMediaConversation(conversationId: string) {
  return useQuery({
    queryKey: socialMediaKeys.conversation(conversationId),
    queryFn: async (): Promise<{
      conversation: SocialMediaConversation;
      messages: SocialMediaMessage[];
    }> => {
      const response = await getSocialMediaConversation(conversationId);
      return response.data;
    },
    enabled: !!conversationId,
    staleTime: 1 * 60 * 1000,
  });
}

export function useSocialMediaMessages(conversationId: string) {
  return useQuery({
    queryKey: socialMediaKeys.messages(conversationId),
    queryFn: async (): Promise<SocialMediaMessage[]> => {
      const response = await getSocialMediaMessages(conversationId);
      return response.data;
    },
    enabled: !!conversationId,
    staleTime: 1 * 60 * 1000,
  });
}

export function useCreateSocialMediaConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: CreateConversationRequest) => {
      const response = await createSocialMediaConversation(payload);
      return response.data;
    },
    onSuccess: () => {
      toast.success("Conversation created successfully!");
      queryClient.invalidateQueries({
        queryKey: socialMediaKeys.conversations(),
      });
    },
    onError: (error: unknown) => {
      const apiError = error as ApiError;
      const message =
        apiError?.response?.data?.error || "Failed to create conversation";
      toast.error(message);
    },
  });
}

export function useSendSocialMediaMessage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (
      payload: SendMessageRequest
    ): Promise<SendMessageResponse> => {
      const response = await sendSocialMediaMessage(payload);
      return response.data;
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({
        queryKey: socialMediaKeys.conversations(),
      });

      if (variables.conversation_id) {
        queryClient.invalidateQueries({
          queryKey: socialMediaKeys.conversation(variables.conversation_id),
        });
        queryClient.invalidateQueries({
          queryKey: socialMediaKeys.messages(variables.conversation_id),
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

export function useDeleteSocialMediaConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (conversationId: string) => {
      const response = await deleteSocialMediaConversation(conversationId);
      return response.data;
    },
    onSuccess: (_, conversationId) => {
      toast.success("Conversation deleted successfully!");
      queryClient.removeQueries({
        queryKey: socialMediaKeys.conversation(conversationId),
      });
      queryClient.removeQueries({
        queryKey: socialMediaKeys.messages(conversationId),
      });
      queryClient.invalidateQueries({
        queryKey: socialMediaKeys.conversations(),
      });
    },
    onError: (error: unknown) => {
      const apiError = error as ApiError;
      const message =
        apiError?.response?.data?.error || "Failed to delete conversation";
      toast.error(message);
    },
  });
}

export function useSocialMediaPosts() {
  return useQuery({
    queryKey: socialMediaKeys.posts(),
    queryFn: async () => {
      const response = await getSocialMediaPosts();
      return response.data;
    },
    staleTime: 2 * 60 * 1000,
  });
}

export function useGenerateInstagramPost() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: {
      user_request: string;
      social_account_id?: string;
      conversation_id?: string;
    }) => {
      const response = await generateInstagramPost(payload);
      return response.data;
    },
    onSuccess: () => {
      toast.success("Instagram post generated successfully!");
      queryClient.invalidateQueries({ queryKey: socialMediaKeys.posts() });
    },
    onError: (error: unknown) => {
      const apiError = error as ApiError;
      const message =
        apiError?.response?.data?.error || "Failed to generate post";
      toast.error(message);
    },
  });
}

export function useApproveSocialMediaPost() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (postId: string) => {
      const response = await approveSocialMediaPost(postId);
      return response.data;
    },
    onSuccess: () => {
      toast.success("Post approved successfully!");
      queryClient.invalidateQueries({ queryKey: socialMediaKeys.posts() });
    },
    onError: (error: unknown) => {
      const apiError = error as ApiError;
      const message =
        apiError?.response?.data?.error || "Failed to approve post";
      toast.error(message);
    },
  });
}

export function useRejectSocialMediaPost() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      postId,
      feedback,
    }: {
      postId: string;
      feedback: string;
    }) => {
      const response = await rejectSocialMediaPost(postId, feedback);
      return response.data;
    },
    onSuccess: () => {
      toast.success("Post rejected successfully!");
      queryClient.invalidateQueries({ queryKey: socialMediaKeys.posts() });
    },
    onError: (error: unknown) => {
      const apiError = error as ApiError;
      const message =
        apiError?.response?.data?.error || "Failed to reject post";
      toast.error(message);
    },
  });
}

export function usePostToInstagram() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (postId: string) => {
      const response = await postToInstagram(postId);
      return response.data;
    },
    onSuccess: () => {
      toast.success("Post published to Instagram successfully!");
      queryClient.invalidateQueries({ queryKey: socialMediaKeys.posts() });
    },
    onError: (error: unknown) => {
      const apiError = error as ApiError;
      const message =
        apiError?.response?.data?.error || "Failed to post to Instagram";
      toast.error(message);
    },
  });
}

export function usePostPreview(postId: string) {
  return useQuery({
    queryKey: socialMediaKeys.post(postId),
    queryFn: async () => {
      const response = await getPostPreview(postId);
      return response.data;
    },
    enabled: !!postId,
    staleTime: 5 * 60 * 1000,
  });
}
