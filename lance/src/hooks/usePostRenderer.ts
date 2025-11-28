import { useRef, useCallback, useEffect, useState } from "react";
import { LayoutJSON } from "../types/Layout";
import { useFontLoader } from "./useFontLoader";
import type { TemplateType } from "../services/templateRenderer";
import type { BusinessProfile } from "../constants/mockBusinessProfiles";
import {
  renderBackground,
  renderText,
  renderImages,
} from "../utils/canvasRenderer";
import { renderTemplateToCanvas } from "../services/templateRenderer";
import { prepareFontString } from "../utils/textUtils";
import { getTemplateConfig, getAreaBounds } from "../config/templateAreas";

// Visual debug flag - set to true to show availableAreaToPlaceElements as red rectangle
const DEBUG_SHOW_AVAILABLE_AREA = false;

// Set global flag for other components to use
if (typeof window !== "undefined") {
  (window as unknown as Record<string, unknown>).DEBUG_SHOW_AVAILABLE_AREA =
    DEBUG_SHOW_AVAILABLE_AREA;
}

const getLayoutKey = (
  layout: LayoutJSON,
  selectedTemplate?: string
): string => {
  return JSON.stringify({
    layout: selectedTemplate,
    textBlocks: layout.textBlocks.map(tb => ({
      id: tb.id,
      text: tb.text,
      componentType: tb.componentType,
      alignment: tb.alignment,
      order: tb.order,
    })),
    images: layout.images.map(img => ({
      id: img.id,
      src: img.src,
      position: img.position,
    })),
    selectedTemplate,
    background: layout.background,
    metadata: layout.metadata,
  });
};

/**
 * Draws the availableAreaToPlaceElements as a red rectangle for visual debugging
 * Now shows the actual bounds used (padding removed from sequential layout engine)
 */
function drawAvailableAreaDebug(
  ctx: CanvasRenderingContext2D,
  selectedTemplate?: TemplateType
): void {
  if (!DEBUG_SHOW_AVAILABLE_AREA || !selectedTemplate) {
    return;
  }

  const canvas = ctx.canvas;
  const canvasWidth = canvas.width;
  const canvasHeight = canvas.height;

  const templateConfig = getTemplateConfig(selectedTemplate);
  if (!templateConfig) {
    console.warn(`[Debug] No template config found for ${selectedTemplate}`);
    return;
  }

  // Template coordinates are defined for 1080x1080 canvas
  const expectedWidth = 1080;
  const expectedHeight = 1080;

  // Calculate scale factors if canvas dimensions differ
  const scaleX = canvasWidth / expectedWidth;
  const scaleY = canvasHeight / expectedHeight;

  const bounds = getAreaBounds(templateConfig.availableAreaToPlaceElements);

  // Scale coordinates if canvas dimensions differ from expected
  const scaledBounds = {
    x: bounds.x * scaleX,
    y: bounds.y * scaleY,
    width: bounds.width * scaleX,
    height: bounds.height * scaleY,
  };

  ctx.save();
  ctx.strokeStyle = "#FF0000"; // Red color
  ctx.lineWidth = 3;
  ctx.setLineDash([5, 5]); // Dashed line for better visibility
  ctx.strokeRect(
    scaledBounds.x,
    scaledBounds.y,
    scaledBounds.width,
    scaledBounds.height
  );
  ctx.restore();
}

interface UsePostRendererProps {
  layout: LayoutJSON;
  onComplete?: (imageData: string) => void;
  onError?: (error: string) => void;
  businessProfile: BusinessProfile;
  selectedTemplate?: TemplateType;
}

export const usePostRenderer = ({
  layout,
  onComplete,
  onError,
  businessProfile,
  selectedTemplate,
}: UsePostRendererProps) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const lastRenderedKeyRef = useRef<string>("");
  const isRenderingRef = useRef(false);
  const [isRendering, setIsRendering] = useState(false);
  const { loadFonts } = useFontLoader();

  const renderPost = useCallback(async () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const currentKey = getLayoutKey(layout, selectedTemplate);
    if (lastRenderedKeyRef.current === currentKey && isRenderingRef.current) {
      return;
    }

    lastRenderedKeyRef.current = currentKey;
    isRenderingRef.current = true;
    setIsRendering(true);

    try {
      if (canvas.width !== 1080 || canvas.height !== 1080) {
        canvas.width = 1080;
        canvas.height = 1080;
      }
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = "high";

      const fontFamilies = Array.from(
        new Set(
          [
            layout.metadata.brand.font_family,
            ...layout.textBlocks.map(
              tb => tb.fontFamily || layout.metadata.brand.font_family
            ),
          ].filter(Boolean)
        )
      );

      const fontLoadResults = await loadFonts(fontFamilies);
      await document.fonts.ready;
      await new Promise(resolve => setTimeout(resolve, 100));

      // TODO(rohan): this is kinda weird, don't know if we need this anymore
      for (const result of fontLoadResults) {
        if (result.loaded) {
          const testCanvas = document.createElement("canvas");
          const testCtx = testCanvas.getContext("2d");
          if (testCtx) {
            const testSize = 56; // CANVAS_TEXT_FONT_SIZE
            const testWeights = ["normal", "bold", "600"];
            let fontWorking = false;

            for (const weight of testWeights) {
              const fontString = prepareFontString(
                weight,
                testSize,
                result.family
              );
              testCtx.font = fontString;
              const withFont = testCtx.measureText("Test Font").width;

              testCtx.font = `${weight} ${testSize}px sans-serif`;
              const fallback = testCtx.measureText("Test Font").width;

              if (Math.abs(withFont - fallback) > 1) {
                fontWorking = true;
                break;
              }
            }

            if (!fontWorking) {
              console.error(
                `❌ Font ${result.family} failed canvas test - will use fallback`
              );
            }
          }
        } else {
          console.warn(`Failed to load font ${result.family}:`, result.error);
        }
      }

      await new Promise(resolve => setTimeout(resolve, 500));

      if (selectedTemplate && businessProfile) {
        try {
          await renderTemplateToCanvas(
            ctx,
            selectedTemplate,
            businessProfile,
            canvas.width,
            canvas.height
          );
          // Draw debug visualization after template is rendered
          drawAvailableAreaDebug(ctx, selectedTemplate);
        } catch (error) {
          console.error("Error rendering selectedTemplate:", error);
          await renderBackground(
            ctx,
            layout.background,
            layout,
            businessProfile
          );
        }
      } else {
        await renderBackground(ctx, layout.background, layout, businessProfile);
      }

      if (layout.textBlocks.length > 0) {
        await renderText(
          ctx,
          layout.textBlocks,
          layout,
          businessProfile,
          selectedTemplate
        );
      }

      if (layout.images.length > 0) {
        await renderImages(
          ctx,
          layout.images,
          businessProfile,
          selectedTemplate,
          layout.textBlocks,
          layout
        );
      }

      const imageData = canvas.toDataURL("image/png", 1.0);

      isRenderingRef.current = false;
      setIsRendering(false);
      onComplete?.(imageData);
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Unknown rendering error";
      console.error("Rendering error:", error);

      isRenderingRef.current = false;
      setIsRendering(false);

      onError?.(errorMessage);
    }
  }, [
    layout,
    selectedTemplate,
    businessProfile,
    loadFonts,
    onComplete,
    onError,
  ]);

  useEffect(() => {
    if (!layout || isRenderingRef.current) return;

    const currentKey = getLayoutKey(layout, selectedTemplate);
    if (lastRenderedKeyRef.current === currentKey) {
      return;
    }

    const timeoutId = setTimeout(() => {
      renderPost();
    }, 0);

    return () => clearTimeout(timeoutId);
  }, [layout, renderPost, selectedTemplate, businessProfile]);

  const forceRedraw = useCallback(() => {
    lastRenderedKeyRef.current = "";
    isRenderingRef.current = false;
    renderPost();
  }, [renderPost]);

  return {
    canvasRef,
    isRendering,
    renderPost,
    forceRedraw,
  };
};
