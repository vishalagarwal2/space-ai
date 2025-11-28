/**
 * Content Calendar Hooks
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  generateContentCalendar,
  getContentCalendars,
  approveContentIdea,
  unscheduleContentIdea,
  updateContentIdea,
  deleteContentCalendar,
} from "@/lib/api/contentCalendar";
import type {
  GenerateContentCalendarRequest,
  UpdateContentIdeaRequest,
  ContentCalendar,
  ContentIdea,
} from "@/types/ContentCalendar";

interface ApiError {
  response?: {
    data?: {
      error?: string;
    };
  };
  message?: string;
}

export const contentCalendarKeys = {
  all: ["content-calendar"] as const,
  calendars: (businessProfileId?: string) =>
    [...contentCalendarKeys.all, "list", businessProfileId || "all"] as const,
  calendar: (id: string) => [...contentCalendarKeys.all, "detail", id] as const,
  posts: () => [...contentCalendarKeys.all, "posts"] as const,
  post: (ideaId: string) => [...contentCalendarKeys.posts(), ideaId] as const,
};

/**
 * Hook to fetch all content calendars, optionally filtered by business profile
 */
export function useContentCalendars(businessProfileId?: string) {
  return useQuery({
    queryKey: contentCalendarKeys.calendars(businessProfileId),
    queryFn: async (): Promise<ContentCalendar[]> => {
      const response = await getContentCalendars(businessProfileId);
      if (!response.success || !response.data) {
        throw new Error(response.error || "Failed to fetch content calendars");
      }
      return response.data.calendars;
    },
    staleTime: 2 * 60 * 1000, // Increased to 2 minutes for less aggressive polling
    gcTime: 10 * 60 * 1000, // Keep in cache for 10 minutes
    retry: 3, // Retry failed requests 3 times
    retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000), // Exponential backoff
  });
}

/**
 * Hook to generate a new content calendar
 */
export function useGenerateContentCalendar() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (
      request: GenerateContentCalendarRequest
    ): Promise<ContentCalendar> => {
      const response = await generateContentCalendar(request);
      if (!response.success || !response.data) {
        throw new Error(
          response.error || "Failed to generate content calendar"
        );
      }
      return response.data.calendar;
    },
    onSuccess: data => {
      toast.success(
        `Content calendar generated successfully for ${data.title}!`
      );
      queryClient.invalidateQueries({
        queryKey: contentCalendarKeys.all,
        refetchType: "active",
      });
    },
    onError: (error: unknown) => {
      const apiError = error as ApiError;
      const message =
        apiError?.response?.data?.error ||
        apiError?.message ||
        "Failed to generate content calendar";
      toast.error(message);
    },
  });
}

/**
 * Hook to approve a content idea
 */
export function useApproveContentIdea(
  onSuccessCallback?: (updatedIdea: ContentIdea) => void
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (ideaId: string) => {
      const response = await approveContentIdea(ideaId);
      if (!response.success || !response.data) {
        throw new Error(response.error || "Failed to approve content idea");
      }
      return response.data;
    },
    onSuccess: updatedIdea => {
      toast.success("Content idea approved successfully!");

      // Invalidate all calendar queries since we don't know which business profile this belongs to
      queryClient.invalidateQueries({
        queryKey: contentCalendarKeys.all,
        refetchType: "active",
      });

      if (onSuccessCallback) {
        onSuccessCallback(updatedIdea);
      }
    },
    onError: (error: unknown) => {
      const apiError = error as ApiError;
      const message =
        apiError?.response?.data?.error ||
        apiError?.message ||
        "Failed to approve content idea";
      toast.error(message);
    },
  });
}

/**
 * Hook to unschedule a content idea
 */
export function useUnscheduleContentIdea(
  onSuccessCallback?: (updatedIdea: ContentIdea) => void
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (ideaId: string) => {
      const response = await unscheduleContentIdea(ideaId);
      if (!response.success || !response.data) {
        throw new Error(response.error || "Failed to unschedule content idea");
      }
      return response.data;
    },
    onSuccess: updatedIdea => {
      toast.success("Content idea unscheduled successfully!");

      // Invalidate all calendar queries since we don't know which business profile this belongs to
      queryClient.invalidateQueries({
        queryKey: contentCalendarKeys.all,
        refetchType: "active",
      });

      if (onSuccessCallback) {
        onSuccessCallback(updatedIdea);
      }
    },
    onError: (error: unknown) => {
      const apiError = error as ApiError;
      const message =
        apiError?.response?.data?.error ||
        apiError?.message ||
        "Failed to unschedule content idea";
      toast.error(message);
    },
  });
}

/**
 * Hook to update a content idea
 */
export function useUpdateContentIdea() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      ideaId,
      updates,
    }: {
      ideaId: string;
      updates: UpdateContentIdeaRequest;
    }) => {
      const response = await updateContentIdea(ideaId, updates);
      if (!response.success || !response.data) {
        throw new Error(response.error || "Failed to update content idea");
      }
      return { ideaId, updates, data: response.data };
    },
    onSuccess: () => {
      toast.success("Content idea updated successfully!");

      queryClient.invalidateQueries({
        queryKey: contentCalendarKeys.all,
        refetchType: "active",
      });

      queryClient.invalidateQueries({
        queryKey: contentCalendarKeys.posts(),
      });

      setTimeout(() => {
        queryClient.refetchQueries({
          queryKey: contentCalendarKeys.all,
          type: "active",
        });
      }, 200);
    },
    onError: (error: unknown) => {
      const apiError = error as ApiError;
      const message =
        apiError?.response?.data?.error ||
        apiError?.message ||
        "Failed to update content idea";
      toast.error(message);
    },
  });
}

/**
 * Hook to delete a content calendar
 */
export function useDeleteContentCalendar() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (calendarId: string) => {
      const response = await deleteContentCalendar(calendarId);
      if (!response.success) {
        throw new Error(response.error || "Failed to delete content calendar");
      }
      return response;
    },
    onSuccess: () => {
      toast.success("Content calendar deleted successfully!");
      queryClient.removeQueries({
        queryKey: contentCalendarKeys.all,
      });
      queryClient.invalidateQueries({
        queryKey: contentCalendarKeys.all,
        refetchType: "active",
      });
    },
    onError: (error: unknown) => {
      const apiError = error as ApiError;
      const message =
        apiError?.response?.data?.error ||
        apiError?.message ||
        "Failed to delete content calendar";
      toast.error(message);
    },
  });
}
