"use client";

import React from "react";
import { PostRendererProps } from "../types/Layout";
import { usePostRenderer } from "../hooks/usePostRenderer";

export const PostRenderer: React.FC<PostRendererProps> = ({
  layout,
  onComplete,
  onError,
  businessProfile,
  selectedTemplate,
  onRendererReady,
}) => {
  const { canvasRef, forceRedraw, isRendering } = usePostRenderer({
    layout,
    onComplete,
    onError,
    businessProfile,
    selectedTemplate,
  });

  const prevIsRenderingRef = React.useRef<boolean | null>(null);
  const hasCalledReadyRef = React.useRef(false);
  const onRendererReadyRef = React.useRef(onRendererReady);

  React.useEffect(() => {
    onRendererReadyRef.current = onRendererReady;
  }, [onRendererReady]);

  React.useEffect(() => {
    const callback = onRendererReadyRef.current;
    if (callback) {
      const prevIsRendering = prevIsRenderingRef.current;

      if (!hasCalledReadyRef.current || prevIsRendering !== isRendering) {
        prevIsRenderingRef.current = isRendering;
        hasCalledReadyRef.current = true;
        callback({ forceRedraw, isRendering });
      }
    }
  }, [forceRedraw, isRendering]);

  return (
    <div className="post-renderer w-full">
      <div
        className="canvas-container border border-gray-200 overflow-hidden"
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <canvas
          ref={canvasRef}
          style={{
            width: "100%",
            maxWidth: "600px",
            height: "auto",
            imageRendering: "auto",
            animation: "none",
            display: "block",
          }}
        />
      </div>
    </div>
  );
};

export default PostRenderer;
