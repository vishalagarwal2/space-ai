import { ImageElement } from "../types/Layout";

/**
 * Check if an image element is a logo
 * Standardized check: logos are identified by id === "brand-logo" or src === "logo.png"
 */
export const isLogo = (imageConfig: ImageElement): boolean =>
  imageConfig.id === "brand-logo" || imageConfig.src === "logo.png";

/**
 * Calculate aspect ratio-adjusted dimensions for image rendering
 */
export const calculateImageDimensions = (
  img: HTMLImageElement,
  targetWidth: number,
  targetHeight: number
): { width: number; height: number } => {
  const imgAspectRatio = img.width / img.height;
  const targetAspectRatio = targetWidth / targetHeight;

  if (imgAspectRatio > targetAspectRatio) {
    return {
      width: targetWidth,
      height: targetWidth / imgAspectRatio,
    };
  } else {
    return {
      width: targetHeight * imgAspectRatio,
      height: targetHeight,
    };
  }
};

/**
 * Calculate centered position for image within bounds
 */
export const calculateCenteredPosition = (
  originalX: number,
  originalY: number,
  originalWidth: number,
  originalHeight: number,
  actualWidth: number,
  actualHeight: number,
  verticalOffset: number = 0
): { x: number; y: number } => {
  return {
    x: originalX + (originalWidth - actualWidth) / 2,
    y: originalY + (originalHeight - actualHeight) / 2 + verticalOffset,
  };
};

/**
 * Calculate logo position for template layouts
 */
export const calculateLogoPosition = (
  imageConfig: ImageElement,
  img: HTMLImageElement,
  firstTextBlockY: number | null,
  canvasWidth: number,
  verticalOffset: number,
  sequentialLogoPosition?: {
    x: number;
    y: number;
    width: number;
    height: number;
  } | null
): { x: number; y: number; width: number; height: number } => {
  if (sequentialLogoPosition) {
    // Use the sequential layout position and bounds, but calculate proper aspect ratio within those bounds
    const imgAspectRatio = img.width / img.height;
    const maxWidth = sequentialLogoPosition.width;
    const maxHeight = sequentialLogoPosition.height;

    // Calculate dimensions that fit within the sequential layout bounds while maintaining aspect ratio
    let drawWidth = maxWidth;
    let drawHeight = drawWidth / imgAspectRatio;

    // If height exceeds bounds, scale down based on height constraint
    if (drawHeight > maxHeight) {
      drawHeight = maxHeight;
      drawWidth = drawHeight * imgAspectRatio;
    }

    // Center the logo within the sequential layout bounds
    const drawX = sequentialLogoPosition.x + (maxWidth - drawWidth) / 2;
    const drawY = sequentialLogoPosition.y + (maxHeight - drawHeight) / 2;

    return { x: drawX, y: drawY, width: drawWidth, height: drawHeight };
  } else if (firstTextBlockY !== null) {
    const sizeIncrease = 150;
    const drawWidth = imageConfig.width + sizeIncrease;
    const drawHeight = drawWidth / (img.width / img.height);

    const logoSpacing = 180;
    const drawX = (canvasWidth - drawWidth) / 2;
    const drawY = firstTextBlockY - drawHeight - logoSpacing + verticalOffset;

    return { x: drawX, y: drawY, width: drawWidth, height: drawHeight };
  }

  return {
    x: imageConfig.position.x,
    y: imageConfig.position.y + verticalOffset,
    width: imageConfig.width,
    height: imageConfig.height,
  };
};

/**
 * Validate if an image URL is valid
 */
export const isValidImageUrl = (url?: string): boolean => {
  if (!url) return false;
  return (
    url.startsWith("http") || url.startsWith("data:") || url.startsWith("/")
  );
};
