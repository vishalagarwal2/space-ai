"use client";

import { useState, useEffect, useCallback } from "react";
import PostRenderer from "./PostRenderer";
import type { SocialMediaPost } from "@/lib/api/socialMediaPosts";
import type { BusinessProfile } from "@/constants/mockBusinessProfiles";
import type { TemplateId, TemplateType } from "@/config/templates";
import type { LayoutJSON } from "@/types/Layout";
import "./CarouselPreview.css";

interface CarouselPreviewProps {
  post: SocialMediaPost;
  businessProfile: BusinessProfile;
  template: TemplateId;
  onRendererReady?: (
    controls: {
      forceRedraw: () => void;
      isRendering: boolean;
    } | null
  ) => void;
}

export default function CarouselPreview({
  post,
  businessProfile,
  template,
  onRendererReady,
}: CarouselPreviewProps) {
  const [currentSlide, setCurrentSlide] = useState(0);

  const slides = post.carousel_layouts;
  const totalSlides = slides?.length || 0;

  const goToPrevSlide = useCallback(() => {
    setCurrentSlide(prev => (prev === 0 ? totalSlides - 1 : prev - 1));
  }, [totalSlides]);

  const goToNextSlide = useCallback(() => {
    setCurrentSlide(prev => (prev === totalSlides - 1 ? 0 : prev + 1));
  }, [totalSlides]);

  const goToSlide = (index: number) => {
    setCurrentSlide(index);
  };

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        goToPrevSlide();
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        goToNextSlide();
      }
    };

    // Add event listener when component mounts
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [goToPrevSlide, goToNextSlide]);

  if (post.post_type !== "carousel") {
    return null;
  }

  return (
    <div className="carousel-preview" tabIndex={0}>
      <div className="carousel-container">
        <div className="carousel-slide-wrapper">
          <PostRenderer
            key={`carousel-slide-${currentSlide}-${JSON.stringify(slides?.[currentSlide]?.textBlocks?.map((tb: { text: string }) => tb.text))}`}
            layout={
              (slides?.[currentSlide] as LayoutJSON) || {
                textBlocks: [],
                images: [],
                background: { type: "solid", colors: ["#ffffff"] },
                metadata: {
                  brand: { 
                    font_family: "Arial",
                    primary_color: "#000000",
                    secondary_color: "#ffffff",
                    company_name: "",
                  },
                  template: "minimal-clean",
                  dimensions: {
                    width: 1080,
                    height: 1080,
                  },
                },
              } as LayoutJSON
            }
            onComplete={() => {}}
            onError={error => {
              console.error("Error rendering carousel slide:", error);
            }}
            businessProfile={businessProfile}
            selectedTemplate={template as TemplateType}
            onRendererReady={onRendererReady}
          />
          {totalSlides > 1 && (
            <>
              <button
                className="carousel-nav carousel-nav-prev"
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
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </button>
              <button
                className="carousel-nav carousel-nav-next"
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
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </button>
            </>
          )}
        </div>
        {totalSlides > 1 && (
          <div className="carousel-indicators">
            {slides?.map((_, index) => (
              <button
                key={index}
                className={`carousel-indicator ${index === currentSlide ? "active" : ""}`}
                onClick={() => goToSlide(index)}
                aria-label={`Go to slide ${index + 1}`}
              />
            ))}
          </div>
        )}
        {totalSlides > 1 && (
          <div className="carousel-counter">
            {currentSlide + 1} / {totalSlides}
          </div>
        )}
      </div>
    </div>
  );
}
