import { useState, useEffect } from "react";
import { toast } from "sonner";
import { createChatConversation } from "@/lib/api/chat";

interface ApiError {
  response?: {
    data?: {
      error?: string;
      message?: string;
    };
  };
  message?: string;
}

export function useChatConversation() {
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);

  useEffect(() => {
    const initializeConversation = async () => {
      try {
        setIsInitializing(true);

        const response = await createChatConversation({
          title: "Social Media Post Creation",
          agent_id: undefined,
        });

        if (response.data.success) {
          const conversation = response.data.data;
          setConversationId(conversation.id);
        } else {
          throw new Error(
            response.data.error || "Failed to create conversation"
          );
        }
      } catch (error: unknown) {
        console.error("Error initializing conversation:", error);

        const apiError = error as ApiError;
        const errorMessage =
          apiError?.response?.data?.error ||
          apiError?.response?.data?.message ||
          apiError?.message ||
          "Failed to initialize chat. Please try again.";

        toast.error(errorMessage);
      } finally {
        setIsInitializing(false);
      }
    };

    initializeConversation();
  }, []);

  return { conversationId, setConversationId, isInitializing };
}

