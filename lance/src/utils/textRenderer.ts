import { TextBlock } from "../types/Layout";
import { getTemplate, TemplateType } from "../config/templates";

/**
 * Determine text color based on template configuration
 */
export const getTextColor = (
  block: TextBlock,
  template?: TemplateType
): string => {
  let textColor = block.color || "#000000";

  if (template) {
    const templateConfig = getTemplate(template);
    if (templateConfig) {
      textColor = templateConfig.colorConfig.textColor;
    }
  }

  return textColor;
};
