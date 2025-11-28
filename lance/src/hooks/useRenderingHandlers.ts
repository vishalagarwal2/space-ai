import { useCallback } from "react";
import { toast } from "sonner";
import { Message } from "./useChatMessages";

export function useRenderingHandlers(
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>
) {
  const handleRenderingComplete = useCallback(
    (messageId: string) => (imageData: string) => {
      setMessages(prev =>
        prev.map(msg =>
          msg.id === messageId ? { ...msg, renderedImageUrl: imageData } : msg
        )
      );
    },
    [setMessages]
  );

  const handleRenderingError = useCallback(
    (messageId: string) => (error: string, stepId: string) => {
      console.error(
        `Rendering error for message ${messageId} in step ${stepId}:`,
        error
      );
      toast.error(`Rendering failed: ${error}`);
    },
    []
  );

  return {
    handleRenderingComplete,
    handleRenderingError,
  };
}
