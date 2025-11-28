// Basic text wrapping without height tracking
export const wrapText = (
  ctx: CanvasRenderingContext2D,
  text: string,
  x: number,
  y: number,
  maxWidth: number,
  lineHeight: number
): number => {
  const words = text.split(" ");
  let line = "";
  let currentY = y;
  let lines = 0;

  for (let n = 0; n < words.length; n++) {
    const testLine = line + words[n] + " ";
    const testWidth = ctx.measureText(testLine).width;

    if (testWidth > maxWidth && n > 0) {
      ctx.fillText(line.trim(), x, currentY);
      line = words[n] + " ";
      currentY += lineHeight;
      lines++;
    } else {
      line = testLine;
    }
  }

  if (line.trim()) {
    ctx.fillText(line.trim(), x, currentY);
    lines++;
  }

  return lines;
};

// Center-aligned text wrapping without height tracking
export const centerWrapText = (
  ctx: CanvasRenderingContext2D,
  text: string,
  centerX: number,
  y: number,
  maxWidth: number,
  lineHeight: number
): number => {
  const words = text.split(" ");
  let line = "";
  let currentY = y;
  let lines = 0;

  for (let n = 0; n < words.length; n++) {
    const testLine = line + words[n] + " ";
    const testWidth = ctx.measureText(testLine).width;

    if (testWidth > maxWidth && n > 0) {
      ctx.textAlign = "center";
      ctx.fillText(line.trim(), centerX, currentY);
      line = words[n] + " ";
      currentY += lineHeight;
      lines++;
    } else {
      line = testLine;
    }
  }

  if (line.trim()) {
    ctx.textAlign = "center";
    ctx.fillText(line.trim(), centerX, currentY);
    lines++;
  }

  return lines;
};

// Calculate text height without rendering
export const calculateTextHeight = (
  ctx: CanvasRenderingContext2D,
  text: string,
  maxWidth: number,
  lineHeight: number
): number => {
  const words = text.split(" ");
  let line = "";
  let lines = 0;

  for (let n = 0; n < words.length; n++) {
    const testLine = line + words[n] + " ";
    const testWidth = ctx.measureText(testLine).width;

    if (testWidth > maxWidth && n > 0) {
      line = words[n] + " ";
      lines++;
    } else {
      line = testLine;
    }
  }

  if (line.trim()) {
    lines++;
  }

  return lines * lineHeight;
};

// Enhanced wrap text functions that return actual height
export const wrapTextWithHeight = (
  ctx: CanvasRenderingContext2D,
  text: string,
  x: number,
  y: number,
  maxWidth: number,
  lineHeight: number
): number => {
  const words = text.split(" ");
  let line = "";
  let currentY = y;
  let lines = 0;

  for (let n = 0; n < words.length; n++) {
    const testLine = line + words[n] + " ";
    const testWidth = ctx.measureText(testLine).width;

    if (testWidth > maxWidth && n > 0) {
      ctx.fillText(line.trim(), x, currentY);
      line = words[n] + " ";
      currentY += lineHeight;
      lines++;
    } else {
      line = testLine;
    }
  }

  if (line.trim()) {
    ctx.fillText(line.trim(), x, currentY);
    lines++;
  }

  return lines * lineHeight;
};

export const centerWrapTextWithHeight = (
  ctx: CanvasRenderingContext2D,
  text: string,
  centerX: number,
  y: number,
  maxWidth: number,
  lineHeight: number
): number => {
  const words = text.split(" ");
  let line = "";
  let currentY = y;
  let lines = 0;

  for (let n = 0; n < words.length; n++) {
    const testLine = line + words[n] + " ";
    const testWidth = ctx.measureText(testLine).width;

    if (testWidth > maxWidth && n > 0) {
      ctx.textAlign = "center";
      ctx.fillText(line.trim(), centerX, currentY);
      line = words[n] + " ";
      currentY += lineHeight;
      lines++;
    } else {
      line = testLine;
    }
  }

  if (line.trim()) {
    ctx.textAlign = "center";
    ctx.fillText(line.trim(), centerX, currentY);
    lines++;
  }

  return lines * lineHeight;
};

/**
 * Prepare font string for canvas context
 * Handles font family fallbacks and quoting
 */
export const prepareFontString = (
  fontWeight: string,
  fontSize: number,
  fontFamily: string
): string => {
  // Quote individual font families that contain spaces
  const quoteIfNeeded = (name: string): string => {
    if (name.includes(" ")) {
      return `"${name}"`;
    }
    return name;
  };

  // Add proper font fallbacks for better font rendering
  let fontWithFallback: string;
  if (fontFamily === "Aleo") {
    fontWithFallback = `${quoteIfNeeded(fontFamily)}, "Times New Roman", serif`;
  } else if (fontFamily === "Optika") {
    fontWithFallback = `${quoteIfNeeded(fontFamily)}, "Helvetica Neue", "Arial", sans-serif`;
  } else if (fontFamily.includes("serif") || fontFamily === "Times") {
    fontWithFallback = `${quoteIfNeeded(fontFamily)}, serif`;
  } else {
    fontWithFallback = `${quoteIfNeeded(fontFamily)}, sans-serif`;
  }

  return `${fontWeight} ${fontSize}px ${fontWithFallback}`;
};

/**
 * Get font size based on component type
 */
export const getFontSizeByComponentType = (componentType?: string): number => {
  switch (componentType) {
    case "headerText":
      return 72; // Large size for main headers/slogans
    case "specialBannerText":
      return 48; // Medium-large size for special banners
    case "bodyText":
    default:
      return 40; // Default size for body text
  }
};

/**
 * Render special banner text with background color and border radius
 * Now supports multi-line text in a single unified banner
 */
export const renderSpecialBannerText = (
  ctx: CanvasRenderingContext2D,
  text: string,
  x: number,
  y: number,
  fontSize: number,
  textColor: string,
  primaryColor: string,
  maxWidth: number,
  fontFamily: string = "Arial, sans-serif"
): void => {
  // Set font for measurement using the correct font family
  ctx.font = prepareFontString("bold", fontSize, fontFamily);

  // Split text into lines that fit within maxWidth
  const words = text.split(" ");
  const lines: string[] = [];
  let currentLine = "";

  const bannerPadding = 60; // Total horizontal padding (30px each side)
  const availableWidth = maxWidth - bannerPadding;

  for (const word of words) {
    const testLine = currentLine ? `${currentLine} ${word}` : word;
    const testWidth = ctx.measureText(testLine).width;

    if (testWidth <= availableWidth) {
      currentLine = testLine;
    } else {
      if (currentLine) lines.push(currentLine);
      currentLine = word;
    }
  }
  if (currentLine) lines.push(currentLine);

  // Calculate banner dimensions for all lines
  const lineHeight = fontSize * 1.2;
  const paddingX = 30;
  const paddingY = 20;

  // Find the widest line
  const maxLineWidth = Math.max(
    ...lines.map(line => ctx.measureText(line).width)
  );
  const bannerWidth = Math.min(maxLineWidth + paddingX * 2, maxWidth);
  const totalTextHeight = lines.length * lineHeight;
  const bannerHeight = totalTextHeight + paddingY * 2;

  // Calculate banner position - center around the y position
  const bannerX = x - bannerWidth / 2;
  const bannerY = y - bannerHeight / 2;

  // Draw unified banner background
  const borderRadius = 25;
  ctx.fillStyle = primaryColor;
  ctx.beginPath();
  ctx.roundRect(bannerX, bannerY, bannerWidth, bannerHeight, borderRadius);
  ctx.fill();

  // Draw each line of text centered in the unified banner
  ctx.fillStyle = "#FFFFFF";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";

  // Start from the top of the text area within the banner
  const textStartY = bannerY + paddingY + lineHeight / 2;
  lines.forEach((line, index) => {
    const lineY = textStartY + index * lineHeight;
    ctx.fillText(line, x, lineY);
  });

  // Only show debug visuals when explicitly debugging
  const DEBUG_VISUALS = false; // Set to true when debugging spacing issues
  if (DEBUG_VISUALS && typeof window !== "undefined") {
    // Draw banner outline in red
    ctx.strokeStyle = "rgba(255, 0, 0, 0.7)";
    ctx.lineWidth = 2;
    ctx.strokeRect(bannerX, bannerY, bannerWidth, bannerHeight);

    // Draw center line in green
    ctx.strokeStyle = "rgba(0, 255, 0, 0.8)";
    ctx.beginPath();
    ctx.moveTo(bannerX, y);
    ctx.lineTo(bannerX + bannerWidth, y);
    ctx.stroke();
  }
};

/**
 * Render a single line banner (for visual appeal)
 */
export const renderSingleLineBanner = (
  ctx: CanvasRenderingContext2D,
  text: string,
  x: number,
  y: number,
  fontSize: number,
  primaryColor: string,
  maxWidth: number,
  fontFamily: string = "Arial, sans-serif"
): void => {
  // Set font for measurement
  ctx.font = prepareFontString("bold", fontSize, fontFamily);

  // Measure text
  const textMetrics = ctx.measureText(text);
  const textWidth = textMetrics.width;

  // Calculate banner dimensions
  const paddingX = 30;
  const paddingY = 20;
  const bannerWidth = Math.min(textWidth + paddingX * 2, maxWidth);
  const bannerHeight = fontSize + paddingY * 2;

  // Calculate banner position
  const bannerX = x - bannerWidth / 2;
  const bannerY = y - bannerHeight / 2;

  // Draw banner background
  const borderRadius = 25;
  ctx.fillStyle = primaryColor;
  ctx.beginPath();
  ctx.roundRect(bannerX, bannerY, bannerWidth, bannerHeight, borderRadius);
  ctx.fill();

  // Draw text
  ctx.fillStyle = "#FFFFFF";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(text, x, y);
};
