import { useCallback } from "react";
import { FontLoadStatus } from "../types/Layout";

/**
 * Load local fonts that are already defined in CSS
 */
async function loadLocalFont(family: string): Promise<FontLoadStatus> {
  try {
    if (document.fonts.check(`16px "${family}"`)) {
      return { family, loaded: true };
    }

    await document.fonts.ready;

    await new Promise(resolve => setTimeout(resolve, 100));

    if (document.fonts.check(`16px "${family}"`)) {
      return { family, loaded: true };
    }

    return { family, loaded: true };
  } catch (error) {
    console.warn(`Failed to load local font ${family}:`, error);
    return {
      family,
      loaded: false,
      error: error instanceof Error ? error.message : "Unknown error",
    };
  }
}

/**
 * Load Google Fonts by fetching the CSS and parsing font URLs
 */
async function loadGoogleFont(family: string): Promise<FontLoadStatus> {
  try {
    if (document.fonts.check(`16px "${family}"`)) {
      return { family, loaded: true };
    }

    const fontName = family.replace(/\s+/g, "+");
    const cssUrl = `https://fonts.googleapis.com/css2?family=${fontName}:wght@400;500;600;700;800&display=swap`;

    const response = await fetch(cssUrl);
    if (!response.ok) {
      throw new Error(`Failed to fetch font CSS: ${response.statusText}`);
    }

    const cssText = await response.text();

    const fontFaceRegex = /@font-face\s*\{([^}]+)\}/g;
    const fontFaces: FontFace[] = [];
    let blockMatch;

    while ((blockMatch = fontFaceRegex.exec(cssText)) !== null) {
      const blockContent = blockMatch[1];

      const srcMatch = blockContent.match(/src:\s*url\(([^)]+)\)/i);
      if (!srcMatch) continue;

      let url = srcMatch[1].replace(/['"]/g, "");
      if (url.startsWith("http")) {
      } else if (url.startsWith("//")) {
        url = `https:${url}`;
      } else {
        url = `https://fonts.gstatic.com${url}`;
      }

      const weightMatch = blockContent.match(/font-weight:\s*(\d+)/i);
      const weight = weightMatch ? weightMatch[1] : "400";

      const styleMatch = blockContent.match(/font-style:\s*(\w+)/i);
      const style = styleMatch ? styleMatch[1] : "normal";

      try {
        const descriptors: FontFaceDescriptors = {};
        if (weight) {
          descriptors.weight = weight;
        }
        if (
          style &&
          (style === "normal" || style === "italic" || style === "oblique")
        ) {
          descriptors.style = style;
        }

        const fontFace = new FontFace(family, `url(${url})`, descriptors);
        await fontFace.load();
        document.fonts.add(fontFace);
        fontFaces.push(fontFace);
      } catch (err) {
        console.warn(`Failed to load font variant from ${url}:`, err);
      }
    }

    if (fontFaces.length === 0) {
      throw new Error(`No font variants loaded for ${family}`);
    }
    return { family, loaded: true };
  } catch (error) {
    console.warn(`Failed to load Google Font ${family}:`, error);

    // Special handling for Aleo font - ensure it's available
    if (family === "Aleo") {
      console.warn(
        `[Font Loader] Aleo font failed to load, will use serif fallback`
      );
    }

    return {
      family,
      loaded: false,
      error: error instanceof Error ? error.message : "Unknown error",
    };
  }
}

/**
 * List of fonts that are loaded locally via CSS @font-face
 */
const LOCAL_FONTS = ["Optika", "Neue Montreal Medium", "Neue Montreal Regular"];

export const useFontLoader = () => {
  const loadFonts = useCallback(
    async (fontFamilies: string[]): Promise<FontLoadStatus[]> => {
      const results: FontLoadStatus[] = [];

      const loadPromises = fontFamilies.map(family => {
        // Check if this is a local font
        if (LOCAL_FONTS.includes(family)) {
          return loadLocalFont(family);
        } else {
          // Load as Google Font
          return loadGoogleFont(family);
        }
      });

      const loadedResults = await Promise.all(loadPromises);
      results.push(...loadedResults);

      return results;
    },
    []
  );

  return { loadFonts };
};
