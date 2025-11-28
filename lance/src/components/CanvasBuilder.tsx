"use client";

import { useState, useRef, useEffect } from "react";
import "./CanvasBuilder.css";
import { Shape, ColorPalette } from "@/types/Canvas";
import { drawCanvas } from "@/utils/canvasDrawer";
import { generateTemplate } from "@/utils/templateGenerator";

interface CanvasBuilderProps {
  width?: number;
  height?: number;
}

export default function CanvasBuilder({
  width = 1080,
  height = 1080,
}: CanvasBuilderProps) {
  const defaultColorPalette: ColorPalette = {
    primary: "#FCD34D",
    secondary: "#6B7280",
    accent: "#4B5563",
    background: "#374151",
    text: "#9CA3AF",
  };

  const [shapes, setShapes] = useState<Shape[]>(() =>
    generateTemplate(width, height, defaultColorPalette)
  );
  const [selectedShape, setSelectedShape] = useState<string | null>(null);
  const [colorPalette, setColorPalette] =
    useState<ColorPalette>(defaultColorPalette);

  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    drawCanvas(canvas, shapes, selectedShape, colorPalette, width, height);
  }, [shapes, selectedShape, colorPalette, width, height]);

  const handleCanvasClick = () => {
    setSelectedShape(null);
  };

  const handleGenerateTemplate = () => {
    const templateShapes = generateTemplate(width, height, colorPalette);
    setShapes(templateShapes);
    setSelectedShape(null);
  };

  const handleClearCanvas = () => {
    setShapes([]);
    setSelectedShape(null);
  };

  const handleExportCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const link = document.createElement("a");
    link.download = `canvas-template-${Date.now()}.png`;
    link.href = canvas.toDataURL();
    link.click();
  };

  return (
    <div className="canvas-builder">
      <div className="canvas-builder-header">
        <h2>Geometric Template Builder</h2>
        <p>
          Generate the specific geometric template with customizable colors.
          Perfect base for adding text, logos, and illustrations later.
        </p>
      </div>

      <div className="canvas-builder-content">
        <div className="canvas-toolbar">
          <div className="toolbar-section">
            <h4>Template Color Palette</h4>
            <p className="color-description">
              Customize the colors for your geometric template. Changes apply to
              all elements.
            </p>
            <div className="color-palette">
              <div className="color-item">
                <label>Corner Triangles</label>
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
                  <div
                    className="color-preview"
                    style={{ backgroundColor: colorPalette.primary }}
                  ></div>
                </div>
              </div>
              <div className="color-item">
                <label>Light Crosses</label>
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
                  <div
                    className="color-preview"
                    style={{ backgroundColor: colorPalette.secondary }}
                  ></div>
                </div>
              </div>
              <div className="color-item">
                <label>Dark Crosses</label>
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
                  <div
                    className="color-preview"
                    style={{ backgroundColor: colorPalette.accent }}
                  ></div>
                </div>
              </div>
              <div className="color-item">
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
                  <div
                    className="color-preview"
                    style={{ backgroundColor: colorPalette.background }}
                  ></div>
                </div>
              </div>
              <div className="color-item">
                <label>Text (for future use)</label>
                <div className="color-input-group">
                  <input
                    type="color"
                    value={colorPalette.text}
                    onChange={e =>
                      setColorPalette(prev => ({
                        ...prev,
                        text: e.target.value,
                      }))
                    }
                  />
                  <div
                    className="color-preview"
                    style={{ backgroundColor: colorPalette.text }}
                  ></div>
                </div>
              </div>
            </div>
          </div>

          <div className="toolbar-section">
            <h4>Template Actions</h4>
            <div className="action-buttons">
              <button onClick={handleGenerateTemplate} className="generate-btn">
                Generate Geometric Template
              </button>
              <button onClick={handleClearCanvas} className="clear-btn">
                Clear Canvas
              </button>
              <button onClick={handleExportCanvas} className="export-btn">
                Export Template as PNG
              </button>
            </div>
            <p className="action-description">
              Generate the template with your custom colors, then export it for
              use with text and logos.
            </p>
          </div>
        </div>

        <div className="canvas-container">
          <canvas
            ref={canvasRef}
            width={width}
            height={height}
            onClick={handleCanvasClick}
            className="main-canvas"
          />
        </div>

        <div className="info-panel">
          <h4>Template Information</h4>
          <div className="info-item">
            <label>Canvas Size:</label>
            <span>
              {width} × {height} pixels
            </span>
          </div>
          <div className="info-item">
            <label>Template Elements:</label>
            <span>{shapes.length} shapes</span>
          </div>
          <div className="info-item">
            <label>Corner Triangles:</label>
            <span style={{ color: colorPalette.primary }}>●</span>{" "}
            {colorPalette.primary}
          </div>
          <div className="info-item">
            <label>Cross Elements:</label>
            <span style={{ color: colorPalette.secondary }}>●</span>{" "}
            {colorPalette.secondary} /
            <span style={{ color: colorPalette.accent }}>●</span>{" "}
            {colorPalette.accent}
          </div>
          <div className="info-item">
            <label>Background:</label>
            <span style={{ color: colorPalette.background }}>●</span>{" "}
            {colorPalette.background}
          </div>
          <div className="template-preview-info">
            <h5>Usage Instructions:</h5>
            <ul>
              <li>Generate template with your colors</li>
              <li>Export as PNG for external use</li>
              <li>Add text, logos, and illustrations as needed</li>
              <li>Perfect for social media, presentations, and branding</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
