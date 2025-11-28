import {
  BackgroundConfig,
  ImageElement,
  TextBlock,
  LayoutJSON,
} from "../types/Layout";
import { layoutElementsSequentially } from "./sequentialLayoutEngine";
import { getTemplateConfig } from "../config/templateAreas";
import {
  prepareFontString,
  getFontSizeByComponentType,
  renderSingleLineBanner,
} from "./textUtils";
import { getTextColor } from "./textRenderer";
import { CANVAS_LINE_HEIGHT_MULTIPLIER } from "./canvasConstants";
import {
  isLogo,
  calculateImageDimensions,
  calculateCenteredPosition,
  calculateLogoPosition,
  isValidImageUrl,
} from "./imageUtils";
import { getFirstTextBlockY } from "./collisionUtils";
import { TemplateType } from "../config/templates";
import { BusinessProfile } from "../constants/mockBusinessProfiles";

/**
 * Apply text transform based on business profile design components
 */
const applyTextTransform = (
  text: string,
  componentType: string,
  templateBusinessProfile?: BusinessProfile
): string => {
  if (!templateBusinessProfile?.designComponents?.componentRules) {
    return text;
  }

  const componentRules =
    templateBusinessProfile.designComponents.componentRules;
  const componentRule =
    componentRules[componentType as keyof typeof componentRules];
  if (!componentRule?.styling?.textTransform) {
    return text;
  }

  const transform = componentRule.styling.textTransform;
  switch (transform) {
    case "uppercase":
      return text.toUpperCase();
    case "lowercase":
      // Apply sentence case: first letter of each sentence capitalized, rest lowercase
      return text
        .toLowerCase()
        .replace(
          /(^|[.!?]\s+)([a-z])/g,
          (_, prefix, letter) => prefix + letter.toUpperCase()
        );
    case "capitalize":
      return text.replace(/\b\w/g, l => l.toUpperCase());
    case "none":
    default:
      return text;
  }
};

/**
 * Get text color based on business profile design components
 */
const getComponentTextColor = (
  componentType: string,
  templateBusinessProfile?: BusinessProfile,
  businessProfile?: { primary_color?: string; secondary_color?: string },
  defaultColor?: string
): string => {
  if (!templateBusinessProfile?.designComponents?.componentRules) {
    return defaultColor || "#333333";
  }

  const componentRules =
    templateBusinessProfile.designComponents.componentRules;
  const componentRule =
    componentRules[componentType as keyof typeof componentRules];
  if (!componentRule?.styling?.color) {
    return defaultColor || "#333333";
  }

  const color = componentRule.styling.color;
  if (color === "primary") {
    return (
      businessProfile?.primary_color ||
      templateBusinessProfile.colorPalette?.primary ||
      "#333333"
    );
  }

  return color;
};

/**
 * Get font weight based on business profile design components
 */
const getComponentFontWeight = (
  componentType: string,
  templateBusinessProfile?: BusinessProfile,
  defaultFontWeight?: string
): string => {
  if (!templateBusinessProfile?.designComponents?.componentRules) {
    return defaultFontWeight || "normal";
  }

  const componentRules =
    templateBusinessProfile.designComponents.componentRules;
  const componentRule =
    componentRules[componentType as keyof typeof componentRules];
  if (!componentRule?.styling?.fontWeight) {
    return defaultFontWeight || "normal";
  }

  return componentRule.styling.fontWeight;
};

export const renderBackground = async (
  ctx: CanvasRenderingContext2D,
  background: BackgroundConfig,
  layout: LayoutJSON,
  businessProfile: BusinessProfile
) => {
  const canvas = ctx.canvas;

  if (
    background.type === "solid" &&
    layout.metadata.template === "promotional"
  ) {
    const primaryColor =
      businessProfile.colorPalette?.primary ||
      layout.metadata.brand.primary_color ||
      "#4CAF50";
    const secondaryColor =
      businessProfile.colorPalette?.secondary ||
      layout.metadata.brand.secondary_color ||
      "#81C784";

    const gradient = ctx.createLinearGradient(
      0,
      0,
      canvas.width,
      canvas.height
    );
    gradient.addColorStop(0, primaryColor);
    gradient.addColorStop(1, secondaryColor);

    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  } else if (background.type === "solid") {
    const primaryColor =
      businessProfile.colorPalette?.primary ||
      layout.metadata.brand.primary_color;
    const secondaryColor =
      businessProfile.colorPalette?.secondary ||
      layout.metadata.brand.secondary_color;

    if (primaryColor && secondaryColor && primaryColor !== secondaryColor) {
      const gradient = ctx.createLinearGradient(
        0,
        0,
        canvas.width,
        canvas.height
      );
      gradient.addColorStop(0, primaryColor);
      gradient.addColorStop(1, secondaryColor);
      ctx.fillStyle = gradient;
    } else {
      ctx.fillStyle = background.colors[0] || "#ffffff";
    }
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  } else if (background.type === "linear-gradient") {
    const angle = ((background.direction || 45) * Math.PI) / 180;
    const x1 = Math.cos(angle) * canvas.width;
    const y1 = Math.sin(angle) * canvas.height;

    const gradient = ctx.createLinearGradient(0, 0, x1, y1);
    background.colors.forEach((color: string, index: number) => {
      gradient.addColorStop(index / (background.colors.length - 1), color);
    });

    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  } else if (background.type === "radial-gradient") {
    const gradient = ctx.createRadialGradient(
      canvas.width / 2,
      canvas.height / 2,
      0,
      canvas.width / 2,
      canvas.height / 2,
      Math.max(canvas.width, canvas.height) / 2
    );

    background.colors.forEach((color: string, index: number) => {
      gradient.addColorStop(index / (background.colors.length - 1), color);
    });

    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  }
};

export const renderText = async (
  ctx: CanvasRenderingContext2D,
  textBlocks: TextBlock[],
  layout: LayoutJSON,
  businessProfile: BusinessProfile,
  selectedTemplate?: TemplateType
) => {
  if (textBlocks.length === 0) return;

  const logoImage = layout.images?.find(img => isLogo(img));

  const fontFamily = layout.metadata.brand.font_family || "Arial, sans-serif";

  // Use selected template or business profile's default template
  const templateName: TemplateType =
    selectedTemplate ||
    (businessProfile.defaultTemplate as TemplateType) ||
    TemplateType.GENERAL_CROSS_PATTERN;

  const layoutResult = layoutElementsSequentially(
    ctx,
    templateName,
    textBlocks,
    logoImage || null,
    fontFamily
  );

  for (const block of layoutResult.textBlocks) {
    const originalBlock = textBlocks.find(b => b.id === block.id);
    if (!originalBlock) continue;

    // Get font weight with design component support
    const componentFontWeight = getComponentFontWeight(
      originalBlock.componentType || "bodyText",
      businessProfile,
      originalBlock.fontWeight || "normal"
    );
    const fontWeight = componentFontWeight;
    const fontSize = getFontSizeByComponentType(originalBlock.componentType);
    const fontFamily =
      originalBlock.fontFamily ||
      layout.metadata.brand.font_family ||
      "Arial, sans-serif";

    // Get text color with design component support
    const componentTextColor = getComponentTextColor(
      originalBlock.componentType || "bodyText",
      businessProfile,
      {
        primary_color: businessProfile.colorPalette?.primary,
        secondary_color: businessProfile.colorPalette?.secondary,
      },
      getTextColor(originalBlock, templateName)
    );

    const alignment = originalBlock.alignment || "left";

    if (originalBlock.componentType === "specialBannerText") {
      const primaryColor =
        businessProfile.colorPalette?.primary ||
        layout.metadata.brand.primary_color ||
        "#4CAF50";

      let currentY = block.y;
      const lineSpacing = fontSize * 0.3;

      for (const line of block.lines) {
        const transformedLine = applyTextTransform(
          line,
          originalBlock.componentType || "specialBannerText",
          businessProfile
        );

        const bannerY = currentY + fontSize / 2 + 20; // fontSize/2 + paddingY from banner

        renderSingleLineBanner(
          ctx,
          transformedLine,
          block.x,
          bannerY,
          fontSize,
          primaryColor,
          900,
          fontFamily
        );
        currentY += fontSize + 40 + lineSpacing;
      }
    } else {
      ctx.font = prepareFontString(fontWeight, fontSize, fontFamily);
      ctx.fillStyle = componentTextColor;
      ctx.textAlign = alignment as CanvasTextAlign;
      ctx.textBaseline = "top"; // Ensure Y coordinate represents the top of the text

      const lineHeight = fontSize * CANVAS_LINE_HEIGHT_MULTIPLIER;
      let currentY = block.y;

      for (const line of block.lines) {
        // Apply text transform for regular text
        const transformedLine = applyTextTransform(
          line,
          originalBlock.componentType || "bodyText",
          businessProfile
        );

        ctx.fillText(transformedLine, block.x, currentY);
        currentY += lineHeight;
      }
    }
  }
};

export const renderImages = async (
  ctx: CanvasRenderingContext2D,
  images: ImageElement[],
  businessProfile: BusinessProfile,
  selectedTemplate?: TemplateType,
  textBlocks?: TextBlock[],
  layout?: LayoutJSON
) => {
  const verticalOffset = selectedTemplate ? 300 : 0;

  const templateConfig = selectedTemplate
    ? getTemplateConfig(selectedTemplate)
    : null;
  let sequentialLogoPosition: {
    x: number;
    y: number;
    width: number;
    height: number;
  } | null = null;

  if (templateConfig && selectedTemplate && textBlocks && layout) {
    const logoImage = images.find(img => isLogo(img));

    if (logoImage) {
      const fontFamily =
        layout.metadata.brand.font_family || "Arial, sans-serif";
      const layoutResult = layoutElementsSequentially(
        ctx,
        selectedTemplate,
        textBlocks,
        logoImage,
        fontFamily
      );
      sequentialLogoPosition = layoutResult.logo;
    }
  }

  const firstTextBlockY = getFirstTextBlockY(
    selectedTemplate,
    textBlocks,
    verticalOffset
  );

  for (let i = 0; i < images.length; i++) {
    const imageConfig = images[i];

    try {
      ctx.globalAlpha = imageConfig.opacity || 1;

      let imageUrl = imageConfig.src;

      if (
        isLogo(imageConfig) &&
        (businessProfile.logoUrl || businessProfile.postLogoUrl)
      ) {
        imageUrl = businessProfile.postLogoUrl || businessProfile.logoUrl || "";
      }

      if (!isValidImageUrl(imageUrl)) {
        ctx.globalAlpha = 1;
        continue;
      }

      if (isValidImageUrl(imageUrl)) {
        const img = new Image();
        img.crossOrigin = "anonymous";

        await new Promise<void>(resolve => {
          img.onload = () => {
            try {
              let drawPosition;

              if (selectedTemplate && isLogo(imageConfig)) {
                drawPosition = calculateLogoPosition(
                  imageConfig,
                  img,
                  firstTextBlockY,
                  ctx.canvas.width,
                  verticalOffset,
                  sequentialLogoPosition
                );
              } else {
                const dimensions = calculateImageDimensions(
                  img,
                  imageConfig.width,
                  imageConfig.height
                );
                const position = calculateCenteredPosition(
                  imageConfig.position.x,
                  imageConfig.position.y,
                  imageConfig.width,
                  imageConfig.height,
                  dimensions.width,
                  dimensions.height,
                  verticalOffset
                );
                drawPosition = {
                  x: position.x,
                  y: position.y,
                  width: dimensions.width,
                  height: dimensions.height,
                };
              }

              ctx.drawImage(
                img,
                drawPosition.x,
                drawPosition.y,
                drawPosition.width,
                drawPosition.height
              );

              if (selectedTemplate && isLogo(imageConfig)) {
                // Check if debug mode is enabled (same flag as in usePostRenderer)
                // You can enable this by setting DEBUG_SHOW_AVAILABLE_AREA = true in usePostRenderer.ts
                const debugEnabled =
                  typeof window !== "undefined" &&
                  (window as unknown as Record<string, unknown>)
                    .DEBUG_SHOW_AVAILABLE_AREA === true;

                if (debugEnabled) {
                  ctx.save();
                  ctx.strokeStyle = "#0000FF"; // Blue color for logo bounds
                  ctx.lineWidth = 3;
                  ctx.setLineDash([8, 4]); // Different dash pattern than template bounds
                  ctx.strokeRect(
                    drawPosition.x,
                    drawPosition.y,
                    drawPosition.width,
                    drawPosition.height
                  );

                  ctx.fillStyle = "#0000FF";
                  ctx.font = "14px Arial";
                  ctx.setLineDash([]); // Reset dash for text
                  ctx.fillText(
                    "Logo bounds",
                    drawPosition.x + 5,
                    drawPosition.y - 5
                  );
                  ctx.restore();
                }
              }

              resolve();
            } catch (drawError) {
              console.error(
                `[renderImages] Failed to draw image ${imageConfig.src}:`,
                {
                  imageId: imageConfig.id,
                  imageUrl,
                  error: drawError,
                  errorMessage:
                    drawError instanceof Error
                      ? drawError.message
                      : String(drawError),
                }
              );
              resolve();
            }
          };

          img.onerror = error => {
            console.error(`[renderImages] Failed to load image ${imageUrl}:`, {
              imageId: imageConfig.id,
              imageUrl,
              error,
            });
            resolve();
          };

          img.src = imageUrl;
        });
      }

      ctx.globalAlpha = 1;
    } catch (error) {
      console.error(
        `[renderImages] Exception while processing image ${imageConfig.src}:`,
        {
          imageId: imageConfig.id,
          error,
          errorMessage: error instanceof Error ? error.message : String(error),
        }
      );
    }
  }
};
