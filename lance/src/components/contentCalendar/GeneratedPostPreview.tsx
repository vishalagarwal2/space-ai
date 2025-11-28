import type { SocialMediaPost } from "@/lib/api/socialMediaPosts";
import PostRenderer from "../PostRenderer";
import PostDebugPanel from "./PostDebugPanel";
import { toast } from "sonner";
import { useState } from "react";
import Image from "next/image";
import {
  DEFAULT_TEMPLATE,
  getTemplatesForBusiness,
  type TemplateId,
  TemplateType,
} from "@/config/templates";
import { useBusinessProfile } from "@/contexts/BusinessProfileContext";
import type { BusinessProfile } from "@/constants/mockBusinessProfiles";
import { DEFAULT_BUSINESS_PROFILE } from "@/constants/mockBusinessProfiles";
import type { UnifiedBusinessProfile } from "@/hooks/useBusinessProfile";
import "./GeneratedPostPreview.css";

interface GeneratedPostPreviewProps {
  post: SocialMediaPost;
  onSaveDraft: (postId: string) => void;
  onPublish: (postId: string) => void;
}

// Helper function to convert UnifiedBusinessProfile to BusinessProfile
function convertToBusinessProfile(
  profile: UnifiedBusinessProfile
): BusinessProfile {
  return {
    ...profile,
    designComponents:
      profile.designComponents || DEFAULT_BUSINESS_PROFILE.designComponents,
  };
}

export default function GeneratedPostPreview({
  post,
  onSaveDraft,
  onPublish,
}: GeneratedPostPreviewProps) {
  const { selectedBusinessProfile } = useBusinessProfile();
  const [selectedTemplate, setSelectedTemplate] =
    useState<TemplateId>(DEFAULT_TEMPLATE);

  const layout =
    typeof post.layout_json === "string"
      ? JSON.parse(post.layout_json)
      : post.layout_json;
  const debugInfo = layout?._debug;

  return (
    <div className="preview-post-card">
      <div className="template-selector-container">
        <label htmlFor="template-select" className="template-selector-label">
          Template:
        </label>
        <select
          id="template-select"
          value={selectedTemplate}
          onChange={e => setSelectedTemplate(e.target.value as TemplateId)}
          className="template-selector-dropdown"
        >
          {getTemplatesForBusiness(selectedBusinessProfile?.id).map(
            template => (
              <option key={template.id} value={template.id}>
                {template.name}
              </option>
            )
          )}
        </select>
      </div>

      {post.layout_json && selectedBusinessProfile ? (
        <div className="preview-image-container">
          <PostRenderer
            key={selectedTemplate}
            layout={
              typeof post.layout_json === "string"
                ? JSON.parse(post.layout_json)
                : post.layout_json
            }
            onComplete={() => {}}
            onError={error => {
              console.error("Error rendering post:", error);
              toast.error("Failed to render post image");
            }}
            businessProfile={convertToBusinessProfile(selectedBusinessProfile)}
            selectedTemplate={selectedTemplate as TemplateType}
          />
        </div>
      ) : post.generated_image_url ? (
        <div className="preview-image-container">
          <Image
            src={post.generated_image_url}
            alt="Generated post"
            className="preview-image"
            width={400}
            height={400}
          />
        </div>
      ) : (
        <div className="preview-placeholder">
          <div className="loading-spinner"></div>
          <p className="placeholder-text">Generating image...</p>
        </div>
      )}

      <div className="preview-caption-section">
        <div className="preview-caption">
          <p className="caption-text">{post.caption}</p>
          <p className="hashtags-text">{post.hashtags}</p>
        </div>
      </div>

      <PostDebugPanel debugInfo={debugInfo} layout={layout} />

      <div className="preview-post-actions">
        <button
          className="save-draft-button"
          onClick={() => onSaveDraft(post.id)}
        >
          Save draft
        </button>
        <button
          className="post-instagram-button"
          onClick={() => onPublish(post.id)}
          disabled={!post.layout_json && !post.generated_image_url}
        >
          Post to Instagram
        </button>
      </div>
    </div>
  );
}
