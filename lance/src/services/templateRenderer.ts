import { BusinessProfile } from "../constants/mockBusinessProfiles";
import {
  TemplateType,
  TemplateCategory,
  getTemplate,
} from "../config/templates";

export type { TemplateType };

interface ColorPalette {
  primary: string;
  secondary: string;
  accent?: string;
  background?: string;
}

/**
 * Determines if a template is an image template (PNG/JPEG) vs SVG template
 */
function isImageTemplate(templateType: TemplateType): boolean {
  const template = getTemplate(templateType);
  return template?.colorConfig.category === TemplateCategory.IMAGE;
}

/**
 * Lightens a hex color by a given factor (0-1, where 1 = white)
 */
function lightenColor(hexColor: string, factor: number): string {
  const hex = hexColor.replace("#", "");

  const r = parseInt(hex.substr(0, 2), 16);
  const g = parseInt(hex.substr(2, 2), 16);
  const b = parseInt(hex.substr(4, 2), 16);

  const newR = Math.round(r + (255 - r) * factor);
  const newG = Math.round(g + (255 - g) * factor);
  const newB = Math.round(b + (255 - b) * factor);

  const toHex = (n: number) => n.toString(16).padStart(2, "0");
  return `#${toHex(newR)}${toHex(newG)}${toHex(newB)}`;
}

async function loadSVG(templatePath: string): Promise<string> {
  try {
    const response = await fetch(templatePath);
    if (!response.ok) {
      throw new Error(`Failed to load template: ${response.statusText}`);
    }
    return await response.text();
  } catch (error) {
    console.error("Error loading SVG template:", error);
    throw error;
  }
}

/**
 * Loads an image template (PNG/JPEG) and returns a Promise that resolves to an Image
 */
async function loadImageTemplate(
  templatePath: string
): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();

    img.onload = () => {
      resolve(img);
    };

    img.onerror = error => {
      console.error("Error loading image template:", error);
      reject(new Error(`Failed to load image template: ${templatePath}`));
    };

    img.src = templatePath;
  });
}

function transformSVGColors(
  svgString: string,
  templateType: TemplateType,
  palette: ColorPalette
): string {
  let transformedSVG = svgString;

  if (templateType === TemplateType.GENERAL_CROSS_PATTERN) {
    transformedSVG = transformedSVG.replace(
      /<g id="Artboard"[^>]*>/,
      `<g id="Artboard" stroke="none" stroke-width="1" fill="none" fill-rule="evenodd">
       <rect width="100%" height="100%" fill="#FFFFFF"/>`
    );

    transformedSVG = transformedSVG.replace(
      /fill="#000000"/g,
      'fill="#E6E7EB"'
    );

    let colorReplacements = 0;
    transformedSVG = transformedSVG.replace(
      /fill="#([a-fA-F0-9]{6})"/g,
      (match, colorHex) => {
        const hex = colorHex.toLowerCase();

        // Don't replace white/light gray backgrounds
        if (hex === "e6e7eb" || hex === "ffffff" || hex === "f9fafb") {
          return match;
        }

        const r = parseInt(hex.substr(0, 2), 16);
        const g = parseInt(hex.substr(2, 2), 16);
        const b = parseInt(hex.substr(4, 2), 16);

        let newColor: string;

        // Yellow/bright colors -> primary color
        if (r > 180 && g > 140 && b < 120) {
          newColor = palette.primary;
        }
        // Dark colors -> secondary color
        else if (r < 120 && g < 120 && b < 120) {
          newColor = palette.secondary;
        }
        // Bright colors -> primary
        else {
          const brightness = (r + g + b) / 3;
          newColor = brightness > 150 ? palette.primary : palette.secondary;
        }

        colorReplacements++;
        return `fill="${newColor}"`;
      }
    );
  } else if (templateType === TemplateType.GENERAL_GRID_PATTERN) {
    transformedSVG = transformedSVG.replace(
      /<g style="mix-blend-mode:soft-light"/,
      `<rect width="100%" height="100%" fill="#E6E7EB"/>
       <g style="mix-blend-mode:normal"`
    );

    const gradientId = "customRadialGradient";
    const newGradient = `<radialGradient id="${gradientId}" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(1073.45 488) rotate(90) scale(488 1073.6)">
      <stop stop-color="${palette.primary}" stop-opacity="0.9"/>
      <stop offset="0.6" stop-color="${palette.primary}" stop-opacity="0.4"/>
      <stop offset="1" stop-color="#FFFFFF" stop-opacity="0.1"/>
    </radialGradient>`;

    transformedSVG = transformedSVG.replace(
      /<radialGradient id="paint0_radial_77_304"[^>]*>[\s\S]*?<\/radialGradient>/,
      newGradient
    );

    transformedSVG = transformedSVG.replace(
      /stroke="url\(#paint0_radial_77_304\)"/g,
      `stroke="url(#${gradientId})"`
    );

    transformedSVG = transformedSVG.replace(/opacity="0\.7"/g, 'opacity="1"');
    transformedSVG = transformedSVG.replace(
      /stroke-opacity="0\.61"/g,
      'stroke-opacity="0.9"'
    );
    transformedSVG = transformedSVG.replace(
      /stroke-width="0\.805493"/g,
      'stroke-width="2"'
    );
    transformedSVG = transformedSVG.replace(
      /mix-blend-mode:soft-light/g,
      "mix-blend-mode:normal"
    );
  } else if (templateType === TemplateType.GENERAL_BORDER_PATTERN) {
    transformedSVG = transformedSVG.replace(
      /<stop stop-color="#45B549" offset="100%"><\/stop>/g,
      `<stop stop-color="${palette.primary}" offset="100%"></stop>`
    );

    // Create a lighter version of the primary color for the inner rectangle
    const lightPrimaryColor = lightenColor(palette.primary, 0.9);
    transformedSVG = transformedSVG.replace(
      /fill="#F4F9F4"/g,
      `fill="${lightPrimaryColor}"`
    );
  }

  return transformedSVG;
}

export async function renderTemplateToCanvas(
  ctx: CanvasRenderingContext2D,
  templateType: TemplateType,
  businessProfile: BusinessProfile,
  width: number = 1080,
  height: number = 1080
): Promise<void> {
  try {
    const templateMap: Record<TemplateType, string> = {
      // General Templates (SVG)
      [TemplateType.GENERAL_CROSS_PATTERN]: "/images/Template-1.svg",
      [TemplateType.GENERAL_GRID_PATTERN]: "/images/Template-2.svg",
      [TemplateType.GENERAL_BORDER_PATTERN]: "/images/Template-3.svg",

      // Miraai Recycling Specific Templates (Images)
      [TemplateType.MIRAAI_MODERN_IMAGE]: "/images/Template-4.jpeg",
      [TemplateType.MIRAAI_CREATIVE_IMAGE]: "/images/Template-5.png",
      [TemplateType.MIRAAI_STYLISH_IMAGE]: "/images/Template-6.png",

      // Tailwind Specific Templates (Images)
      [TemplateType.TAILWIND_MODERN_IMAGE]: "/images/Template-7.png",
    };

    const templatePath = templateMap[templateType];
    if (!templatePath) {
      console.warn(`Unknown template type: ${templateType}`);
      return;
    }

    if (isImageTemplate(templateType)) {
      const img = await loadImageTemplate(templatePath);

      const imgAspectRatio = img.width / img.height;
      const drawWidth = width;
      const drawHeight = width / imgAspectRatio;
      const drawX = 0;
      const drawY = 0;

      if (drawHeight > height) {
        ctx.canvas.height = drawHeight;
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = "high";
      }

      ctx.save();
      ctx.drawImage(img, drawX, drawY, drawWidth, drawHeight);
      ctx.restore();
      return;
    }

    const svgString = await loadSVG(templatePath);

    const palette: ColorPalette = {
      primary: businessProfile.colorPalette?.primary || "#44B549",
      secondary: businessProfile.colorPalette?.secondary || "#3F3F3F",
      accent: businessProfile.colorPalette?.accent,
      background: businessProfile.colorPalette?.background,
    };

    const transformedSVG = transformSVGColors(svgString, templateType, palette);

    const svgBlob = new Blob([transformedSVG], { type: "image/svg+xml" });
    const url = URL.createObjectURL(svgBlob);

    return new Promise((resolve, reject) => {
      const img = new Image();

      img.onload = () => {
        const svgAspectRatio = img.width / img.height;

        const drawWidth = width;
        const drawHeight = width / svgAspectRatio;
        const drawX = 0;
        const drawY = 0;

        if (drawHeight > height) {
          ctx.canvas.height = drawHeight;
          ctx.imageSmoothingEnabled = true;
          ctx.imageSmoothingQuality = "high";
        }

        ctx.save();
        ctx.drawImage(img, drawX, drawY, drawWidth, drawHeight);
        ctx.restore();

        URL.revokeObjectURL(url);
        resolve();
      };

      img.onerror = error => {
        console.error("Error loading SVG as image:", error);
        URL.revokeObjectURL(url);
        reject(error);
      };

      img.src = url;
    });
  } catch (error) {
    console.error("Error rendering template to canvas:", error);
    throw error;
  }
}
