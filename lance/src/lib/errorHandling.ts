import { AxiosError } from "axios";

export interface ApiError {
  message: string;
  status?: number;
  code?: string;
  details?: unknown;
}

export function handleApiError(error: unknown): ApiError {
  if (error instanceof AxiosError) {
    const status = error.response?.status;
    const data = error.response?.data;

    switch (status) {
      case 400:
        return {
          message: data?.error || "Bad request. Please check your input.",
          status: 400,
          code: "BAD_REQUEST",
          details: data,
        };
      case 401:
        return {
          message: "You are not authorized. Please log in again.",
          status: 401,
          code: "UNAUTHORIZED",
        };
      case 403:
        return {
          message: "You don't have permission to perform this action.",
          status: 403,
          code: "FORBIDDEN",
        };
      case 404:
        return {
          message: "The requested resource was not found.",
          status: 404,
          code: "NOT_FOUND",
        };
      case 409:
        return {
          message:
            data?.error ||
            "Conflict. The resource already exists or is in use.",
          status: 409,
          code: "CONFLICT",
          details: data,
        };
      case 422:
        return {
          message: data?.error || "Invalid data provided.",
          status: 422,
          code: "VALIDATION_ERROR",
          details: data,
        };
      case 429:
        return {
          message: "Too many requests. Please try again later.",
          status: 429,
          code: "RATE_LIMITED",
        };
      case 500:
        return {
          message: "Internal server error. Please try again later.",
          status: 500,
          code: "SERVER_ERROR",
        };
      case 502:
      case 503:
      case 504:
        return {
          message: "Service temporarily unavailable. Please try again later.",
          status,
          code: "SERVICE_UNAVAILABLE",
        };
      default:
        return {
          message:
            data?.error || error.message || "An unexpected error occurred.",
          status,
          code: "UNKNOWN_ERROR",
          details: data,
        };
    }
  }

  // Network error
  if (error instanceof Error) {
    if (
      error.message.includes("Network Error") ||
      error.message.includes("ERR_NETWORK")
    ) {
      return {
        message: "Network error. Please check your internet connection.",
        code: "NETWORK_ERROR",
      };
    }

    return {
      message: error.message,
      code: "GENERIC_ERROR",
    };
  }

  // Unknown error
  return {
    message: "An unexpected error occurred.",
    code: "UNKNOWN_ERROR",
  };
}

export function isRetryableError(error: unknown): boolean {
  if (error instanceof AxiosError) {
    const status = error.response?.status;

    // Don't retry client errors (4xx) except for 408, 429
    if (status && status >= 400 && status < 500) {
      return status === 408 || status === 429;
    }

    // Retry server errors (5xx)
    if (status && status >= 500) {
      return true;
    }

    // Retry network errors
    return !error.response;
  }

  return false;
}
