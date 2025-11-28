import axiosInstance from "../axios";

// Types for social media chat
export interface SocialMediaConversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface SocialMediaMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
  metadata?: Record<string, any>;
}

export interface CreateConversationRequest {
  title?: string;
  social_account_id?: string;
}

export interface SendMessageRequest {
  content: string;
  conversation_id?: string;
}

export interface SendMessageResponse {
  success: boolean;
  data: {
    message: SocialMediaMessage;
    conversation_id: string;
  };
  error?: string;
}

// Create a new social media conversation
export const createSocialMediaConversation = async (
  payload: CreateConversationRequest
) => {
  return axiosInstance.post("/api/social-media/conversations/", payload);
};

// Get all social media conversations for the user
export const getSocialMediaConversations = async () => {
  return axiosInstance.get("/api/social-media/conversations/");
};

// Get a specific conversation with messages
export const getSocialMediaConversation = async (conversationId: string) => {
  return axiosInstance.get(
    `/api/social-media/conversations/${conversationId}/`
  );
};

// Send a message to a conversation
export const sendSocialMediaMessage = async (payload: SendMessageRequest) => {
  return axiosInstance.post(
    "/api/social-media/conversations/messages/",
    payload
  );
};

// Get messages for a specific conversation
export const getSocialMediaMessages = async (conversationId: string) => {
  return axiosInstance.get(
    `/api/social-media/conversations/${conversationId}/messages/`
  );
};

// Delete a conversation
export const deleteSocialMediaConversation = async (conversationId: string) => {
  return axiosInstance.delete(
    `/api/social-media/conversations/${conversationId}/`
  );
};

// Generate Instagram post with AI
export const generateInstagramPost = async (payload: {
  user_request: string;
  social_account_id?: string;
  conversation_id?: string;
}) => {
  return axiosInstance.post(
    "/api/social-media/instagram/generate-post/",
    payload
  );
};

// Get user's social media posts
export const getSocialMediaPosts = async () => {
  return axiosInstance.get("/api/social-media/posts/");
};

// Approve a generated post
export const approveSocialMediaPost = async (postId: string) => {
  return axiosInstance.post(`/api/social-media/posts/${postId}/approve/`);
};

// Reject a generated post
export const rejectSocialMediaPost = async (
  postId: string,
  feedback: string
) => {
  return axiosInstance.post(`/api/social-media/posts/${postId}/reject/`, {
    feedback,
  });
};

// Post to Instagram
export const postToInstagram = async (postId: string) => {
  return axiosInstance.post(`/api/social-media/posts/${postId}/post/`);
};

// Get post preview
export const getPostPreview = async (postId: string) => {
  return axiosInstance.get(`/api/social-media/posts/${postId}/preview/`);
};

// Instagram Post Types
export interface InstagramPost {
  id: number;
  caption: string;
  media_url: string;
  media_type: "image" | "video";
  status: "draft" | "scheduled" | "posted" | "failed";
  instagram_post_id?: string;
  scheduled_at?: string;
  posted_at?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateInstagramPostRequest {
  caption?: string;
  media: File;
}

// Create a new Instagram post with media upload
export const createInstagramPost = async (
  payload: CreateInstagramPostRequest
) => {
  const formData = new FormData();
  formData.append("media", payload.media);
  if (payload.caption) {
    formData.append("caption", payload.caption);
  }

  return axiosInstance.post("/api/instagram-posts/create/", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
};

// Get all Instagram posts for the user
export const getInstagramPosts = async () => {
  return axiosInstance.get("/api/instagram-posts/");
};

// Post to Instagram (dummy implementation)
export const postToInstagramAPI = async (postId: number | string) => {
  // Try sending as JSON instead of FormData
  return axiosInstance.post("/api/instagram-posts/post/", {
    post_id: postId.toString(),
  });
};
