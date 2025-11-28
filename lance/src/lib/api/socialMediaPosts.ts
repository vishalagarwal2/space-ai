import axiosInstance from "../axios";

export interface SocialMediaPost {
  id: string;
  post_type: "single" | "carousel";
  image_prompt: string;
  layout_json?: string;
  carousel_layouts?: Array<Record<string, any>>; // Array of layout JSONs for carousel slides
  generated_image_url?: string;
  caption: string;
  hashtags: string;
  status:
    | "draft"
    | "generating"
    | "ready"
    | "refining"
    | "publishing"
    | "published"
    | "failed";
  user_input: string;
  instagram_post_id?: string;
  connected_account_id?: string;
  business_profile: {
    company_name: string;
    industry: string;
    brand_voice: string;
    primary_color: string;
    secondary_color: string;
    font_family: string;
    logo_url?: string;
  };
  created_at: string;
  updated_at: string;
}

export interface GeneratePostRequest {
  user_input: string;
  conversation_id?: string;
  business_profile?: {
    company_name: string;
    industry: string;
    brand_voice?: string;
    target_audience?: string;
    primary_color?: string;
    secondary_color?: string;
    font_family?: string;
    logo_url?: string;
  };
}

export interface RefinePostRequest {
  post_id: string;
  refinements: {
    caption?: string;
    hashtags?: string;
    regenerate_image?: boolean;
  };
}

export interface PublishPostRequest {
  post_id: string;
  connected_account_id: string;
  publish_immediately?: boolean;
}

export const generateSocialMediaPost = async (payload: GeneratePostRequest) => {
  return axiosInstance.post("/api/social-media/generate-post/", payload);
};

export const refineSocialMediaPost = async (payload: RefinePostRequest) => {
  return axiosInstance.post("/api/social-media/refine-post/", payload);
};

export const publishSocialMediaPost = async (payload: PublishPostRequest) => {
  return axiosInstance.post("/api/social-media/publish-post/", payload);
};
