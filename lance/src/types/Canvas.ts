export interface Shape {
  id: string;
  type: "rectangle" | "circle" | "cross" | "triangle" | "line" | "text";
  x: number;
  y: number;
  width?: number;
  height?: number;
  radius?: number;
  rotation?: number;
  color: string;
  strokeWidth?: number;
  text?: string;
  fontSize?: number;
  points?: { x: number; y: number }[];
}

export interface ColorPalette {
  primary: string;
  secondary: string;
  accent: string;
  background: string;
  text: string;
}

