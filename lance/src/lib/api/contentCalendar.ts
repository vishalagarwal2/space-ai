/**
 * Content Calendar API Service
 */

import axios from "axios";
import axiosInstance from "../axios";
import type {
  GenerateContentCalendarRequest,
  GenerateContentCalendarResponse,
  GetContentCalendarsResponse,
  UpdateContentIdeaRequest,
  ContentIdeaResponse,
  ContentIdea,
} from "@/types/ContentCalendar";
import type { SocialMediaPost } from "@/lib/api/socialMediaPosts";
import type { BusinessProfile } from "@/constants/mockBusinessProfiles";

/**
 * Generate a new content calendar for the upcoming month
 */
export async function generateContentCalendar(
  request: GenerateContentCalendarRequest
): Promise<GenerateContentCalendarResponse> {
  try {
    const response = await axiosInstance.post(
      "/api/content-calendar/generate/",
      request
    );

    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const axiosError = error as { response?: { data?: { error?: string } } };
      throw new Error(
        axiosError?.response?.data?.error ||
          "Failed to generate content calendar"
      );
    }
    throw error;
  }
}

/**
 * Get all content calendars for the current user, optionally filtered by business profile
 */
export async function getContentCalendars(
  businessProfileId?: string
): Promise<GetContentCalendarsResponse> {
  try {
    const params = businessProfileId
      ? { business_profile_id: businessProfileId }
      : {};
    const response = await axiosInstance.get("/api/content-calendar/", {
      params,
    });

    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const axiosError = error as { response?: { data?: { error?: string } } };
      throw new Error(
        axiosError?.response?.data?.error || "Failed to fetch content calendars"
      );
    }
    throw error;
  }
}

/**
 * Approve a content idea
 */
export async function approveContentIdea(
  ideaId: string
): Promise<ContentIdeaResponse> {
  try {
    const response = await axiosInstance.put(
      `/api/content-calendar/ideas/${ideaId}/approve/`,
      {}
    );

    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const axiosError = error as { response?: { data?: { error?: string } } };
      throw new Error(
        axiosError?.response?.data?.error || "Failed to approve content idea"
      );
    }
    throw error;
  }
}

/**
 * Unschedule a content idea
 */
export async function unscheduleContentIdea(
  ideaId: string
): Promise<ContentIdeaResponse> {
  try {
    const response = await axiosInstance.put(
      `/api/content-calendar/ideas/${ideaId}/unschedule/`,
      {}
    );

    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const axiosError = error as { response?: { data?: { error?: string } } };
      throw new Error(
        axiosError?.response?.data?.error || "Failed to unschedule content idea"
      );
    }
    throw error;
  }
}

/**
 * Update a content idea
 */
export async function updateContentIdea(
  ideaId: string,
  updates: UpdateContentIdeaRequest
): Promise<ContentIdeaResponse> {
  try {
    const response = await axiosInstance.put(
      `/api/content-calendar/ideas/${ideaId}/`,
      updates
    );

    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const axiosError = error as { response?: { data?: { error?: string } } };
      throw new Error(
        axiosError?.response?.data?.error || "Failed to update content idea"
      );
    }
    throw error;
  }
}

/**
 * Generate a post for a content idea
 */
export async function generatePostForContentIdea(
  ideaId: string,
  businessProfile?: Partial<BusinessProfile> & Record<string, unknown>,
  selectedTemplate?: string,
  postFormat?: "single" | "carousel"
): Promise<
  ContentIdeaResponse & {
    data?: {
      content_idea?: ContentIdea;
      generated_post?: SocialMediaPost;
    };
  }
> {
  try {
    const requestBody: Record<string, unknown> = {};

    if (businessProfile) {
      requestBody.business_profile = businessProfile;
    }

    if (selectedTemplate) {
      requestBody.selected_template = selectedTemplate;
    }

    if (postFormat) {
      requestBody.post_format = postFormat;
    }

    const response = await axiosInstance.post(
      `/api/content-calendar/ideas/${ideaId}/generate-post/`,
      requestBody
    );

    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const axiosError = error as { response?: { data?: { error?: string } } };
      throw new Error(
        axiosError?.response?.data?.error ||
          "Failed to generate post for content idea"
      );
    }
    throw error;
  }
}

/**
 * Delete a content calendar
 */
export async function deleteContentCalendar(
  calendarId: string
): Promise<{ success: boolean; message?: string; error?: string }> {
  try {
    const response = await axiosInstance.delete(
      `/api/content-calendar/${calendarId}/delete/`
    );

    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const axiosError = error as { response?: { data?: { error?: string } } };
      throw new Error(
        axiosError?.response?.data?.error || "Failed to delete content calendar"
      );
    }
    throw error;
  }
}
