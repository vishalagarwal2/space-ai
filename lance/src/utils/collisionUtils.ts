import { LayoutJSON, TextBlock } from "../types/Layout";
import { isLogo } from "./imageUtils";
import { TemplateType } from "../config/templates";

/**
 * Get the actual logo area bounds from the layout images array
 * Returns null if no logo is found
 */
export const getLogoAreaFromLayout = (
  layout: LayoutJSON,
  canvasWidth: number,
  template?: TemplateType,
  verticalOffset: number = 0,
  textBlocks?: TextBlock[]
): { left: number; right: number; top: number; bottom: number } | null => {
  const logoImage = layout.images?.find(img => isLogo(img));

  if (!logoImage) {
    return {
      left: 920,
      right: 1000,
      top: 40,
      bottom: 140,
    };
  }

  let logoX = logoImage.position.x;
  let logoY = logoImage.position.y + verticalOffset;
  const baseLogoWidth = logoImage.width || 100;
  const logoWidth = baseLogoWidth;
  const baseLogoHeight = logoImage.height || 100;
  let logoHeight = baseLogoHeight;

  if (template && textBlocks && textBlocks.length > 0) {
    const topRightX = canvasWidth - 60;

    logoX = Math.min(logoX, topRightX - logoWidth);

    logoY = Math.min(logoY, verticalOffset + 40);
    logoHeight = Math.max(logoHeight, 150);
  }

  const padding = 15;

  return {
    left: logoX - padding,
    right: logoX + logoWidth + padding,
    top: logoY - padding,
    bottom: logoY + logoHeight + padding,
  };
};

/**
 * Check if two rectangles overlap
 */
export const rectanglesOverlap = (
  rect1: { left: number; right: number; top: number; bottom: number },
  rect2: { left: number; right: number; top: number; bottom: number }
): boolean => {
  return !(
    rect1.right < rect2.left ||
    rect1.left > rect2.right ||
    rect1.bottom < rect2.top ||
    rect1.top > rect2.bottom
  );
};

/**
 * Adjust text position/size to avoid logo overlap (flexbox-like behavior)
 * Returns adjusted { x, maxWidth } that ensures no overlap
 */
export const adjustForLogoCollision = (
  textBox: { left: number; right: number; top: number; bottom: number },
  logoArea: { left: number; right: number; top: number; bottom: number },
  originalX: number,
  originalMaxWidth: number,
  alignment: "left" | "center" | "right",
  canvasWidth: number,
  padding: number
): { x: number; maxWidth: number } => {
  if (!rectanglesOverlap(textBox, logoArea)) {
    return { x: originalX, maxWidth: originalMaxWidth };
  }

  let adjustedX = originalX;
  let adjustedMaxWidth = originalMaxWidth;

  switch (alignment) {
    case "left":
      if (textBox.right > logoArea.left) {
        const maxWidthToAvoidLogo = logoArea.left - textBox.left - padding;
        adjustedMaxWidth = Math.max(
          0,
          Math.min(adjustedMaxWidth, maxWidthToAvoidLogo)
        );
      }
      break;

    case "center":
      if (textBox.right > logoArea.left || textBox.left < logoArea.right) {
        const overlapWidth = Math.max(
          textBox.right - logoArea.left,
          logoArea.right - textBox.left
        );
        const reduction = overlapWidth + padding;
        adjustedMaxWidth = Math.max(0, adjustedMaxWidth - reduction);

        if (adjustedMaxWidth <= 0 || textBox.left < logoArea.right) {
          adjustedX = (logoArea.left - padding) / 2;
          adjustedMaxWidth = Math.min(
            originalMaxWidth,
            logoArea.left - padding * 2
          );
        }
      }
      break;

    case "right":
      if (textBox.left < logoArea.right) {
        adjustedX = logoArea.left - padding;
        adjustedMaxWidth = Math.min(originalMaxWidth, adjustedX - padding);
      } else {
        const maxWidthToAvoidLogo = textBox.right - logoArea.left - padding;
        adjustedMaxWidth = Math.max(
          0,
          Math.min(adjustedMaxWidth, maxWidthToAvoidLogo)
        );
      }
      break;
  }

  // Ensure values are within canvas bounds
  adjustedX = Math.max(padding, Math.min(adjustedX, canvasWidth - padding));
  adjustedMaxWidth = Math.max(
    0,
    Math.min(adjustedMaxWidth, canvasWidth - padding * 2)
  );

  return { x: adjustedX, maxWidth: adjustedMaxWidth };
};

/**
 * Find the first text block Y position for logo positioning
 * With sequential layout, we return a default position since blocks are positioned sequentially
 */
export const getFirstTextBlockY = (
  template?: TemplateType,
  textBlocks?: TextBlock[],
  verticalOffset: number = 0
): number | null => {
  if (!template || !textBlocks || textBlocks.length === 0) return null;

  return verticalOffset + 200;
};
