import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Extracts a user-friendly error message from various error types.
 * Handles Axios errors, Error objects, and other unknown error types.
 *
 * @param error - The error to extract a message from
 * @param defaultMessage - Optional default message if no error message can be extracted
 * @returns A string error message suitable for display to users
 *
 * @example
 * ```ts
 * try {
 *   await apiCall();
 * } catch (error) {
 *   const message = extractErrorMessage(error);
 *   toast.error(message);
 * }
 * ```
 */
export function extractErrorMessage(
  error: unknown,
  defaultMessage: string = "An unexpected error occurred"
): string {
  if (!error) {
    return defaultMessage;
  }

  if (error && typeof error === "object" && "response" in error) {
    const errorObj = error as {
      response?: {
        data?: {
          error?: string;
          message?: string;
          detail?: string;
        };
      };
      message?: string;
    };

    return (
      errorObj.response?.data?.error ||
      errorObj.response?.data?.message ||
      errorObj.response?.data?.detail ||
      errorObj.message ||
      defaultMessage
    );
  }

  if (error instanceof Error) {
    return error.message || defaultMessage;
  }

  if (typeof error === "string") {
    return error || defaultMessage;
  }

  try {
    const errorString = String(error);
    return errorString !== "[object Object]" ? errorString : defaultMessage;
  } catch {
    return defaultMessage;
  }
}
