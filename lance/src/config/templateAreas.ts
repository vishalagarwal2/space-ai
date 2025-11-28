/**
 * Template Content Area Definitions
 * Defines the safe rectangular area where elements can be placed
 */

import { TemplateType } from "./templates";

export interface TemplateArea {
  topLeft: { x: number; y: number };
  topRight: { x: number; y: number };
  bottomLeft: { x: number; y: number };
  bottomRight: { x: number; y: number };
}

export interface LogoPlacement {
  bounds: TemplateArea;
  alignment: "left" | "center" | "right";
  sizeIncrease?: number;
}

export interface TemplateConfig {
  name: string;
  availableAreaToPlaceElements: TemplateArea;
  logoPlacement?: LogoPlacement;
}

/**
 * Template configurations - coordinates define safe content rectangles
 */
export const TEMPLATE_CONFIGS: Record<TemplateType, TemplateConfig> = {
  // General Templates - coordinates updated to include the 40px padding that was previously added in calculateContentBounds
  [TemplateType.GENERAL_CROSS_PATTERN]: {
    name: "Cross Pattern",
    availableAreaToPlaceElements: {
      topLeft: { x: 140, y: 340 },
      topRight: { x: 940, y: 340 },
      bottomLeft: { x: 140, y: 960 },
      bottomRight: { x: 940, y: 960 },
    },
  },

  [TemplateType.GENERAL_GRID_PATTERN]: {
    name: "Grid Pattern",
    availableAreaToPlaceElements: {
      topLeft: { x: 80, y: 260 },
      topRight: { x: 700, y: 260 },
      bottomLeft: { x: 80, y: 1000 },
      bottomRight: { x: 700, y: 1000 },
    },
  },

  [TemplateType.GENERAL_BORDER_PATTERN]: {
    name: "Border Pattern",
    availableAreaToPlaceElements: {
      topLeft: { x: 140, y: 400 },
      topRight: { x: 940, y: 400 },
      bottomLeft: { x: 140, y: 1000 },
      bottomRight: { x: 940, y: 1000 },
    },
    logoPlacement: {
      bounds: {
        topLeft: { x: 650, y: 150 },
        topRight: { x: 950, y: 150 },
        bottomLeft: { x: 650, y: 450 },
        bottomRight: { x: 950, y: 450 },
      },
      alignment: "right",
      sizeIncrease: 120,
    },
  },

  // Miraai-specific templates
  [TemplateType.MIRAAI_MODERN_IMAGE]: {
    name: "Miraai Modern",
    availableAreaToPlaceElements: {
      topLeft: { x: 160, y: 480 },
      topRight: { x: 930, y: 480 },
      bottomLeft: { x: 160, y: 960 },
      bottomRight: { x: 930, y: 960 },
    },
  },

  [TemplateType.MIRAAI_CREATIVE_IMAGE]: {
    name: "Miraai Creative",
    availableAreaToPlaceElements: {
      topLeft: { x: 140, y: 300 },
      topRight: { x: 940, y: 300 },
      bottomLeft: { x: 140, y: 810 },
      bottomRight: { x: 940, y: 810 },
    },
    logoPlacement: {
      bounds: {
        topLeft: { x: 100, y: 100 },
        topRight: { x: 350, y: 100 },
        bottomLeft: { x: 100, y: 350 },
        bottomRight: { x: 350, y: 350 },
      },
      alignment: "left",
      sizeIncrease: 60,
    },
  },

  [TemplateType.MIRAAI_STYLISH_IMAGE]: {
    name: "Miraai Stylish",
    availableAreaToPlaceElements: {
      topLeft: { x: 140, y: 400 },
      topRight: { x: 940, y: 400 },
      bottomLeft: { x: 140, y: 760 },
      bottomRight: { x: 940, y: 760 },
    },
  },
  [TemplateType.TAILWIND_MODERN_IMAGE]: {
    name: "Tailwind Modern",
    availableAreaToPlaceElements: {
      topLeft: { x: 160, y: 30 },
      topRight: { x: 930, y: 30 },
      bottomLeft: { x: 160, y: 500 },
      bottomRight: { x: 930, y: 500 },
    },
  },
};

/**
 * Get bounds from template area (helper function)
 */
export function getAreaBounds(area: TemplateArea) {
  return {
    x: area.topLeft.x,
    y: area.topLeft.y,
    width: area.topRight.x - area.topLeft.x,
    height: area.bottomLeft.y - area.topLeft.y,
  };
}

/**
 * Get template config by template type
 */
export function getTemplateConfig(
  templateType: TemplateType
): TemplateConfig | null {
  return TEMPLATE_CONFIGS[templateType] || null;
}
