/**
 * Centralized Template Configuration
 * Used across the app for template selection and display
 * Supports both general and business-specific templates
 */

import type { ContentTypeString } from "@/types/ContentCalendar";

export enum TemplateType {
  // General Templates (SVG-based, customizable with business colors)
  GENERAL_CROSS_PATTERN = "general-cross-pattern",
  GENERAL_GRID_PATTERN = "general-grid-pattern",
  GENERAL_BORDER_PATTERN = "general-border-pattern",

  // Miraai Recycling Specific Templates (Image-based, pre-designed)
  MIRAAI_MODERN_IMAGE = "miraai-modern-image",
  MIRAAI_CREATIVE_IMAGE = "miraai-creative-image",
  MIRAAI_STYLISH_IMAGE = "miraai-stylish-image",

  // Tailwind Specific Templates (Image-based, pre-designed)
  TAILWIND_MODERN_IMAGE = "tailwind-modern-image",
}

export type TemplateId = `${TemplateType}`;

export enum TemplateCategory {
  SVG = "svg",
  IMAGE = "image",
}

export enum TemplateScope {
  GENERAL = "general", // Available for all businesses
  BUSINESS_SPECIFIC = "business_specific", // Only for specific businesses
}

export interface TemplateColorConfig {
  textColor: string;
  category: TemplateCategory;
}

export interface TemplateOption {
  id: TemplateId;
  name: string;
  description?: string;
  contentTypes: ContentTypeString[]; // Content types this template can be used for
  colorConfig: TemplateColorConfig;
  scope: TemplateScope;
  businessIds?: string[]; // If business_specific, which businesses can use it
}

/**
 * Available templates with display names and color configurations
 * Organized by scope (general vs business-specific)
 */
export const AVAILABLE_TEMPLATES: TemplateOption[] = [
  // General Templates - Available for all businesses
  {
    id: TemplateType.GENERAL_CROSS_PATTERN,
    name: "Cross Pattern",
    description: "Split layout with decorative cross pattern",
    contentTypes: [
      "promo",
      "educational",
      "behind_scenes",
      "testimonial",
      "holiday",
    ],
    colorConfig: {
      textColor: "#1F2937",
      category: TemplateCategory.SVG,
    },
    scope: TemplateScope.GENERAL,
  },
  {
    id: TemplateType.GENERAL_GRID_PATTERN,
    name: "Grid Pattern",
    description: "Side content with grid background",
    contentTypes: ["promo", "educational", "behind_scenes"],
    colorConfig: {
      textColor: "#111827",
      category: TemplateCategory.SVG,
    },
    scope: TemplateScope.GENERAL,
  },
  {
    id: TemplateType.GENERAL_BORDER_PATTERN,
    name: "Border Pattern",
    description: "Center content with border background",
    contentTypes: ["educational", "testimonial", "holiday"],
    colorConfig: {
      textColor: "#1a1a1a",
      category: TemplateCategory.SVG,
    },
    scope: TemplateScope.GENERAL,
  },

  // Miraai Recycling Specific Templates
  {
    id: TemplateType.MIRAAI_MODERN_IMAGE,
    name: "Miraai Modern",
    description: "Modern design with Miraai branding",
    contentTypes: ["promo", "behind_scenes", "testimonial"],
    colorConfig: {
      textColor: "#1a1a1a",
      category: TemplateCategory.IMAGE,
    },
    scope: TemplateScope.BUSINESS_SPECIFIC,
    businessIds: ["miraai-recycling"],
  },
  {
    id: TemplateType.MIRAAI_CREATIVE_IMAGE,
    name: "Miraai Creative",
    description: "Creative layout with Miraai branding",
    contentTypes: ["promo", "educational", "holiday"],
    colorConfig: {
      textColor: "#1a1a1a",
      category: TemplateCategory.IMAGE,
    },
    scope: TemplateScope.BUSINESS_SPECIFIC,
    businessIds: ["miraai-recycling"],
  },
  {
    id: TemplateType.MIRAAI_STYLISH_IMAGE,
    name: "Miraai Stylish",
    description: "Stylish design with Miraai branding",
    contentTypes: ["promo", "educational", "holiday"],
    colorConfig: {
      textColor: "#1a1a1a",
      category: TemplateCategory.IMAGE,
    },
    scope: TemplateScope.BUSINESS_SPECIFIC,
    businessIds: ["miraai-recycling"],
  },
  {
    id: TemplateType.TAILWIND_MODERN_IMAGE,
    name: "Tailwind Modern",
    description: "Modern design with Tailwind branding",
    contentTypes: ["promo", "educational", "holiday"],
    colorConfig: {
      textColor: "#1a1a1a",
      category: TemplateCategory.IMAGE,
    },
    scope: TemplateScope.BUSINESS_SPECIFIC,
    businessIds: ["tailwind-financial"],
  },
];

/**
 * Default template to use when none specified
 */
export const DEFAULT_TEMPLATE: TemplateId = TemplateType.GENERAL_CROSS_PATTERN;

/**
 * Get template display name by ID
 */
export function getTemplateName(templateId: TemplateId | string): string {
  const template = AVAILABLE_TEMPLATES.find(t => t.id === templateId);
  return template?.name || templateId;
}

/**
 * Get template by ID
 */
export function getTemplate(
  templateId: TemplateId | string
): TemplateOption | undefined {
  return AVAILABLE_TEMPLATES.find(t => t.id === templateId);
}

/**
 * Check if template ID is valid
 */
export function isValidTemplate(templateId: string): templateId is TemplateId {
  return AVAILABLE_TEMPLATES.some(t => t.id === templateId);
}

/**
 * Get templates available for a specific business
 * Includes general templates and business-specific templates
 */
export function getTemplatesForBusiness(businessId?: string): TemplateOption[] {
  return AVAILABLE_TEMPLATES.filter(template => {
    // Include general templates
    if (template.scope === TemplateScope.GENERAL) {
      return true;
    }

    // Include business-specific templates if business matches
    if (template.scope === TemplateScope.BUSINESS_SPECIFIC && businessId) {
      return template.businessIds?.includes(businessId) || false;
    }

    return false;
  });
}

/**
 * Get templates that support a specific content type
 * Optionally filtered by business
 */
export function getTemplatesByContentType(
  contentType: ContentTypeString,
  businessId?: string
): TemplateOption[] {
  const availableTemplates = businessId
    ? getTemplatesForBusiness(businessId)
    : AVAILABLE_TEMPLATES.filter(t => t.scope === TemplateScope.GENERAL);

  return availableTemplates.filter(template =>
    template.contentTypes.includes(contentType)
  );
}

/**
 * Randomly select a template that supports the given content type
 * Prioritizes business-specific templates if available, falls back to general templates
 */
export function getRandomTemplateForContentType(
  contentType: ContentTypeString,
  businessId?: string
): TemplateId {
  const matchingTemplates = getTemplatesByContentType(contentType, businessId);

  if (matchingTemplates.length === 0) {
    console.warn(
      `No templates found for content type "${contentType}" and business "${businessId}", using default template`
    );
    return DEFAULT_TEMPLATE;
  }

  // Prioritize business-specific templates if available
  const businessSpecificTemplates = matchingTemplates.filter(
    t => t.scope === TemplateScope.BUSINESS_SPECIFIC
  );

  const templatesToChooseFrom =
    businessSpecificTemplates.length > 0
      ? businessSpecificTemplates
      : matchingTemplates;

  const randomIndex = Math.floor(Math.random() * templatesToChooseFrom.length);
  return templatesToChooseFrom[randomIndex].id;
}
