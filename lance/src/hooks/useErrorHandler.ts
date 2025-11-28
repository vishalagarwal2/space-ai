import { useCallback } from "react";
import { toast } from "sonner";
import { handleApiError } from "@/lib/errorHandling";

export function useErrorHandler() {
  const handleError = useCallback((error: unknown, context?: string) => {
    const apiError = handleApiError(error);

    console.error(`Error${context ? ` in ${context}` : ""}:`, {
      message: apiError.message,
      status: apiError.status,
      code: apiError.code,
      details: apiError.details,
    });

    toast.error(apiError.message);

    return apiError;
  }, []);

  return { handleError };
}
