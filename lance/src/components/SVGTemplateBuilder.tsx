"use client";

import { useState, useRef, useEffect, useCallback, useMemo } from "react";
import "./SVGTemplateBuilder.css";
import { TemplateType, getTemplatesForBusiness } from "../config/templates";

export interface ColorPalette {
  primary: string;
  secondary: string;
  accent: string;
  background: string;
}

interface Template {
  id: string;
  name: string;
  description: string;
  file: string;
}

interface SVGTemplateBuilderProps {
  width?: number;
  height?: number;
}

const lightenColor = (color: string, amount: number = 0.2): string => {
  const hex = color.replace("#", "");
  const r = parseInt(hex.substr(0, 2), 16);
  const g = parseInt(hex.substr(2, 2), 16);
  const b = parseInt(hex.substr(4, 2), 16);

  const newR = Math.min(255, Math.floor(r + (255 - r) * amount));
  const newG = Math.min(255, Math.floor(g + (255 - g) * amount));
  const newB = Math.min(255, Math.floor(b + (255 - b) * amount));

  return `#${newR.toString(16).padStart(2, "0")}${newG.toString(16).padStart(2, "0")}${newB.toString(16).padStart(2, "0")}`;
};

const darkenColor = (color: string, amount: number = 0.2): string => {
  const hex = color.replace("#", "");
  const r = parseInt(hex.substr(0, 2), 16);
  const g = parseInt(hex.substr(2, 2), 16);
  const b = parseInt(hex.substr(4, 2), 16);

  const newR = Math.max(0, Math.floor(r * (1 - amount)));
  const newG = Math.max(0, Math.floor(g * (1 - amount)));
  const newB = Math.max(0, Math.floor(b * (1 - amount)));

  return `#${newR.toString(16).padStart(2, "0")}${newG.toString(16).padStart(2, "0")}${newB.toString(16).padStart(2, "0")}`;
};

export default function SVGTemplateBuilder({
  width = 800,
  height = 600,
}: SVGTemplateBuilderProps) {
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateType>(
    TemplateType.GENERAL_CROSS_PATTERN
  );
  const [colorPalette, setColorPalette] = useState<ColorPalette>({
    primary: "#3B82F6",
    secondary: "#10B981",
    accent: "#F59E0B",
    background: "#F3F4F6",
  });

  const [svgContent, setSvgContent] = useState<string>("");
  const [isLoading, setIsLoading] = useState(true);

  const svgRef = useRef<HTMLDivElement>(null);

  const templates: Template[] = useMemo(
    () =>
      getTemplatesForBusiness()
        .filter(t => t.colorConfig.category === "svg")
        .map(t => ({
          id: t.id,
          name: t.name,
          description: t.description || "",
          file: `/images/${t.id}.svg`,
        })),
    []
  );

  const generateExtendedPalette = useCallback(
    (palette: ColorPalette) => {
      if (selectedTemplate === TemplateType.GENERAL_CROSS_PATTERN) {
        return {
          primary: palette.primary,
          primaryLight: lightenColor(palette.primary, 0.2),
          primaryDark: darkenColor(palette.primary, 0.2),
          secondary: palette.secondary,
          secondaryLight: lightenColor(palette.secondary, 0.3),
          secondaryDark: darkenColor(palette.secondary, 0.3),
          secondaryExtraLight: lightenColor(palette.secondary, 0.5),
          background: "#FFFFFF",
          accent: lightenColor(palette.secondary, 0.2),
          accentLight: lightenColor(palette.secondary, 0.4),
          accentDark: darkenColor(palette.secondary, 0.1),
          backgroundLight: "#FFFFFF",
          backgroundDark: "#F8F9FA",
        };
      } else if (selectedTemplate === TemplateType.GENERAL_GRID_PATTERN) {
        return {
          primary: palette.primary,
          primaryLight: lightenColor(palette.primary, 0.2),
          primaryDark: darkenColor(palette.primary, 0.2),
          secondary: palette.secondary,
          secondaryLight: lightenColor(palette.secondary, 0.4),
          secondaryDark: darkenColor(palette.secondary, 0.3),
          background: "#FFF",
          backgroundLight: "#fff",
          backgroundDark: "#DADCE0",
          accent: palette.primary,
          accentLight: lightenColor(palette.primary, 0.3),
          accentDark: darkenColor(palette.primary, 0.3),
        };
      } else {
        return {
          primary: palette.primary,
          primaryLight: lightenColor(palette.primary, 0.3),
          primaryDark: darkenColor(palette.primary, 0.3),
          secondary: palette.secondary,
          secondaryLight: lightenColor(palette.secondary, 0.3),
          secondaryDark: darkenColor(palette.secondary, 0.3),
          accent: palette.accent,
          accentLight: lightenColor(palette.accent, 0.3),
          accentDark: darkenColor(palette.accent, 0.3),
          background: palette.background,
          backgroundLight: lightenColor(palette.background, 0.1),
          backgroundDark: darkenColor(palette.background, 0.1),
        };
      }
    },
    [selectedTemplate]
  );

  const transformSVGColors = useCallback(
    (svgString: string, palette: ColorPalette): string => {
      let transformedSVG = svgString;

      if (selectedTemplate === TemplateType.GENERAL_CROSS_PATTERN) {
        transformedSVG = transformedSVG.replace(
          /<g id="Artboard"[^>]*>/,
          `<g id="Artboard" stroke="none" stroke-width="1" fill="none" fill-rule="evenodd">
         <rect width="100%" height="100%" fill="#FFFFFF"/>`
        );

        transformedSVG = transformedSVG.replace(
          /fill="#000000"/g,
          'fill="#E6E7EB"'
        );

        transformedSVG = transformedSVG.replace(
          /fill="#([a-fA-F0-9]{6})"/g,
          (match, colorHex) => {
            const hex = colorHex.toLowerCase();

            if (hex === "e6e7eb" || hex === "ffffff") {
              return match;
            }

            const r = parseInt(hex.substr(0, 2), 16);
            const g = parseInt(hex.substr(2, 2), 16);
            const b = parseInt(hex.substr(4, 2), 16);

            if (r > 180 && g > 140 && b < 120) {
              return `fill="${palette.primary}"`;
            } else if (r < 120 && g < 120 && b < 120) {
              return `fill="${palette.secondary}"`;
            }

            const brightness = (r + g + b) / 3;
            if (brightness > 150) {
              return `fill="${palette.primary}"`;
            } else {
              return `fill="${palette.secondary}"`;
            }
          }
        );
      } else if (selectedTemplate === TemplateType.GENERAL_GRID_PATTERN) {
        const extendedPalette = generateExtendedPalette(palette);

        transformedSVG = transformedSVG.replace(
          /<g style="mix-blend-mode:soft-light"/,
          `<rect width="100%" height="100%" fill="${extendedPalette.background}"/>
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

        transformedSVG = transformedSVG.replace(
          /opacity="0\.7"/g,
          'opacity="1"'
        );
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
      }

      return transformedSVG;
    },
    [selectedTemplate, generateExtendedPalette]
  );

  const loadTemplate = useCallback(
    async (templateId: string) => {
      setIsLoading(true);
      const template = templates.find(t => t.id === templateId);
      if (!template) return;

      try {
        const response = await fetch(template.file);
        if (!response.ok) throw new Error("Failed to load template");

        const svgText = await response.text();
        const transformedSVG = transformSVGColors(svgText, colorPalette);
        setSvgContent(transformedSVG);
      } catch (error) {
        console.error("Error loading template:", error);
        setSvgContent(
          `<svg><text x="50" y="50" fill="red">Error loading template</text></svg>`
        );
      } finally {
        setIsLoading(false);
      }
    },
    [colorPalette, templates, transformSVGColors]
  );

  useEffect(() => {
    loadTemplate(selectedTemplate);
  }, [selectedTemplate, colorPalette, loadTemplate]);

  const exportSVG = () => {
    if (!svgContent) return;

    const blob = new Blob([svgContent], { type: "image/svg+xml" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${selectedTemplate}-${Date.now()}.svg`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const exportPNG = () => {
    if (!svgContent || !svgRef.current) return;

    const svg = svgRef.current.querySelector("svg");
    if (!svg) return;

    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const img = new Image();
    const svgBlob = new Blob([svgContent], {
      type: "image/svg+xml;charset=utf-8",
    });
    const url = URL.createObjectURL(svgBlob);

    img.onload = () => {
      canvas.width = width;
      canvas.height = height;
      ctx.drawImage(img, 0, 0, width, height);

      canvas.toBlob(blob => {
        if (blob) {
          const link = document.createElement("a");
          link.href = URL.createObjectURL(blob);
          link.download = `${selectedTemplate}-${Date.now()}.png`;
          link.click();
          URL.revokeObjectURL(link.href);
        }
      }, "image/png");

      URL.revokeObjectURL(url);
    };

    img.src = url;
  };

  const currentTemplate = templates.find(t => t.id === selectedTemplate);

  return (
    <div className="svg-template-builder">
      <div className="template-builder-header">
        <h2>SVG Template Builder</h2>
        <p>
          Choose a template and customize colors. Additional shades are
          automatically generated from your 4-color palette.
        </p>
      </div>

      <div className="template-builder-content">
        <div className="controls-panel">
          <div className="control-section">
            <h4>Template Selection</h4>
            <select
              value={selectedTemplate}
              onChange={e =>
                setSelectedTemplate(e.target.value as TemplateType)
              }
              className="template-dropdown"
            >
              {templates.map(template => (
                <option key={template.id} value={template.id}>
                  {template.name}
                </option>
              ))}
            </select>
            {currentTemplate && (
              <p className="template-description">
                {currentTemplate.description}
              </p>
            )}
          </div>

          <div className="control-section">
            <h4>
              {selectedTemplate === TemplateType.GENERAL_CROSS_PATTERN ||
              selectedTemplate === TemplateType.GENERAL_GRID_PATTERN
                ? "2-Color Palette"
                : "4-Color Palette"}
            </h4>
            <p className="palette-description">
              {selectedTemplate === TemplateType.GENERAL_CROSS_PATTERN
                ? "Cross Pattern: Primary color for yellow shapes, Secondary color for dark shapes. Background is fixed white."
                : selectedTemplate === TemplateType.GENERAL_GRID_PATTERN
                  ? "Grid Pattern: Primary color for grid lines (with gradient to white), Secondary color for background (fixed light gray)."
                  : "Set your base colors. Lighter and darker variants are auto-generated for the template."}
            </p>
            <div className="color-controls">
              <div className="color-control">
                <label>
                  Primary{" "}
                  {selectedTemplate === TemplateType.GENERAL_CROSS_PATTERN
                    ? "(Yellow Shapes)"
                    : selectedTemplate === TemplateType.GENERAL_GRID_PATTERN
                      ? "(Grid Lines)"
                      : ""}
                </label>
                <div className="color-input-group">
                  <input
                    type="color"
                    value={colorPalette.primary}
                    onChange={e =>
                      setColorPalette(prev => ({
                        ...prev,
                        primary: e.target.value,
                      }))
                    }
                  />
                  <span className="color-value">{colorPalette.primary}</span>
                </div>
              </div>

              <div className="color-control">
                <label>
                  Secondary{" "}
                  {selectedTemplate === TemplateType.GENERAL_CROSS_PATTERN
                    ? "(Dark Shapes)"
                    : selectedTemplate === TemplateType.GENERAL_GRID_PATTERN
                      ? "(Background Base)"
                      : ""}
                </label>
                <div className="color-input-group">
                  <input
                    type="color"
                    value={colorPalette.secondary}
                    onChange={e =>
                      setColorPalette(prev => ({
                        ...prev,
                        secondary: e.target.value,
                      }))
                    }
                  />
                  <span className="color-value">{colorPalette.secondary}</span>
                </div>
              </div>

              {selectedTemplate !== TemplateType.GENERAL_CROSS_PATTERN &&
                selectedTemplate !== TemplateType.GENERAL_GRID_PATTERN && (
                  <>
                    <div className="color-control">
                      <label>Accent</label>
                      <div className="color-input-group">
                        <input
                          type="color"
                          value={colorPalette.accent}
                          onChange={e =>
                            setColorPalette(prev => ({
                              ...prev,
                              accent: e.target.value,
                            }))
                          }
                        />
                        <span className="color-value">
                          {colorPalette.accent}
                        </span>
                      </div>
                    </div>

                    <div className="color-control">
                      <label>Background</label>
                      <div className="color-input-group">
                        <input
                          type="color"
                          value={colorPalette.background}
                          onChange={e =>
                            setColorPalette(prev => ({
                              ...prev,
                              background: e.target.value,
                            }))
                          }
                        />
                        <span className="color-value">
                          {colorPalette.background}
                        </span>
                      </div>
                    </div>
                  </>
                )}
            </div>
          </div>

          <div className="control-section">
            <h4>Generated Color Variations</h4>
            <div className="generated-colors">
              {Object.entries(generateExtendedPalette(colorPalette)).map(
                ([key, color]) => (
                  <div key={key} className="generated-color">
                    <div
                      className="color-swatch"
                      style={{ backgroundColor: color }}
                    ></div>
                    <span className="color-name">{key}</span>
                    <span className="color-hex">{color}</span>
                  </div>
                )
              )}
            </div>
          </div>

          <div className="control-section">
            <h4>Export</h4>
            <div className="export-buttons">
              <button onClick={exportSVG} className="export-btn svg-btn">
                Export SVG
              </button>
              <button onClick={exportPNG} className="export-btn png-btn">
                Export PNG
              </button>
            </div>
            <p className="export-description">
              Export your customized template for use in design tools or web
              projects.
            </p>
          </div>
        </div>

        <div className="svg-preview-container">
          <div className="svg-preview-header">
            <h4>Preview: {currentTemplate?.name}</h4>
            {isLoading && <span className="loading-indicator">Loading...</span>}
          </div>

          <div ref={svgRef} className="svg-preview" style={{ width, height }}>
            {isLoading ? (
              <div className="loading-placeholder">
                <div className="loading-spinner"></div>
                <p>Loading template...</p>
              </div>
            ) : (
              <div
                dangerouslySetInnerHTML={{ __html: svgContent }}
                className="svg-content"
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
