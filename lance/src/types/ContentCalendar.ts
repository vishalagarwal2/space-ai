/**
 * Content Calendar Types
 */

export enum ContentType {
  PROMO = "promo",
  EDUCATIONAL = "educational",
  BEHIND_SCENES = "behind_scenes",
  TESTIMONIAL = "testimonial",
  HOLIDAY = "holiday",
}

export type ContentTypeString =
  | "promo"
  | "educational"
  | "behind_scenes"
  | "testimonial"
  | "holiday";

export type ContentIdeaStatus = "pending_approval" | "scheduled" | "published";

import type { SocialMediaPost } from "@/lib/api/socialMediaPosts";

export type PostFormat = "single" | "carousel";

export interface ContentIdea {
  id: string;
  content_calendar: string;
  title: string;
  description: string;
  content_type: ContentTypeString;
  post_format: PostFormat;
  generation_prompt: string;
  scheduled_date: string; // ISO date string
  scheduled_time?: string; // ISO time string
  status: ContentIdeaStatus;
  generated_post_id?: string;
  generated_post_data?: SocialMediaPost; // Full generated post data
  published_post_id?: string;
  selected_template?: string; // Template ID for post generation
  user_notes?: string;
  media_urls: string[];
  created_at: string;
  updated_at: string;
  approved_at?: string;
  published_at?: string;
}

export interface ContentCalendar {
  id: string;
  user: string;
  business_profile_id: string;
  title: string;
  month: number;
  year: number;
  business_profile_data: Record<string, unknown>;
  generation_prompt: string;
  content_ideas?: ContentIdea[];
  created_at: string;
  updated_at: string;
}

export interface GenerateContentCalendarRequest {
  business_profile: {
    name?: string;
    company_name?: string;
    companyName?: string;
    industry?: string;
    tagline?: string;
    website_url?: string;
    instagram_handle?: string;
    brand_mission?: string;
    brand_values?: string;
    business_basic_details?: string;
    business_services?: string;
    business_context?: string;
    business_additional_details?: string;
  };
  business_profile_id?: string;
}

export interface GenerateContentCalendarResponse {
  success: boolean;
  data?: {
    calendar: ContentCalendar;
    content_ideas: ContentIdea[];
  };
  message?: string;
  error?: string;
}

export interface GetContentCalendarsResponse {
  success: boolean;
  data?: {
    calendars: ContentCalendar[];
  };
  error?: string;
}

export interface UpdateContentIdeaRequest {
  title?: string;
  description?: string;
  scheduled_date?: string;
  scheduled_time?: string;
  user_notes?: string;
  status?: ContentIdeaStatus;
  selected_template?: string;
  post_format?: PostFormat;
}

export interface ContentIdeaResponse {
  success: boolean;
  data?: ContentIdea;
  message?: string;
  error?: string;
}

// Helper function to format date for display
export function formatContentDate(dateString: string): string {
  const date = new Date(dateString);
  const dayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const monthNames = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
  ];

  return `${dayNames[date.getDay()]}, ${monthNames[date.getMonth()]} ${date.getDate()}${getDaySuffix(date.getDate())}`;
}

function getDaySuffix(day: number): string {
  if (day >= 11 && day <= 13) {
    return "th";
  }
  switch (day % 10) {
    case 1:
      return "st";
    case 2:
      return "nd";
    case 3:
      return "rd";
    default:
      return "th";
  }
}

export function getStatusLabelColor(status: ContentIdeaStatus): string {
  switch (status) {
    case "pending_approval":
      return "#FEE074";
    case "scheduled":
      return "#10B981";
    case "published":
      return "#10B981";
    default:
      return "#6B7280"; // Gray fallback
  }
}

export function getStatusLabelBgColor(status: ContentIdeaStatus): string {
  return getStatusLabelColor(status);
}

// Helper function to get status label
export function getStatusLabel(status: ContentIdeaStatus): string {
  switch (status) {
    case "pending_approval":
      return "NEEDS APPROVAL";
    case "scheduled":
      return "SCHEDULED TO POST";
    case "published":
      return "PUBLISHED";
    default:
      return String(status).toUpperCase();
  }
}

function lightenColor(hex: string, amount: number = 0.85): string {
  // Remove # if present
  hex = hex.replace("#", "");

  // Parse RGB values
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);

  // Mix with white (255, 255, 255)
  // amount is the percentage of white to mix (0.85 = 85% white, 15% original color)
  const newR = Math.round(r * (1 - amount) + 255 * amount);
  const newG = Math.round(g * (1 - amount) + 255 * amount);
  const newB = Math.round(b * (1 - amount) + 255 * amount);

  // Convert back to hex
  return `#${newR.toString(16).padStart(2, "0")}${newG.toString(16).padStart(2, "0")}${newB.toString(16).padStart(2, "0")}`;
}

export function getContentTypeBadgeColor(type: ContentTypeString): string {
  switch (type) {
    case "promo":
      return "#8B5CF6"; // Purple
    case "educational":
      return "#3B82F6"; // Blue
    case "behind_scenes":
      return "#F59E0B"; // Amber
    case "testimonial":
      return "#EC4899"; // Pink
    case "holiday":
      return "#EF4444"; // Red
    default:
      return "#6B7280"; // Gray
  }
}

// Helper function to get lightened badge background color
export function getContentTypeBadgeBackgroundColor(
  type: ContentTypeString
): string {
  return lightenColor(getContentTypeBadgeColor(type));
}

export function getContentTypeLabel(type: ContentTypeString): string {
  switch (type) {
    case "promo":
      return "Promotional";
    case "educational":
      return "Educational";
    case "behind_scenes":
      return "Behind the Scenes";
    case "testimonial":
      return "Testimonial";
    case "holiday":
      return "Holiday";
    default:
      return type;
  }
}

// Helper function to get post format label
export function getPostFormatLabel(format: PostFormat): string {
  switch (format) {
    case "carousel":
      return "🎠 Carousel";
    case "single":
      return "📄 Single Post";
    default:
      return format;
  }
}

// Helper function to get post format badge color
export function getPostFormatBadgeColor(format: PostFormat): string {
  switch (format) {
    case "carousel":
      return "#7c3aed"; // Purple
    case "single":
      return "#0277bd"; // Blue
    default:
      return "#6B7280"; // Gray
  }
}

// Helper function to get post format badge background color
export function getPostFormatBadgeBackgroundColor(format: PostFormat): string {
  switch (format) {
    case "carousel":
      return "#f3e8ff"; // Light purple
    case "single":
      return "#e0f2fe"; // Light blue
    default:
      return "#f3f4f6"; // Light gray
  }
}
