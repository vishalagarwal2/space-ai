"use client";

import { useState, useEffect, useCallback } from "react";
import PostPreviewCard from "./PostPreviewCard";
import type { SocialMediaPost } from "@/lib/api/socialMediaPosts";
import type { BusinessProfile } from "@/constants/mockBusinessProfiles";
import type { TemplateId } from "@/config/templates";
import "./SocialMediaPostWrapper.css";

interface SocialMediaPostWrapperProps {
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

export default function SocialMediaPostWrapper({
  post,
  onRefine,
  onPublish,
  onSaveDraft,
  isRefining = false,
  isPublishing = false,
  businessProfile,
  template,
  showActions = true,
}: SocialMediaPostWrapperProps) {
  const [currentSlide, setCurrentSlide] = useState(0);

  const isCarousel =
    post.post_type === "carousel" &&
    post.carousel_layouts &&
    post.carousel_layouts.length > 0;

  const totalSlides = isCarousel ? post.carousel_layouts!.length : 1;

  const goToPrevSlide = useCallback(() => {
    setCurrentSlide(prev => (prev === 0 ? totalSlides - 1 : prev - 1));
  }, [totalSlides]);

  const goToNextSlide = useCallback(() => {
    setCurrentSlide(prev => (prev === totalSlides - 1 ? 0 : prev + 1));
  }, [totalSlides]);

  const goToSlide = (index: number) => {
    setCurrentSlide(index);
  };

  const currentPost = isCarousel
    ? {
        ...post,
        layout_json: JSON.stringify(post.carousel_layouts![currentSlide]),
      }
    : post;

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isCarousel) return;

      if (e.key === "ArrowLeft") {
        e.preventDefault();
        goToPrevSlide();
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        goToNextSlide();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isCarousel, totalSlides, goToPrevSlide, goToNextSlide]);

  return (
    <div className="social-media-post-wrapper" tabIndex={0}>
      <div className="post-container">
        {isCarousel && totalSlides > 1 && (
          <>
            <div
              className="post-nav post-nav-prev"
              onClick={goToPrevSlide}
              aria-label="Previous slide"
            >
              <svg
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M15 18L9 12L15 6"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>

            <div
              className="post-nav post-nav-next"
              onClick={goToNextSlide}
              aria-label="Next slide"
            >
              <svg
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M9 18L15 12L9 6"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
          </>
        )}

        <PostPreviewCard
          post={currentPost}
          onRefine={onRefine}
          onPublish={onPublish}
          onSaveDraft={onSaveDraft}
          isRefining={isRefining}
          isPublishing={isPublishing}
          businessProfile={businessProfile}
          template={template}
          showActions={showActions}
        />

        {isCarousel && totalSlides > 1 && (
          <div className="post-indicators">
            {Array.from({ length: totalSlides }, (_, index) => (
              <button
                key={index}
                className={`post-indicator ${index === currentSlide ? "active" : ""}`}
                onClick={() => goToSlide(index)}
                aria-label={`Go to slide ${index + 1}`}
              />
            ))}
          </div>
        )}
      </div>

      {process.env.NODE_ENV === "development" && (
        <div className="debug-info">
          <details>
            <summary>🐛 Debug Info</summary>
            <div className="debug-content">
              <p>
                <strong>Post Type:</strong> {post.post_type}
              </p>
              <p>
                <strong>Is Carousel:</strong> {isCarousel ? "Yes" : "No"}
              </p>
              <p>
                <strong>Total Slides:</strong> {totalSlides}
              </p>
              <p>
                <strong>Current Slide:</strong> {currentSlide + 1}
              </p>
              <p>
                <strong>Status:</strong> {post.status}
              </p>
              {isCarousel && (
                <p>
                  <strong>Carousel Layouts:</strong>{" "}
                  {post.carousel_layouts?.length || 0} slides
                </p>
              )}
            </div>
          </details>
        </div>
      )}
    </div>
  );
}
