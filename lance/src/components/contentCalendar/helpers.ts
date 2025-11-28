import type { BusinessProfile } from "@/constants/mockBusinessProfiles";
import type { UnifiedBusinessProfile } from "@/hooks/useBusinessProfile";
import type { GenerateContentCalendarRequest } from "@/types/ContentCalendar";

export function transformBusinessProfileToRequest(
  profile: BusinessProfile | UnifiedBusinessProfile | any
): GenerateContentCalendarRequest["business_profile"] {
  if (profile && "company_name" in profile && !("companyName" in profile)) {
    return {
      name: profile.company_name,
      company_name: profile.company_name,
      companyName: profile.company_name,
      industry: profile.industry || "",
      tagline: "",
      website_url: profile.website_url || "",
      instagram_handle: "",
      brand_mission: "",
      brand_values: profile.brand_voice || "",
      business_basic_details: profile.business_description || "",
      business_services: "",
      business_context: "",
      business_additional_details: `Target Audience: ${profile.target_audience || ""}`,
    };
  }

  if (profile && "companyName" in profile && "brandGuidelines" in profile) {
    return {
      name: profile.name,
      company_name: profile.companyName,
      companyName: profile.companyName,
      industry: profile.brandGuidelines.industry,
      tagline: profile.brandGuidelines.tagline,
      website_url: profile.website_url,
      instagram_handle: profile.instagram_handle,
      brand_mission: profile.brand_mission,
      brand_values: profile.brand_values,
      business_basic_details: profile.business_basic_details,
      business_services: profile.business_services,
      business_context: profile.business_context,
      business_additional_details: profile.business_additional_details,
    };
  }

  return {
    name: profile?.name || profile?.company_name || "Unknown Company",
    company_name:
      profile?.company_name || profile?.companyName || "Unknown Company",
    companyName:
      profile?.companyName || profile?.company_name || "Unknown Company",
    industry: profile?.industry || profile?.brandGuidelines?.industry || "",
    tagline: profile?.tagline || profile?.brandGuidelines?.tagline || "",
    website_url: profile?.website_url || "",
    instagram_handle: profile?.instagram_handle || "",
    brand_mission: profile?.brand_mission || "",
    brand_values: profile?.brand_values || profile?.brand_voice || "",
    business_basic_details:
      profile?.business_basic_details || profile?.business_description || "",
    business_services: profile?.business_services || "",
    business_context: profile?.business_context || "",
    business_additional_details: profile?.business_additional_details || "",
  };
}
