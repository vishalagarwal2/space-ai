import { useState, useMemo, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import type {
  ContentIdea,
  ContentIdeaStatus,
  ContentCalendar as ContentCalendarType,
} from "@/types/ContentCalendar";
import type { SocialMediaPost } from "@/lib/api/socialMediaPosts";
import type { UnifiedBusinessProfile } from "@/hooks/useBusinessProfile";
import { generatePostForContentIdea } from "@/lib/api/contentCalendar";
import { contentCalendarKeys } from "@/hooks/useContentCalendar";
import { useBusinessProfile } from "@/contexts/BusinessProfileContext";
import { toast } from "sonner";
import { extractErrorMessage } from "@/lib/utils";

export function useContentCalendarState(
  calendars: ContentCalendarType[] | undefined
) {
  const [selectedCalendarId, setSelectedCalendarId] = useState<string | null>(
    null
  );
  const [selectedContentIdeaId, setSelectedContentIdeaId] = useState<
    string | null
  >(null);
  const [generatedPost, setGeneratedPost] = useState<SocialMediaPost | null>(
    null
  );
  const [editingField, setEditingField] = useState<
    "title" | "description" | null
  >(null);
  const [editValues, setEditValues] = useState<{
    title: string;
    description: string;
  }>({
    title: "",
    description: "",
  });

  const effectiveCalendarId = useMemo(() => {
    if (!calendars || calendars.length === 0) return null;

    if (
      selectedCalendarId &&
      calendars.find(cal => cal.id === selectedCalendarId)
    ) {
      return selectedCalendarId;
    }

    return calendars[0]?.id || null;
  }, [calendars, selectedCalendarId]);

  const selectedCalendar = useMemo(
    () => calendars?.find(cal => cal.id === effectiveCalendarId) || null,
    [calendars, effectiveCalendarId]
  );

  const selectedContentIdea = useMemo(() => {
    if (!selectedContentIdeaId || !calendars) return null;
    for (const calendar of calendars) {
      const idea = calendar.content_ideas?.find(
        i => i.id === selectedContentIdeaId
      );
      if (idea) return idea;
    }
    return null;
  }, [selectedContentIdeaId, calendars]);

  const derivedGeneratedPost = useMemo(() => {
    if (editingField) return generatedPost;
    return selectedContentIdea?.generated_post_data || null;
  }, [selectedContentIdea?.generated_post_data, editingField, generatedPost]);

  const handleContentIdeaClick = useCallback((idea: ContentIdea) => {
    setEditingField(null);
    setSelectedContentIdeaId(idea.id);
  }, []);

  const handleStartEdit = useCallback(
    (field: "title" | "description") => {
      if (!selectedContentIdea) return;
      setEditingField(field);
      setEditValues({
        title: selectedContentIdea.title,
        description: selectedContentIdea.description,
      });
    },
    [selectedContentIdea]
  );

  const handleCancelEdit = useCallback(() => {
    setEditingField(null);
    setEditValues({ title: "", description: "" });
  }, []);

  const clearSelectedStates = useCallback(() => {
    setSelectedCalendarId(null);
    setSelectedContentIdeaId(null);
    setGeneratedPost(null);
    setEditingField(null);
    setEditValues({ title: "", description: "" });
  }, []);

  const setSelectedCalendar = useCallback(
    (calendar: ContentCalendarType | null) => {
      setSelectedCalendarId(calendar?.id || null);
      if (calendar?.id !== effectiveCalendarId) {
        setSelectedContentIdeaId(null);
      }
    },
    [effectiveCalendarId]
  );

  const setSelectedContentIdea = useCallback((idea: ContentIdea | null) => {
    setSelectedContentIdeaId(idea?.id || null);
  }, []);

  return {
    selectedCalendar,
    setSelectedCalendar,
    selectedContentIdea,
    setSelectedContentIdea,
    generatedPost: derivedGeneratedPost,
    setGeneratedPost,
    editingField,
    setEditingField,
    editValues,
    setEditValues,
    handleContentIdeaClick,
    handleStartEdit,
    handleCancelEdit,
    clearSelectedStates,
  };
}

const transformBusinessProfile = (
  businessProfile: UnifiedBusinessProfile | null
): Record<string, unknown> => {
  if (!businessProfile) {
    return {};
  }
  return {
    name: businessProfile.name,
    company_name: businessProfile.companyName,
    companyName: businessProfile.companyName,
    industry: businessProfile.brandGuidelines?.industry,
    tagline: businessProfile.brandGuidelines?.tagline,
    font_family: businessProfile.brandGuidelines?.fontFamily,
    fontFamily: businessProfile.brandGuidelines?.fontFamily,
    brandGuidelines: {
      fontFamily: businessProfile.brandGuidelines?.fontFamily,
      industry: businessProfile.brandGuidelines?.industry,
      tagline: businessProfile.brandGuidelines?.tagline,
    },
    colorPalette: businessProfile.colorPalette,
    logoUrl: businessProfile.logoUrl,
    postLogoUrl: businessProfile.postLogoUrl,
    website_url: businessProfile.website_url,
    instagram_handle: businessProfile.instagram_handle,
    brand_mission: businessProfile.brand_mission,
    brand_values: businessProfile.brand_values,
    business_basic_details: businessProfile.business_basic_details,
    business_services: businessProfile.business_services,
    business_context: businessProfile.business_context,
    business_additional_details: businessProfile.business_additional_details,
  };
};

export function usePostGeneration(
  selectedContentIdea: ContentIdea | null,
  setSelectedContentIdea: (idea: ContentIdea) => void,
  setGeneratedPost: (post: SocialMediaPost | null) => void
) {
  const queryClient = useQueryClient();
  const { selectedBusinessProfile } = useBusinessProfile();
  const [isGeneratingPostForIdea, setIsGeneratingPostForIdea] = useState<
    string | null
  >(null);

  const handleGeneratePost = useCallback(
    async (
      idea: ContentIdea,
      onGeneratePost?: (idea: ContentIdea) => void,
      selectedTemplate?: string,
      postFormat?: "single" | "carousel"
    ) => {
      if (onGeneratePost) {
        onGeneratePost(idea);
        return;
      }

      setIsGeneratingPostForIdea(idea.id);
      setGeneratedPost(null);

      if (!selectedBusinessProfile) {
        toast.error("Business profile is required to generate posts");
        setIsGeneratingPostForIdea(null);
        return;
      }

      try {
        const transformedBusinessProfile = transformBusinessProfile(
          selectedBusinessProfile
        );

        const response = await generatePostForContentIdea(
          idea.id,
          transformedBusinessProfile,
          selectedTemplate,
          postFormat
        );

        if (response.success && response.data) {
          const generatedPost =
            response.data.generated_post ||
            response.data.content_idea?.generated_post_data;

          if (generatedPost) {
            setGeneratedPost(generatedPost);

            if (
              response.data.content_idea &&
              selectedContentIdea?.id === idea.id
            ) {
              const postFormat =
                generatedPost.post_type === "carousel" ? "carousel" : "single";

              const updatedIdea: ContentIdea = {
                ...idea,
                ...response.data.content_idea,
                post_format:
                  response.data.content_idea.post_format || postFormat, // Use backend value, fallback to post type
                generated_post_data: generatedPost,
                status: "pending_approval" as ContentIdeaStatus,
              };

              if (updatedIdea.post_format !== postFormat) {
                console.warn(
                  `Post format mismatch: ContentIdea has '${updatedIdea.post_format}' but generated post is '${postFormat}'. Using ContentIdea value.`
                );
              }

              setSelectedContentIdea(updatedIdea);
            }

            if (selectedBusinessProfile) {
              queryClient.invalidateQueries({
                queryKey: contentCalendarKeys.calendars(
                  selectedBusinessProfile.id
                ),
                refetchType: "active",
              });

              queryClient.invalidateQueries({
                queryKey: contentCalendarKeys.posts(),
              });

              setTimeout(() => {
                queryClient.refetchQueries({
                  queryKey: contentCalendarKeys.calendars(
                    selectedBusinessProfile.id
                  ),
                  type: "active",
                });
              }, 500);
            }

            toast.success("Post generated successfully!");
          } else {
            throw new Error("No post data in response");
          }
        } else {
          throw new Error(response.error || "Failed to generate post");
        }
      } catch (error: unknown) {
        const errorMessage = extractErrorMessage(error);
        toast.error(errorMessage);
      } finally {
        setIsGeneratingPostForIdea(null);
      }
    },
    [
      selectedBusinessProfile,
      setGeneratedPost,
      setSelectedContentIdea,
      queryClient,
      selectedContentIdea,
    ]
  );

  return {
    isGeneratingPostForIdea,
    handleGeneratePost,
  };
}
