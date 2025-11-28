import { useState, useRef, useEffect } from "react";
import { toast } from "sonner";
import { sendChatMessage } from "@/lib/api/chat";
import {
  generateSocialMediaPost,
  SocialMediaPost,
} from "@/lib/api/socialMediaPosts";
import { LayoutJSON } from "@/types/Layout";
import type { BusinessProfile } from "@/constants/mockBusinessProfiles";

interface ApiError {
  response?: {
    data?: {
      error?: string;
      message?: string;
    };
  };
  message?: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  postPreview?: SocialMediaPost;
  layoutJson?: LayoutJSON;
  renderingSteps?: unknown[];
  renderedImageUrl?: string;
  isPublished?: boolean;
}

const WELCOME_MESSAGE: Message = {
  id: "welcome",
  role: "assistant",
  content:
    "Hi! I'm your AI social media assistant. I can help you create engaging Instagram posts for your business. What kind of post would you like to create today?",
  timestamp: new Date(),
};

export function useChatMessages(
  conversationId: string | null,
  setConversationId: (id: string) => void,
  businessProfile: BusinessProfile | null,
  isInitializing: boolean,
  selectedBusinessProfile?: BusinessProfile
) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isGeneratingPost, setIsGeneratingPost] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (!isInitializing) {
      setMessages([WELCOME_MESSAGE]);
    }
  }, [isInitializing]);

  const sendMessage = async (content: string) => {
    if (!content.trim() || isLoading || isInitializing || isGeneratingPost)
      return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: content,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    const isPostRequest =
      content.toLowerCase().includes("post") ||
      content.toLowerCase().includes("create") ||
      content.toLowerCase().includes("make") ||
      content.toLowerCase().includes("generate");

    if (isPostRequest && (businessProfile || selectedBusinessProfile)) {
      try {
        setIsGeneratingPost(true);

        const response = await generateSocialMediaPost({
          user_input: content,
          conversation_id: conversationId || undefined,
          business_profile: selectedBusinessProfile
            ? {
                company_name:
                  selectedBusinessProfile.companyName ||
                  selectedBusinessProfile.name,
                industry:
                  selectedBusinessProfile.brandGuidelines?.industry || "",
                brand_voice:
                  selectedBusinessProfile.brandGuidelines?.tagline || "",
                target_audience: "", // Add if available in mock profiles
                primary_color:
                  selectedBusinessProfile.colorPalette?.primary || "",
                secondary_color:
                  selectedBusinessProfile.colorPalette?.secondary || "",
                font_family:
                  selectedBusinessProfile.brandGuidelines?.fontFamily || "",
                logo_url:
                  selectedBusinessProfile.postLogoUrl ||
                  selectedBusinessProfile.logoUrl ||
                  "",
              }
            : undefined,
        });

        if (response.data.status === "success" && response.data.data) {
          const postData = response.data.data;

          let layoutJson: LayoutJSON | undefined;
          try {
            if (postData.layout_json) {
              layoutJson = JSON.parse(postData.layout_json);
            }
          } catch {
            // Failed to parse layout_json, continue without it
          }

          const assistantMessage: Message = {
            id: response.data.data.id,
            role: "assistant",
            content: layoutJson
              ? "I've created a social post for you. Here's a preview of how it looks:"
              : "I've created a social media post for you! Here's what I generated:",
            timestamp: new Date(),
            postPreview: postData,
            layoutJson: layoutJson,
            isPublished: postData.status === "published",
          };

          setMessages(prev => [...prev, assistantMessage]);
        } else {
          throw new Error(response.data.message || "Failed to generate post");
        }
      } catch (error: unknown) {
        const apiError = error as ApiError;
        const errorMessage =
          apiError?.response?.data?.message ||
          apiError?.message ||
          "Failed to generate post. Please try again.";

        toast.error(errorMessage);

        const errorMessageObj: Message = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content:
            "I'm sorry, I couldn't generate a post right now. Please try again in a moment.",
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, errorMessageObj]);
      } finally {
        setIsGeneratingPost(false);
        setIsLoading(false);
      }
    } else {
      try {
        const payload: { content: string; conversation_id?: string } = {
          content: content,
        };
        if (conversationId) {
          payload.conversation_id = conversationId;
        }

        const response = await sendChatMessage(payload);

        if (response.data.success) {
          const assistantMessage: Message = {
            id: response.data.data.message.id,
            role: "assistant",
            content:
              response.data.data.response || response.data.data.message.content,
            timestamp: new Date(response.data.data.message.created_at),
          };
          setMessages(prev => [...prev, assistantMessage]);

          if (response.data.data.conversation_id && !conversationId) {
            setConversationId(response.data.data.conversation_id);
          }
        } else {
          throw new Error(response.data.error || "Failed to send message");
        }
      } catch (error: unknown) {
        const apiError = error as ApiError;
        const errorMessage =
          apiError?.response?.data?.error ||
          apiError?.response?.data?.message ||
          apiError?.message ||
          "Failed to send message. Please try again.";

        toast.error(errorMessage);

        const errorMessageObj: Message = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content:
            "I'm sorry, I'm having trouble processing your request right now. Please try again in a moment.",
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, errorMessageObj]);
      } finally {
        setIsLoading(false);
      }
    }
  };

  return {
    messages,
    setMessages,
    isLoading,
    isGeneratingPost,
    messagesEndRef,
    sendMessage,
  };
}
