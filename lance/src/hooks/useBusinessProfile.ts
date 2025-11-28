import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import axiosInstance from "@/lib/axios";
import {
  BusinessProfile as MockBusinessProfile,
  MOCK_BUSINESS_PROFILES,
  DEFAULT_BUSINESS_PROFILE,
} from "@/constants/mockBusinessProfiles";
import { useState, useCallback, useEffect } from "react";

// API Business Profile interface (from backend)
export interface APIBusinessProfile {
  id: string;
  business_id: string;
  business_name: string;
  website_url: string;
  instagram_handle: string;
  logo_url?: string;
  primary_color: string;
  secondary_color: string;
  accent_color: string;
  font_family: string;
  brand_mission: string;
  brand_values: string;
  business_basic_details: string;
  business_services: string;
  business_additional_details: string;
  created_at: string;
  updated_at: string;
}

// Unified Business Profile interface that works for both admin and business users
export interface UnifiedBusinessProfile {
  id: string;
  name: string;
  companyName: string;
  logoUrl?: string;
  postLogoUrl?: string;
  colorPalette: {
    primary: string;
    secondary: string;
    accent?: string;
    background?: string;
  };
  brandGuidelines: {
    fontFamily: string;
    tagline?: string;
    industry: string;
  };
  designComponents?: {
    instructions: string;
    componentRules: {
      headerText: {
        description: string;
        styling: Record<string, unknown>;
        usage: string;
      };
      bodyText: {
        description: string;
        styling: Record<string, unknown>;
        usage: string;
      };
      specialBannerText: {
        description: string;
        styling: Record<string, unknown>;
        usage: string;
      };
    };
  }; // From mock profiles
  defaultTemplate?: string;
  website_url?: string;
  instagram_handle?: string;
  brand_mission?: string;
  brand_values?: string;
  business_basic_details?: string;
  business_services?: string;
  business_context?: string;
  business_additional_details?: string;
  // API-specific fields
  business_description?: string;
  target_audience?: string;
  brand_voice?: string;
  social_media_handles?: Record<string, string>;
  created_at?: string;
  updated_at?: string;
}

export interface UserType {
  type: "admin" | "business";
  id: string;
  email: string;
  first_name: string;
  last_name: string;
}

export interface BusinessProfileFormData {
  business_name: string;
  website_url?: string;
  instagram_handle?: string;
  primary_color: string;
  secondary_color: string;
  accent_color?: string;
  font_family: string;
  brand_mission: string;
  brand_values: string;
  business_basic_details: string;
  business_services: string;
  business_additional_details: string;
  logo?: File;
}

export const businessProfileKeys = {
  all: ["businessProfile"] as const,
  profile: () => [...businessProfileKeys.all, "profile"] as const,
  userType: () => [...businessProfileKeys.all, "userType"] as const,
};

const STORAGE_KEY = "selectedBusinessProfile";

// Helper function to convert API profile to unified format
function convertAPIProfileToUnified(
  apiProfile: APIBusinessProfile
): UnifiedBusinessProfile {
  return {
    id: apiProfile.id,
    name: apiProfile.business_name || "Business Profile",
    companyName: apiProfile.business_name || "Business Profile",
    logoUrl: apiProfile.logo_url,
    postLogoUrl: apiProfile.logo_url,
    colorPalette: {
      primary: apiProfile.primary_color,
      secondary: apiProfile.secondary_color,
      accent: apiProfile.accent_color || "#F59E0B",
      background: "#F8FAFC", // Default background
    },
    brandGuidelines: {
      fontFamily: apiProfile.font_family || "Inter",
      industry: "", // Not available in current API profile
    },
    website_url: apiProfile.website_url,
    instagram_handle: apiProfile.instagram_handle,
    brand_mission: apiProfile.brand_mission,
    brand_values: apiProfile.brand_values,
    business_basic_details: apiProfile.business_basic_details,
    business_services: apiProfile.business_services,
    business_additional_details: apiProfile.business_additional_details,
    created_at: apiProfile.created_at,
    updated_at: apiProfile.updated_at,
  };
}

// Helper function to convert mock profile to unified format
function convertMockProfileToUnified(
  mockProfile: MockBusinessProfile
): UnifiedBusinessProfile {
  return {
    id: mockProfile.id,
    name: mockProfile.name,
    companyName: mockProfile.companyName,
    logoUrl: mockProfile.logoUrl,
    postLogoUrl: mockProfile.postLogoUrl,
    colorPalette: mockProfile.colorPalette,
    brandGuidelines: mockProfile.brandGuidelines,
    designComponents: mockProfile.designComponents,
    defaultTemplate: mockProfile.defaultTemplate,
    website_url: mockProfile.website_url,
    instagram_handle: mockProfile.instagram_handle,
    brand_mission: mockProfile.brand_mission,
    brand_values: mockProfile.brand_values,
    business_basic_details: mockProfile.business_basic_details,
    business_services: mockProfile.business_services,
    business_context: mockProfile.business_context,
    business_additional_details: mockProfile.business_additional_details,
  };
}

// Hook to determine user type
export function useUserType() {
  return useQuery({
    queryKey: businessProfileKeys.userType(),
    queryFn: async (): Promise<UserType | null> => {
      // First check for business auth
      try {
        const businessResponse = await axiosInstance.get(
          "/api/business/auth/status/"
        );

        if (
          businessResponse.data.authenticated &&
          businessResponse.data.user_type === "business"
        ) {
          const result = {
            type: "business",
            ...businessResponse.data.business,
          };
          return result;
        }
      } catch {}

      // Check for admin auth
      try {
        const adminResponse = await axiosInstance.get("/api/auth/status/");

        if (adminResponse.data.authenticated) {
          const result = {
            type: "admin",
            ...adminResponse.data.user,
          };
          return result;
        }
      } catch {}

      return null;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  });
}

// Main unified business profile hook
export function useBusinessProfile() {
  const { data: userType, isLoading: userTypeLoading } = useUserType();
  const [selectedMockProfile, setSelectedMockProfile] =
    useState<MockBusinessProfile>(() => {
      if (typeof window !== "undefined") {
        const savedProfileId = localStorage.getItem(STORAGE_KEY);
        if (savedProfileId) {
          const savedProfile = MOCK_BUSINESS_PROFILES.find(
            p => p.id === savedProfileId
          );
          if (savedProfile) {
            return savedProfile;
          }
        }
      }
      return DEFAULT_BUSINESS_PROFILE;
    });

  // For business users, fetch their actual profile from API
  const businessProfileQuery = useQuery({
    queryKey: [...businessProfileKeys.profile(), "business"],
    queryFn: async (): Promise<APIBusinessProfile | null> => {
      const response = await axiosInstance.get("/api/business/profile/");

      if (response.data.status === "success" && response.data.profile) {
        return response.data.profile;
      }

      return null;
    },
    enabled: userType?.type === "business",
    staleTime: 0, // Always fetch fresh data
    retry: (failureCount, _error: unknown) => {
      const apiError = _error as { response?: { status?: number } };
      if (apiError?.response?.status === 404) {
        return false;
      }
      return failureCount < 3;
    },
  });

  // For admin users, fetch their company profile from API
  const adminProfileQuery = useQuery({
    queryKey: [...businessProfileKeys.profile(), "admin"],
    queryFn: async (): Promise<APIBusinessProfile | null> => {
      const response = await axiosInstance.get("/api/company-profile/");
      if (response.data.status === "success" && response.data.data) {
        return response.data.data;
      }
      return null;
    },
    enabled: userType?.type === "admin",
    staleTime: 0,
    retry: (failureCount, _error: unknown) => {
      const apiError = _error as { response?: { status?: number } };
      if (apiError?.response?.status === 404) {
        return false;
      }
      return failureCount < 3;
    },
  });

  // Function to handle mock profile selection (admin only)
  const setSelectedBusinessProfile = useCallback(
    (profile: MockBusinessProfile) => {
      if (userType?.type === "admin") {
        localStorage.setItem(STORAGE_KEY, profile.id);
        setSelectedMockProfile(profile);
      }
    },
    [userType?.type]
  );

  // Determine the current business profile based on user type
  const currentProfile: UnifiedBusinessProfile | null = (() => {
    if (!userType) {
      return null;
    }

    if (userType.type === "business") {
      // For business users, use their API profile
      if (businessProfileQuery.data) {
        const converted = convertAPIProfileToUnified(businessProfileQuery.data);
        return converted;
      }
      return null;
    } else {
      // For admin users, prefer API profile if available, otherwise use selected mock profile
      if (adminProfileQuery.data) {
        const converted = convertAPIProfileToUnified(adminProfileQuery.data);
        return converted;
      }
      const mockConverted = convertMockProfileToUnified(selectedMockProfile);
      return mockConverted;
    }
  })();

  const isLoading =
    userTypeLoading ||
    (userType?.type === "business" && businessProfileQuery.isLoading) ||
    (userType?.type === "admin" && adminProfileQuery.isLoading);

  return {
    // Current active profile
    selectedBusinessProfile: currentProfile,

    // For admin users - mock profile management
    setSelectedBusinessProfile,
    availableProfiles: MOCK_BUSINESS_PROFILES,

    // User type information
    userType,

    // Loading state
    isLoading,

    // Raw API data for advanced use cases
    apiProfile:
      userType?.type === "business"
        ? businessProfileQuery.data
        : adminProfileQuery.data,

    // Refetch functions
    refetch: () => {
      if (userType?.type === "business") {
        businessProfileQuery.refetch();
      } else {
        adminProfileQuery.refetch();
      }
    },
  };
}

// Hook for updating business profiles
export function useUpdateBusinessProfile() {
  const queryClient = useQueryClient();
  const { userType } = useBusinessProfile();

  return useMutation({
    mutationFn: async (formData: BusinessProfileFormData) => {
      const formDataToSend = new FormData();

      formDataToSend.append("business_name", formData.business_name);
      formDataToSend.append("primary_color", formData.primary_color);
      formDataToSend.append("secondary_color", formData.secondary_color);
      formDataToSend.append("font_family", formData.font_family);
      formDataToSend.append("brand_mission", formData.brand_mission);
      formDataToSend.append("brand_values", formData.brand_values);
      formDataToSend.append(
        "business_basic_details",
        formData.business_basic_details
      );
      formDataToSend.append("business_services", formData.business_services);
      formDataToSend.append(
        "business_additional_details",
        formData.business_additional_details
      );

      if (formData.website_url) {
        formDataToSend.append("website_url", formData.website_url);
      }

      if (formData.instagram_handle) {
        formDataToSend.append("instagram_handle", formData.instagram_handle);
      }

      if (formData.accent_color) {
        formDataToSend.append("accent_color", formData.accent_color);
      }

      if (formData.logo) {
        formDataToSend.append("logo", formData.logo);
      }

      // Choose endpoint based on user type
      const endpoint =
        userType?.type === "business"
          ? "/api/business/profile/update/"
          : "/api/company-profile/";

      const response = await axiosInstance.post(endpoint, formDataToSend, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      return response.data;
    },
    onSuccess: data => {
      if (data.status === "success") {
        toast.success("Business profile saved successfully!");
        queryClient.invalidateQueries({
          queryKey: businessProfileKeys.profile(),
        });
        queryClient.invalidateQueries({
          queryKey: businessProfileKeys.userType(),
        });
      } else {
        throw new Error(data.message || "Failed to save profile");
      }
    },
    onError: (error: unknown) => {
      const apiError = error as {
        response?: { data?: { message?: string } };
        message?: string;
      };
      const message =
        apiError?.response?.data?.message ||
        apiError?.message ||
        "Failed to save business profile";
      toast.error(message);
    },
  });
}

// Profile change callback hook for backward compatibility
export function useProfileChangeCallback(
  callback: (profile: UnifiedBusinessProfile) => void
) {
  const { selectedBusinessProfile } = useBusinessProfile();

  useEffect(() => {
    if (selectedBusinessProfile) {
      callback(selectedBusinessProfile);
    }
  }, [selectedBusinessProfile, callback]);

  return useCallback(() => {
    // Cleanup function (no-op for now)
  }, []);
}
