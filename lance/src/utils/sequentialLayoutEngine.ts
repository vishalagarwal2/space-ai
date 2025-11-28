/**
 * Sequential Layout Engine
 * Places logo and text blocks sequentially within a defined content area
 * without overlap or overflow
 */

import { TextBlock, ImageElement } from "../types/Layout";
import {
  getTemplateConfig,
  getAreaBounds,
  TemplateConfig,
} from "../config/templateAreas";
import {
  CANVAS_LINE_HEIGHT_MULTIPLIER,
  LOGO_TO_TEXT_GAP,
  DEFAULT_BLOCK_SPACING,
} from "./canvasConstants";
import { prepareFontString, getFontSizeByComponentType } from "./textUtils";
import { TemplateType } from "../services/templateRenderer";

export interface LayoutResult {
  logo: {
    x: number;
    y: number;
    width: number;
    height: number;
  } | null;
  textBlocks: Array<{
    id: string;
    x: number;
    y: number;
    width: number;
    height: number;
    lines: string[];
  }>;
}

interface ContentBounds {
  x: number;
  y: number;
  width: number;
  height: number;
}

interface LogoPlacement {
  x: number;
  y: number;
  width: number;
  height: number;
}

interface TextMeasurement {
  height: number;
  lines: string[];
}

function breakTextIntoLines(
  ctx: CanvasRenderingContext2D,
  text: string,
  maxWidth: number,
  alignment: string = "left",
  contentBounds: { x: number; width: number }
): string[] {
  const words = text.split(" ");
  const lines: string[] = [];
  let currentLine = "";

  const SAFETY_MARGIN = 30;
  const availableWidth = contentBounds.width - SAFETY_MARGIN * 2;

  const effectiveMaxWidth = Math.min(maxWidth, availableWidth);

  for (const word of words) {
    const testLine = currentLine + (currentLine ? " " : "") + word;
    const testLineWidth = ctx.measureText(testLine).width;

    if (testLineWidth > effectiveMaxWidth && currentLine) {
      lines.push(currentLine);
      currentLine = word;
    } else {
      currentLine = testLine;
    }
  }

  if (currentLine) {
    lines.push(currentLine);
  }

  return lines;
}

function calculateTextHeight(
  ctx: CanvasRenderingContext2D,
  text: string,
  maxWidth: number,
  fontSize: number,
  alignment: string = "left",
  contentBounds: { x: number; width: number }
): TextMeasurement {
  const lines = breakTextIntoLines(
    ctx,
    text,
    maxWidth,
    alignment,
    contentBounds
  );
  const lineHeight = fontSize * CANVAS_LINE_HEIGHT_MULTIPLIER;

  return {
    height: lines.length * lineHeight,
    lines,
  };
}

function calculateBannerTextHeight(
  baseHeight: number,
  lines: string[],
  fontSize: number
): number {
  const bannerPaddingPerLine = 40;
  const lineSpacing = fontSize * 0.3;
  const numLines = lines.length;
  const numGaps = Math.max(0, numLines - 1);

  return baseHeight + bannerPaddingPerLine * numLines + lineSpacing * numGaps;
}

function getTextXPosition(
  alignment: string | undefined,
  contentX: number,
  contentWidth: number
): number {
  // Add safety margin to prevent text from touching the edges
  const SAFETY_MARGIN = 30;

  if (alignment === "center") {
    return contentX + contentWidth / 2;
  } else if (alignment === "right") {
    return contentX + contentWidth - SAFETY_MARGIN;
  }
  // For left alignment, start from the left edge of content area plus margin
  return contentX + SAFETY_MARGIN;
}

function calculateLogoDimensions(
  logoImage: ImageElement,
  maxWidth: number,
  maxHeight?: number
): { width: number; height: number } {
  // Get aspect ratio from image dimensions or use default
  const aspectRatio =
    logoImage.width && logoImage.height
      ? logoImage.width / logoImage.height
      : 1.5;

  // Calculate dimensions that fit within constraints while maintaining aspect ratio
  let logoWidth = maxWidth;
  let logoHeight = logoWidth / aspectRatio;

  // If maxHeight is specified and logo exceeds it, scale down based on height constraint
  if (maxHeight && logoHeight > maxHeight) {
    logoHeight = maxHeight;
    logoWidth = logoHeight * aspectRatio;
  }

  return { width: logoWidth, height: logoHeight };
}

function calculateLogoXPosition(
  alignment: string,
  bounds: ContentBounds,
  logoWidth: number
): number {
  switch (alignment) {
    case "left":
      return bounds.x;
    case "right":
      return bounds.x + bounds.width - logoWidth;
    case "center":
    default:
      return bounds.x + (bounds.width - logoWidth) / 2;
  }
}

function placeLogoWithCustomConfig(
  logoImage: ImageElement,
  config: TemplateConfig
): LogoPlacement {
  if (!config.logoPlacement) {
    throw new Error("Logo placement configuration is required");
  }

  const logoBounds = getAreaBounds(config.logoPlacement.bounds);
  const logoAlignment = config.logoPlacement.alignment;

  let baseLogoWidth = 300;
  if (config.logoPlacement.sizeIncrease) {
    baseLogoWidth += config.logoPlacement.sizeIncrease;
  }

  const maxLogoWidth = Math.min(baseLogoWidth, logoBounds.width);
  const maxLogoHeight = logoBounds.height;

  const { width: logoWidth, height: logoHeight } = calculateLogoDimensions(
    logoImage,
    maxLogoWidth,
    maxLogoHeight
  );

  const logoX = calculateLogoXPosition(logoAlignment, logoBounds, logoWidth);

  const result = {
    x: logoX,
    y: logoBounds.y,
    width: logoWidth,
    height: logoHeight,
  };

  return result;
}

function placeLogoWithDefaultConfig(
  logoImage: ImageElement,
  contentBounds: ContentBounds
): LogoPlacement {
  const maxLogoWidth = Math.min(400, contentBounds.width * 0.6);
  const maxLogoHeight = Math.min(250, contentBounds.height * 0.25);

  const { width: logoWidth, height: logoHeight } = calculateLogoDimensions(
    logoImage,
    maxLogoWidth,
    maxLogoHeight
  );

  const logoX = contentBounds.x + (contentBounds.width - logoWidth) / 2;

  const result = {
    x: logoX,
    y: contentBounds.y,
    width: logoWidth,
    height: logoHeight,
  };

  return result;
}

function calculateContentBounds(
  templateName: TemplateType,
  canvasWidth: number,
  canvasHeight: number
): ContentBounds {
  const config = getTemplateConfig(templateName);

  const defaultBounds = {
    x: 60,
    y: 60,
    width: canvasWidth - 120,
    height: canvasHeight - 120,
  };

  if (!config) {
    return defaultBounds;
  }

  const bounds = getAreaBounds(config.availableAreaToPlaceElements);

  const expectedWidth = 1080;
  const expectedHeight = 1080;
  const scaleX = canvasWidth / expectedWidth;
  const scaleY = canvasHeight / expectedHeight;

  const scaledBounds = {
    x: bounds.x * scaleX,
    y: bounds.y * scaleY,
    width: bounds.width * scaleX,
    height: bounds.height * scaleY,
  };

  return scaledBounds;
}

function drawDebugVisualization(
  ctx: CanvasRenderingContext2D,
  block: TextBlock,
  contentX: number,
  currentY: number,
  contentWidth: number,
  height: number,
  spacing: number
): void {
  const blockSpacing = DEFAULT_BLOCK_SPACING;

  ctx.fillStyle = "rgba(135, 206, 250, 0.3)";
  ctx.fillRect(contentX, currentY, contentWidth, height);

  if (spacing > blockSpacing) {
    ctx.fillStyle = "rgba(255, 182, 193, 0.5)";
    ctx.fillRect(contentX, currentY + height, contentWidth, spacing);
  } else {
    ctx.fillStyle = "rgba(144, 238, 144, 0.3)";
    ctx.fillRect(contentX, currentY + height, contentWidth, spacing);
  }

  ctx.fillStyle = "rgba(0, 0, 0, 0.8)";
  ctx.font = "12px Arial";
  ctx.fillText(
    `${block.componentType || "default"}: ${block.id}`,
    contentX + 5,
    currentY + 15
  );
}

export function layoutElementsSequentially(
  ctx: CanvasRenderingContext2D,
  templateName: TemplateType,
  textBlocks: TextBlock[],
  logoImage: ImageElement | null,
  fontFamily: string = "Arial"
): LayoutResult {
  const config = getTemplateConfig(templateName);
  const DEBUG_SPACING = false;

  const contentBounds = calculateContentBounds(
    templateName,
    ctx.canvas.width,
    ctx.canvas.height
  );

  let currentY = contentBounds.y;
  const result: LayoutResult = {
    logo: null,
    textBlocks: [],
  };

  if (logoImage) {
    let logoPlacement: LogoPlacement;

    if (config?.logoPlacement) {
      logoPlacement = placeLogoWithCustomConfig(logoImage, config);
    } else {
      logoPlacement = placeLogoWithDefaultConfig(logoImage, contentBounds);
    }

    result.logo = logoPlacement;

    const logoBottom = logoPlacement.y + logoPlacement.height;

    if (config?.logoPlacement) {
      const logoOverlapsContent =
        logoPlacement.y < contentBounds.y + contentBounds.height &&
        logoBottom > contentBounds.y;

      if (logoOverlapsContent) {
        currentY = Math.max(currentY, logoBottom + LOGO_TO_TEXT_GAP);
      } else {
      }
    } else {
      currentY = logoBottom + LOGO_TO_TEXT_GAP;
    }
  }

  const sortedBlocks = [...textBlocks].sort((a, b) => a.order - b.order);

  for (const block of sortedBlocks) {
    const fontWeight = block.fontWeight || "normal";
    const fontSize = getFontSizeByComponentType(block.componentType);

    ctx.font = prepareFontString(fontWeight, fontSize, fontFamily);

    const textX = getTextXPosition(
      block.alignment,
      contentBounds.x,
      contentBounds.width
    );

    const { height: baseHeight, lines } = calculateTextHeight(
      ctx,
      block.text,
      contentBounds.width,
      fontSize,
      block.alignment || "left",
      { x: contentBounds.x, width: contentBounds.width }
    );

    let height = baseHeight;
    if (block.componentType === "specialBannerText") {
      height = calculateBannerTextHeight(baseHeight, lines, fontSize);
    }

    result.textBlocks.push({
      id: block.id,
      x: textX,
      y: currentY,
      width: contentBounds.width,
      height: height,
      lines,
    });

    if (DEBUG_SPACING && ctx) {
      const spacing = DEFAULT_BLOCK_SPACING;
      drawDebugVisualization(
        ctx,
        block,
        contentBounds.x,
        currentY,
        contentBounds.width,
        height,
        spacing
      );
    }

    currentY += height + DEFAULT_BLOCK_SPACING;
  }

  return result;
}
