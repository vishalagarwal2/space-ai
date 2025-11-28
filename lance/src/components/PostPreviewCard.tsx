"use client";

import { useState } from "react";
import Image from "next/image";
import { SocialMediaPost } from "@/lib/api/socialMediaPosts";
import PostRenderer from "./PostRenderer";
import {
  DEFAULT_TEMPLATE,
  type TemplateId,
  TemplateType,
} from "@/config/templates";
import type { BusinessProfile } from "@/constants/mockBusinessProfiles";
import { HeartIcon, CommentIcon, ShareIcon, BookmarkIcon } from "./icons";
import PostDebugPanel from "./PostDebugPanel";
import "./PostPreviewCard.css";

interface PostPreviewCardProps {
  post: SocialMediaPost;
  onRefine?: (refinements: {
    caption?: string;
    hashtags?: string;
    regenerateImage?: boolean;
  }) => void;
  onPublish?: () => void;
  onSaveDraft?: () => void;
  isRefining?: boolean;
  isPublishing?: boolean;
  businessProfile?: BusinessProfile;
  template?: TemplateId;
  showActions?: boolean;
}

export default function PostPreviewCard({
  post,
  onRefine,
  onPublish,
  onSaveDraft,
  isRefining = false,
  isPublishing = false,
  businessProfile,
  template = DEFAULT_TEMPLATE,
  showActions = true,
}: PostPreviewCardProps) {
  const [isEditingCaption, setIsEditingCaption] = useState(false);
  const combinedCaption = `${post.caption}\n\n${post.hashtags}`;
  const [editedCombinedCaption, setEditedCombinedCaption] =
    useState(combinedCaption);

  const handleCaptionSave = () => {
    if (onRefine) {
      const lines = editedCombinedCaption.split("\n\n");
      const caption = lines[0] || "";
      const hashtags = lines.slice(1).join("\n\n") || "";

      if (caption !== post.caption || hashtags !== post.hashtags) {
        onRefine({ caption, hashtags });
      }
    }
    setIsEditingCaption(false);
  };

  const displayCaption = post.caption;
  const displayHashtags = post.hashtags;

  const layout = post.layout_json
    ? typeof post.layout_json === "string"
      ? JSON.parse(post.layout_json)
      : post.layout_json
    : null;

  const [rendererControls, setRendererControls] = useState<{
    forceRedraw: () => void;
    isRendering: boolean;
  } | null>(null);

  const isDev =
    process.env.NODE_ENV === "development" ||
    (typeof window !== "undefined" && window.location.hostname === "localhost");

  return (
    <>
      {isDev && rendererControls && (
        <div
          style={{
            marginBottom: "12px",
            display: "flex",
            justifyContent: "center",
          }}
        >
          <button
            onClick={rendererControls.forceRedraw}
            disabled={rendererControls.isRendering}
            style={{
              padding: "6px 12px",
              fontSize: "12px",
              backgroundColor: "#6366f1",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: rendererControls.isRendering ? "not-allowed" : "pointer",
              opacity: rendererControls.isRendering ? 0.5 : 1,
              fontWeight: 500,
            }}
            title="Force redraw canvas (dev only)"
          >
            {rendererControls.isRendering ? "Rendering..." : "🔄 Redraw Canvas"}
          </button>
        </div>
      )}
      <div className="post-preview-card">
        <div className="instagram-post-preview">
          <div className="instagram-image-section">
            {layout ? (
              <div className="post-renderer-wrapper">
                <PostRenderer
                  layout={layout}
                  onComplete={() => {}}
                  onError={error => {
                    console.error("Error rendering post:", error);
                  }}
                  businessProfile={businessProfile!}
                  selectedTemplate={template as TemplateType}
                  onRendererReady={setRendererControls}
                />
              </div>
            ) : post.generated_image_url ? (
              <Image
                src={post.generated_image_url}
                alt="Generated post image"
                className="instagram-post-image"
                width={400}
                height={400}
              />
            ) : (
              <div className="image-placeholder">
                <div className="loading-spinner"></div>
                <p>Generating image...</p>
              </div>
            )}
          </div>
          <div className="instagram-actions-section">
            <div className="instagram-actions-icons">
              <div className="instagram-actions-left">
                <HeartIcon
                  size={24}
                  color="currentColor"
                  className="instagram-action-icon"
                />
                <CommentIcon
                  size={24}
                  color="currentColor"
                  className="instagram-action-icon"
                />
                <ShareIcon
                  size={24}
                  color="currentColor"
                  className="instagram-action-icon"
                />
              </div>
              <BookmarkIcon
                size={24}
                color="currentColor"
                className="instagram-action-icon"
              />
            </div>
          </div>
          <div className="instagram-caption-section">
            {isEditingCaption ? (
              <div className="edit-section">
                <textarea
                  value={editedCombinedCaption}
                  onChange={e => setEditedCombinedCaption(e.target.value)}
                  className="combined-caption-textarea"
                  rows={6}
                  placeholder="Enter your caption and hashtags..."
                />
                <div className="edit-actions">
                  <button
                    className="save-button"
                    onClick={handleCaptionSave}
                    disabled={isRefining || isPublishing}
                  >
                    Save
                  </button>
                  <button
                    className="cancel-button"
                    onClick={() => {
                      setEditedCombinedCaption(combinedCaption);
                      setIsEditingCaption(false);
                    }}
                    disabled={isRefining || isPublishing}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <div className="caption-display">
                <p className="caption-text">{displayCaption}</p>
                <p className="hashtags-text">{displayHashtags}</p>
                <button
                  className="edit-caption-button"
                  onClick={() => {
                    setEditedCombinedCaption(combinedCaption);
                    setIsEditingCaption(true);
                  }}
                  disabled={isRefining || isPublishing}
                >
                  Edit
                </button>
              </div>
            )}
          </div>
        </div>

        {layout && <PostDebugPanel layout={layout} />}

        {showActions && (
          <div className="post-actions">
            <button
              className="save-draft-button"
              onClick={onSaveDraft}
              disabled={isRefining || isPublishing}
            >
              Save draft
            </button>
            <button
              className="post-instagram-button"
              onClick={onPublish}
              disabled={
                isPublishing || (!post.generated_image_url && !post.layout_json)
              }
            >
              {isPublishing ? "Publishing..." : "Post to Instagram"}
            </button>
          </div>
        )}
      </div>
    </>
  );
}
