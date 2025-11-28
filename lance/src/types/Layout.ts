import type { TemplateType } from "../services/templateRenderer";
import type { BusinessProfile } from "../constants/mockBusinessProfiles";

export interface Position {
  x: number;
  y: number;
}

export interface SemanticPosition {
  area: "top" | "center" | "bottom";
  alignment: "left" | "center" | "right";
  order: number;
}

export interface Dimensions {
  width: number;
  height: number;
}

export interface BrandInfo {
  primary_color: string;
  secondary_color: string;
  font_family: string;
  company_name: string;
}

export interface LayoutMetadata {
  template:
    | "gradient-hero"
    | "minimal-clean"
    | "photo-overlay"
    | "split-layout"
    | "card-style"
    | "promotional";
  dimensions: Dimensions;
  brand: BrandInfo;
}

export interface BackgroundConfig {
  type: "solid" | "linear-gradient" | "radial-gradient";
  colors: string[];
  direction?: number;
}

export interface TextBlock {
  id: string;
  text: string;
  fontWeight: "normal" | "bold" | "600" | "700" | "800";
  fontFamily?: string;
  color: string;
  alignment: "left" | "center" | "right";
  order: number; // Order for sequential layout (1, 2, 3...)
  maxWidth?: number;
  componentType?: "headerText" | "bodyText" | "specialBannerText"; // New component type for different styling
}

export interface ImageElement {
  id: string;
  src: string;
  width: number;
  height: number;
  position: Position;
  opacity: number;
}

export interface LayoutJSON {
  metadata: LayoutMetadata;
  background: BackgroundConfig;
  textBlocks: TextBlock[];
  images: ImageElement[];
}

export interface PostRendererProps {
  layout: LayoutJSON;
  onComplete?: (imageData: string) => void;
  onError?: (error: string) => void;
  businessProfile: BusinessProfile;
  selectedTemplate?: TemplateType;
  onRendererReady?: (controls: {
    forceRedraw: () => void;
    isRendering: boolean;
  }) => void;
}

export interface FontLoadStatus {
  family: string;
  loaded: boolean;
  error?: string;
}

export interface RenderingStep {
  id: string;
  name: string;
  status: "pending" | "active" | "completed" | "error";
  progress: number;
  description: string;
  error?: string;
  startTime?: number;
  endTime?: number;
}
